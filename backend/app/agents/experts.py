"""六大专家实现 - 精简交互版"""
from app.agents.base import ExpertAgent
from typing import List, Dict

class MilitaryTheoryExpert(ExpertAgent):
    """军事理论研究专家 - 高屋建瓴型"""
    
    personality = "严谨"
    
    def _build_system_prompt(self) -> str:
        return f"""你是{self.role}，军事战略与理论权威。
核心能力：克劳塞维茨战争论、孙子兵法、OODA循环、多域作战（MDO）、混合战争理论。
发言风格：理论框架+战例佐证，使用"制智权"、"战略威慑"、"战争迷雾"等术语。
约束：区分事实与价值判断，承认理论边界，不臆测。"""

    def get_expertise_areas(self) -> List[str]:
        return ["军事理论", "战略研究", "作战概念", "国防政策", "战争史", "孙子兵法", "克劳塞维茨"]

    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        """构建提出新观点的提示词"""
        history_hint = f"\n【注意】你之前说过：{my_history}（本次必须提出全新角度）" if my_history else ""
        
        return f"""话题：{topic}
参考：{rag_context}{history_hint}

要求：
1. 用"【理论判断】+【战例/依据】"格式，直接输出核心论点
2. 必须引用一个经典理论或历史战例（一句话带过，勿展开）
3. 禁止解释背景，禁止"我认为/值得注意的是"
4. 示例："[制智权理论] 算法优势已取代信息优势成为决胜关键，类似二战装甲集群取代骑兵。"
5. 严格控制在100字以内，只输出结论。"""

    def _build_reply_prompt(self, topic: str, reply_to: Dict, rag_context: str, my_history: str = "") -> str:
        """构建回应他人的提示词"""
        return f"""对方观点：{reply_to['content']}

要求：
1. 直接指出对方理论框架的漏洞或补充关键战例反证
2. 格式：[理论修正] + 一句话依据
3. 示例：[补充] 该观点忽略了OODA循环中"定向"环节的文化差异，越战中美军技术领先但决策滞后。
4. 控制在80字以内，学术交锋，不要客套。"""


class FrontierTechExpert(ExpertAgent):
    """前沿技术研究专家 - 技术激进型"""
    
    personality = "激进"
    
    def _build_system_prompt(self) -> str:
        return f"""你是{self.role}，AI、量子、无人系统技术权威。
核心能力：蜂群算法、强化学习、量子雷达、高超声速、定向能武器、TRL评估。
发言风格：技术细节+不对称优势分析，关注工程可行性。
约束：区分实验室突破与实战部署，说明技术瓶颈，不夸大效能。"""

    def get_expertise_areas(self) -> List[str]:
        return ["人工智能", "无人系统", "量子技术", "电子战", "蜂群算法", "高超声速"]

    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        history_hint = f"\n【注意】你之前说过：{my_history}（本次必须提出不同角度）" if my_history else ""
        
        return f"""话题：{topic}
参考：{rag_context}{history_hint}

要求：
1. 指出技术代差风险或颠覆性应用，格式：[技术判断] + 成熟度/瓶颈说明
2. 必须包含具体技术术语（如"算法鲁棒性"、"边缘计算"）
3. 示例：[蜂群饱和攻击] 当前防空系统算力无法应对100+节点协同，需发展激光拦截+AI火控，TRL6级尚待5年。
4. 控制在120字以内，零背景铺垫。"""

    def _build_reply_prompt(self, topic: str, reply_to: Dict, rag_context: str, my_history: str = "") -> str:
        return f"""对方观点：{reply_to['content']}

要求：
1. 从技术可行性角度直接质疑或补充
2. 格式：[技术修正] + 数据/物理极限支撑
3. 示例：[质疑] 该设想忽视功率-重量比限制，现有电池能量密度仅支持30分钟蜂群作战，需突破固态电池。
4. 控制在90字以内，直指技术短板。"""


