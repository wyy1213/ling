"""专家 Agent 基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncGenerator
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.tools.search import WebSearchTool, SearchAggregator
from app.tools.rag import get_knowledge_base
import json
import random

class ExpertAgent(ABC):
    """领域专家 Agent 基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.expert_id = config["id"]
        self.role = config["role"]
        self.perspective = config["perspective"]
        object.__setattr__(self, 'personality', config.get("personality", "严谨"))
        
        # 初始化 DeepSeek LLM - 降低温度让输出更确定，严格限制token
        self.llm = ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.3,  # 降低温度，减少废话
            max_tokens=300,   # 硬性限制输出长度
            streaming=True
        )
        
        # 初始化工具
        self.search_tool = WebSearchTool()
        self.search_aggregator = SearchAggregator()
        self.kb = get_knowledge_base()
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """构建专家角色的系统提示词"""
        pass
    
    @abstractmethod
    def get_expertise_areas(self) -> List[str]:
        """返回专家擅长领域"""
        pass
    
    def estimate_speaking_willingness(self, topic: str, last_message: Optional[Dict]) -> float:
        """
        评估发言意愿 (0-1)
        基于话题相关性和性格决定本轮是否发言
        """
        base_willingness = 0.7
        
        # 如果有上一轮，根据性格调整回应概率
        if last_message:
            if self.personality == "质疑":
                # 喜欢挑刺，高概率回应
                base_willingness = 0.8
            elif self.personality == "调和":
                # 喜欢总结，看到分歧才说话
                base_willingness = 0.5
            elif self.personality == "激进":
                # 抢着说话
                base_willingness = 0.9
        
        # 话题相关性加成（简单匹配）
        expertise = self.get_expertise_areas()
        if any(area in topic for area in expertise):
            base_willingness += 0.2
        
        return min(base_willingness, 1.0)
    


    def _build_reply_prompt(self, topic: str, reply_to: Dict, my_history: str = "") -> str:
        """构建回应提示词 - 强制针对性回应"""
        target_content = reply_to['content'][:150]
        
        return f"""话题：{topic}

对方（{reply_to['expert_role']}）刚说：
"{target_content}"

{f"【注意】你之前说过：{my_history}（请勿重复）" if my_history else ""}

回应要求：
1. 直接针对对方观点中的具体漏洞、盲点或值得深化的地方进行回应
2. 必须使用"你刚才提到..."、"但是..."等对话式开头，体现你在听对方说话
3. 提出补充、质疑或不同视角，禁止简单重复对方观点
4. 控制在100字以内，像真实辩论一样针锋相对但保持专业
5. 禁止自说自话，必须体现是对对方观点的回应

错误示例（重复自己）："我认为算法战的核心是..."
正确示例（针对对方）："你刚才提到OODA循环压缩，但忽略了通信拒止环境下算法无法获取实时数据的问题..."
"""


    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        """构建新观点提示词 - 强制创新"""
        return f"""话题：{topic}

{f"【知识参考】{rag_context[:100]}" if rag_context else ""}
{f"【注意】你之前已说过：{my_history}（本次必须提出完全不同的新角度）" if my_history else ""}

要求：
1. 提出一个你之前没有提到过的全新视角（从技术风险、伦理困境、历史反例等切入）
2. 禁止重复你之前的观点，必须展现新的思考维度
3. 控制在100字以内，开门见山
4. 如果是第二轮及以后，必须体现对其他专家观点的听过之后的反思，不是独立发言

错误示例："我认为算法战的核心是OODA循环..."（如果之前说过类似内容）
正确示例："听了各位关于技术优势的讨论，我想提醒被忽视的一点：算法偏见可能导致误伤平民，这在法律战上如何辩护？"
"""
    def _build_prompt_by_mode(self, topic: str, context: str, reply_to: Optional[Dict], mode: str) -> str:
        """根据模式选择对应的提示词构建方法"""
        if reply_to:
            return self._build_genuine_reply_prompt(topic, reply_to, context)
        else:
            return self._build_new_point_prompt(topic, context)
    # base.py 中新增话题分析方法
    async def analyze_topic_nature(self, topic: str) -> Dict:
        """让LLM自主判断话题性质，返回角色切换建议"""
        analysis_prompt = f"""作为{self.role}，请快速分析以下话题的性质：

    话题："{topic}"

    请判断：
    1. 这是宏观战略/地缘政治话题，还是具体技术/战术话题？
    2. 你应该从什么角度切入？（战略理论/技术实现/情报评估/历史类比）
    3. 如果是宏观话题，你作为{self.role}应该关注哪个层面？（不要硬套你的技术专长）

    用JSON格式返回：{{"nature": "strategic|technical", "angle": "你的切入角度", "avoid": "应该避免说的内容"}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ])
            # 简单解析
            content = response.content.lower()
            if "strategic" in content or "宏观" in content or "战略" in content:
                return {"nature": "strategic", "avoid_hard_tech": True}
            return {"nature": "technical", "avoid_hard_tech": False}
        except:
            return {"nature": "strategic", "avoid_hard_tech": True}  # 默认战略

    # 修改 speak 方法，先分析再生成
    async def speak(self, topic: str, context: str = "", reply_to: Optional[Dict] = None,
                enable_search: bool = True, enable_rag: bool = True, mode: str = "auto") -> AsyncGenerator[Dict, None]:
        
        # 1. 生成思维链
        thoughts = await self.think(topic, context)
        yield {"type": "thought", "data": json.dumps(thoughts)}
        
        # 2. 【关键】让LLM自主判断话题性质，而不是关键词匹配
        topic_analysis = await self.analyze_topic_nature(topic)
        
        # 3. 根据判断结果选择提示词策略
        if topic_analysis["avoid_hard_tech"] and self._is_tech_expert():
            # 技术专家遇到宏观话题，强制切换视角
            prompt = self._build_strategic_perspective_prompt(topic, context, reply_to)
        else:
            # 正常发挥专长
            prompt = self._build_prompt_by_mode(topic, context, reply_to, mode)
        
        # 4. 流式生成（带实时截断）
        full_content = ""
        try:
            async for chunk in self.llm.astream([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]):
                if chunk.content:
                    full_content += chunk.content
                    if len(full_content) >= 120:
                        # 智能截断：尝试在句号处截断
                        truncated = full_content[:120]
                        if '。' in truncated[-20:]:
                            truncated = truncated[:truncated.rfind('。')+1]
                        elif '.' in truncated[-20:]:
                            truncated = truncated[:truncated.rfind('.')+1]
                        yield {"type": "content", "data": truncated}
                        break
                    yield {"type": "content", "data": chunk.content}
        except Exception as e:
            print(f"生成错误: {e}")
            yield {"type": "content", "data": f"[{self.role}思考中...]"}
        
        yield {"type": "done", "expert_id": self.expert_id, "final_length": len(full_content)}

    def _is_tech_expert(self) -> bool:
        """判断是否是技术类专家"""
        return any(kw in self.role for kw in ["技术", "计算机", "软件", "算法", "AI"])

    def _build_strategic_perspective_prompt(self, topic: str, context: str, reply_to: Optional[Dict]) -> str:
        """技术专家谈宏观话题时的视角切换提示词"""
        
        base = f"""话题：{topic}

    【角色自我修正】你虽然是{self.role}，但敏锐地意识到这是一个需要从**{self.perspective}的宏观影响**角度谈的话题，而非罗列技术细节。

    【发言策略】
    - 不谈"量子"、"算法"、"代码"等具体技术
    - 谈"技术如何改变权力格局/战争形态/决策模式"
    - 用"技术-战略"的桥梁视角：技术能力→战略选项→地缘政治影响

    {f"【你在回应】{reply_to['expert_role']}：{reply_to['content'][:80]}..." if reply_to else ""}

    【强制要求】
    1. {"开头必须引用对方观点：'你刚才提到...，但是/补充...'" if reply_to else "直接给出战略判断"}
    2. 控制在100字以内
    3. 像战略家一样思考，像技术专家一样严谨（但只说战略层面的技术影响）"""

        return base
    
    def _build_strategic_prompt(self, topic: str, context: str, reply_to: Optional[Dict]) -> str:
        """构建宏观战略话题Prompt - 禁止硬套知识库"""
        
        base = f"""话题：{topic}