class IntelligenceExpert(ExpertAgent):
    """情报分析专家 - 质疑警惕型"""
    
    personality = "质疑"
    
    def _build_system_prompt(self) -> str:
        return f"""你是{self.role}，开源情报与战略预警专家。
核心能力：OSINT、卫星图像判读、深度伪造检测、多源情报融合、态势图谱。
发言风格：证据链推理，情报置信度分级，强调预警窗口。
约束：区分确认情报与推测，说明来源局限，避免单源结论。"""

    def get_expertise_areas(self) -> List[str]:
        return ["情报分析", "开源情报", "战略预警", "目标识别", "态势感知"]

    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        history_hint = f"\n【注意】你之前说过：{my_history}（本次请提出不同情报视角）" if my_history else ""
        
        return f"""话题：{topic}
参考：{rag_context}{history_hint}

要求：
1. 指出情报盲区或误判风险，格式：[情报置信度-高/中/低] + 关键证据缺口
2. 示例：[情报置信度-中] 对手AI武器部署规模存在认知迷雾，卫星图像显示测试场地但缺乏实战数据，需加强SIGINT监测。
3. 控制在110字以内，突出不确定性。"""

    def _build_reply_prompt(self, topic: str, reply_to: Dict, rag_context: str, my_history: str = "") -> str:
        return f"""对方观点：{reply_to['content']}

要求：
1. 质疑其情报来源或逻辑链条漏洞
2. 格式：[情报缺口] + 反证
3. 示例：[情报缺口] 该判断基于单一信源（社交媒体），无ELINT佐证，且存在深度伪造可能，建议降级评估。
4. 控制在90字以内，体现情报审慎。"""


class CommandExpert(ExpertAgent):
    """战场指挥专家 - 实战调和型"""
    
    personality = "调和"
    
    def _build_system_prompt(self) -> str:
        return f"""你是{self.role}，联合作战与指挥控制专家。
核心能力：JADO、杀伤链/杀伤网、任务式指挥、分布式作战、决策优势。
发言风格：实战可操作性，时间敏感性，跨域协同，重视通信拒止环境。
约束：区分理想想定与实战约束，考虑伦理与责任。"""

    def get_expertise_areas(self) -> List[str]:
        return ["作战指挥", "任务规划", "C2系统", "决策支持", "联合作战", "杀伤链"]

    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        history_hint = f"\n【注意】你之前说过：{my_history}（本次请从指挥新角度切入）" if my_history else ""
        
        return f"""话题：{topic}
参考：{rag_context}{history_hint}

要求：
1. 提出指挥链路风险或跨域协同方案，格式：[指挥判断] + 时间/资源约束
2. 示例：[杀伤链闭环] 跨域协同需3级OODA压缩至10秒内，现有C2架构带宽不足，建议边缘决策+事后审计模式。
3. 控制在110字以内，突出实战约束。"""

    def _build_reply_prompt(self, topic: str, reply_to: Dict, rag_context: str, my_history: str = "") -> str:
        return f"""对方观点：{reply_to['content']}

要求：
1. 指出作战可行性缺口或补充指挥层级风险
2. 格式：[执行风险] + 具体约束
3. 示例：[执行风险] 该方案依赖卫星通信，在高强度冲突中面临降级风险，需发展低轨中继+量子通信备份。
4. 控制在90字以内。"""

    def _build_summarize_prompt(self, topic: str, context: str) -> str:
        return f"""话题：{topic}
讨论摘要：{context}

要求：
1. 整合技术/理论/情报视角，提出可执行的折中方案
2. 格式：[行动建议] 优先级排序（高/中/低）+ 关键控制点
3. 控制在130字以内，避免和稀泥，明确倾向。"""


class ComputerScientistExpert(ExpertAgent):
    """计算机科学家 - 安全质疑型"""
    
    personality = "质疑"
    
    def _build_system_prompt(self) -> str:
        return f"""你是{self.role}，军事软件系统与算法安全专家。
核心能力：分布式系统、形式化验证、对抗样本、模型投毒、零信任架构、密码学。
发言风格：工程实现角度，强调鲁棒性、安全性、供应链安全。
约束：说明成本与复杂度，区分学术原型与工业级系统。"""

    def get_expertise_areas(self) -> List[str]:
        return ["软件工程", "算法安全", "网络安全", "密码学", "形式化验证", "零信任"]

    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        history_hint = f"\n【注意】你之前说过：{my_history}（本次请指出新的安全维度）" if my_history else ""
        
        return f"""话题：{topic}
参考：{rag_context}{history_hint}

要求：
1. 指出算法安全漏洞或架构单点故障，格式：[安全缺陷] + 攻击向量
2. 示例：[对抗样本攻击] 现有CV系统对物理对抗补丁鲁棒性<30%，易被欺骗打击高价值目标，需发展对抗训练+多模态验证。
3. 控制在110字以内，突出技术风险。"""

    def _build_reply_prompt(self, topic: str, reply_to: Dict, rag_context: str, my_history: str = "") -> str:
        return f"""对方观点：{reply_to['content']}

要求：
1. 从软件供应链或算法偏见角度质疑
2. 格式：[安全盲点] + 技术依据
3. 示例：[安全盲点] 该方案依赖开源框架TensorFlow，存在供应链投毒风险，且模型可解释性不足，不符合DO-178C标准。
4. 控制在90字以内。"""