{f"参考信息：{context}" if context else ""}

【强制要求】
1. 这是宏观战略话题，请从{self.role}的专业视角分析大势、趋势、风险
2. 绝对禁止：强行提及"量子雷达"、"蜂群算法"、"供应链投毒"等具体技术细节（除非话题本身涉及）
3. 必须体现：战略高度、历史视野、系统思维
4. 如果是回应他人，必须直接引用对方观点中的逻辑进行交锋，禁止自说自话
5. 控制在100字以内，像战略研讨会发言，不要像技术汇报"""

        if reply_to:
            base += f"""

对方观点："{reply_to['content'][:100]}..."

你的回应策略：
- 先简要概括对方核心论点（显示你在听）
- 指出其战略盲点或补充更高维度的视角
- 禁止简单重复对方内容，必须有新信息增量"""

        return base

    def _build_summarize_prompt(self, topic: str, context: str) -> str:
        """构建总结调和的提示词"""
        return f"""话题：{topic}
当前讨论摘要：{context}

要求：
1. 总结2-3方观点的共识与分歧
2. 提出调和方案或优先级建议
3. 控制在150字以内"""

    async def think(self, topic: str, context: str = "") -> List[str]:
        """
        生成真实思维链（调用LLM）
        """
        try:
            thought_prompt = f"""作为{self.role}，针对"{topic}"快速形成3个分析步骤。
要求：
1. 用第一人称"我"开头
2. 每步10-15字，体现专业视角
3. 像内心独白一样自然
4. 禁止编号，用逗号分隔或换行

示例：
我在分析技术可行性边界
考虑战场通信拒止场景
评估工程化时间窗口

请直接输出3步思考："""

            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=thought_prompt)
            ])
            
            # 解析响应
            thoughts = [t.strip() for t in response.content.strip().split('\n') if t.strip()]
            return thoughts[:3]  # 最多3步
            
        except Exception as e:
            print(f"思维链生成失败: {e}")
            # 备用：返回基于角色的默认思考
            return [
                f"从{self.perspective}角度切入",
                "分析关键约束条件", 
                "形成初步判断"
            ]