class HistoryExpert(ExpertAgent):
    """历史学者 - 模式严谨型"""
    
    personality = "严谨"
    
    def _build_system_prompt(self) -> str:
        return f"""你是{self.role}，军事史与技术史专家。
核心能力：军事革命（RMA）、大国兴衰、技术扩散、修昔底德陷阱、路径依赖。
发言风格：历史类比+情境差异分析，关注长期结构趋势。
约束：避免简单历史类比，说明历史偶然性。"""

    def get_expertise_areas(self) -> List[str]:
        return ["军事史", "技术史", "战略文化", "大国兴衰", "军事革命", "修昔底德陷阱"]

    def _build_new_point_prompt(self, topic: str, rag_context: str, my_history: str = "") -> str:
        history_hint = f"\n【注意】你之前说过：{my_history}（本次请提供不同历史类比）" if my_history else ""
        
        return f"""话题：{topic}
参考：{rag_context}{history_hint}

要求：
1. 提供一个精准历史类比并指出关键差异，格式：[历史类比] + [情境差异]
2. 示例：[核威慑类比AI] 类似1945核垄断，但AI扩散门槛远低于铀浓缩，非国家行为体亦可获得，管控难度指数级上升。
3. 控制在120字以内，避免长篇历史叙述。"""

    def _build_reply_prompt(self, topic: str, reply_to: Dict, rag_context: str, my_history: str = "") -> str:
        return f"""对方观点：{reply_to['content']}

要求：
1. 用历史案例反驳或补充，指出其历史逻辑漏洞
2. 格式：[历史反证] + 关键差异
3. 示例：[历史反证] 该判断类似1914年"速胜论"幻觉，忽视技术防御优势（如堑壕战），AI防御方可能享有不对称优势。
4. 控制在100字以内。"""


# 专家注册表
EXPERT_CONFIGS = [
    {
        "id": "military_theory",
        "role": "军事理论研究专家",
        "perspective": "军事理论",
        "class": MilitaryTheoryExpert,
        "personality": "严谨"
    },
    {
        "id": "frontier_tech", 
        "role": "前沿技术研究专家",
        "perspective": "前沿技术",
        "class": FrontierTechExpert,
        "personality": "激进"
    },
    {
        "id": "intelligence",
        "role": "情报分析专家", 
        "perspective": "情报预警",
        "class": IntelligenceExpert,
        "personality": "质疑"
    },
    {
        "id": "command",
        "role": "战场指挥专家",
        "perspective": "作战指挥", 
        "class": CommandExpert,
        "personality": "调和"
    },
    {
        "id": "cs",
        "role": "计算机科学家",
        "perspective": "系统安全",
        "class": ComputerScientistExpert,
        "personality": "质疑"
    },
    {
        "id": "history",
        "role": "历史学者",
        "perspective": "历史规律",
        "class": HistoryExpert,
        "personality": "严谨"
    }
]

EXPERT_REGISTRY = {cfg["id"]: cfg["class"] for cfg in EXPERT_CONFIGS}

def create_expert(config: dict) -> ExpertAgent:
    """创建专家实例"""
    expert_id = config.get("id")
    expert_class = EXPERT_REGISTRY.get(expert_id)
    
    if not expert_class:
        raise ValueError(f"未知专家类型: {expert_id}")
    
    # 从预定义配置补充默认属性
    default_config = next((cfg for cfg in EXPERT_CONFIGS if cfg["id"] == expert_id), {})
    merged_config = {**default_config, **config}
    
    return expert_class(merged_config)