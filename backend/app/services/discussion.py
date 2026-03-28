"""研讨服务 - 动态交互版"""
from typing import AsyncGenerator, Dict, List, Optional
from app.agents.coordinator import SymposiumCoordinator
from app.models import Message, StreamChunk
from app.tools.rag import init_knowledge_base
import uuid
import json
from datetime import datetime
import random
import asyncio

class DiscussionService:
    """研讨服务 - 支持自然对话流"""
    
    def __init__(self):
        self.sessions: Dict[str, SymposiumCoordinator] = {}
        self.knowledge_base = None
    
    def ensure_knowledge_base(self):
        if self.knowledge_base is None:
            try:
                self.knowledge_base = init_knowledge_base()
            except:
                self.knowledge_base = None
        return self.knowledge_base
    
    def create_session(self, topic: str, expert_count: int) -> str:
        session_id = str(uuid.uuid4())[:8]
        coordinator = SymposiumCoordinator(topic, expert_count)
        self.sessions[session_id] = coordinator
        
        print(f"✅ 创建会话 {session_id}，话题：{topic}")
        print(f"   专家数量：{len(coordinator.experts)}")
        for e in coordinator.experts:
            print(f"   - {e.role} ({e.personality})")
        
        return session_id

    def get_session(self, session_id: str) -> Optional[SymposiumCoordinator]:
        return self.sessions.get(session_id)
    
    async def stream_discussion(
        self,
        session_id: str,
        current_round: int,
        enable_search: bool = True,
        enable_rag: bool = True
    ) -> AsyncGenerator[str, None]:
        """流式研讨 - 自然对话版"""
        coordinator = self.get_session(session_id)
        if not coordinator:
            yield f"data: {json.dumps({'type': 'error', 'data': '会话不存在'})}\n\n"
            return
        
        coordinator.round = current_round
        
        # 1. 主持人开场（仅第一轮）
        if current_round == 1:
            opening = coordinator.get_host_opening()
            yield f"data: {json.dumps({'type': 'host', 'data': opening})}\n\n"
            await asyncio.sleep(0.5)
        
        # 2. 智能选择发言者
        speaking_queue = await self._build_speaking_queue(coordinator, current_round)
        
        if not speaking_queue:
            yield f"data: {json.dumps({'type': 'round_complete', 'round': current_round})}\n\n"
            return
        
        # 3. 执行发言（关键：维护round_cache实现实时对话）
        round_cache = {}  # expert_id -> content
        
        for idx, item in enumerate(speaking_queue):
            expert = item["expert"]
            mode = item["mode"]
            reply_to = item.get("reply_to")
            
            # 【关键修复】如果是回应模式，获取前一个人的真实完整内容
            if mode == "reply" and reply_to:
                prev_id = reply_to["expert_id"]
                if prev_id in round_cache:
                    real_content = round_cache[prev_id]
                    reply_to = {
                        "expert_role": reply_to["expert_role"],
                        "content": real_content,  # 使用真实内容，不是占位符！
                        "expert_id": prev_id
                    }
                    print(f"   {expert.role} 回应 {reply_to['expert_role']}: {real_content[:40]}...")
            
            # 发送开始信号
            start_data = {
                'type': 'start',
                'expert_id': expert.expert_id, 
                'expert_role': expert.role,
                'mode': mode,
                'reply_to': reply_to['expert_role'] if reply_to else None
            }
            yield f"data: {json.dumps(start_data)}\n\n"
            
            # 构建上下文
            context = self._build_context_for_expert(coordinator, expert, mode, reply_to, round_cache)
            
            # 收集内容
            full_content = ""
            
            async for chunk in expert.speak(
                topic=coordinator.topic,
                context=context,
                reply_to=reply_to,
                enable_search=enable_search and mode == "new",
                enable_rag=enable_rag,
                mode=mode
            ):
                enriched_chunk = {
                    **chunk, 
                    'expert_id': expert.expert_id,
                    'expert_role': expert.role,
                    'reply_to': reply_to['expert_role'] if reply_to else None
                }
                yield f"data: {json.dumps(enriched_chunk)}\n\n"
                
                if chunk["type"] == "content":
                    full_content += chunk["data"]
            
            # 【关键】保存到缓存供下一个人使用
            if full_content:
                round_cache[expert.expert_id] = {
                    "expert_id": expert.expert_id,
                    "expert_role": expert.role,
                    "content": full_content[:200]
                }
                
                # 保存到历史
                message = {
                    "expert_id": expert.expert_id,
                    "expert_role": expert.role,
                    "content": full_content[:150],
                    "timestamp": datetime.now().isoformat(),
                    "mode": mode,
                    "reply_to": reply_to["expert_role"] if reply_to else None,
                    "round": current_round
                }
                coordinator.add_to_history(message)
                
                if idx < len(speaking_queue) - 1:
                    await asyncio.sleep(0.5)  # 对话间隔，营造思考感
        
        # 轮次结束
        complete_data = {
            'type': 'round_complete', 
            'round': current_round,
            'speaking_count': len(round_cache),
            'total_experts': len(coordinator.experts)
        }
        yield f"data: {json.dumps(complete_data)}\n\n"
    
    async def _build_speaking_queue(self, coordinator, current_round: int) -> List[Dict]:
        """构建发言队列 - 促进交锋"""
        experts = coordinator.experts
        history = coordinator.history
        
        print(f"🎲 构建第{current_round}轮队列，历史：{len(history)}条")
        
        # 第1轮：全员立论（随机顺序）
        if current_round == 1:
            shuffled = experts.copy()
            random.shuffle(shuffled)
            queue = [{"expert": e, "mode": "new", "reply_to": None} for e in shuffled]
            print(f"   第1轮全员立论：{[e.role for e in shuffled]}")
            return queue
        
        # 第2轮+：寻找观点差异大的专家交锋
        queue = []
        last_round = [h for h in history if h.get("round") == current_round - 1]
        
        if len(last_round) >= 2:
            # 策略：激进派 vs 严谨派（视角差异最大）
            aggressor = next((e for e in experts if e.personality in ["激进", "质疑"]), None)
            defender = next((e for e in experts if e.personality in ["严谨", "调和"] and e != aggressor), None)
            
            if aggressor and defender:
                # 激进派回应上一轮最后一个观点
                target = last_round[-1]
                queue.append({
                    "expert": aggressor,
                    "mode": "reply",
                    "reply_to": {
                        "expert_role": target["expert_role"],
                        "content": target["content"],
                        "expert_id": target["expert_id"]
                    }
                })
                
                # 严谨派回应激进派（形成对话链）
                queue.append({
                    "expert": defender,
                    "mode": "reply",
                    "reply_to": {
                        "expert_role": aggressor.role,
                        "content": "[待获取]",  # 将在stream_discussion中被替换为真实内容
                        "expert_id": aggressor.expert_id
                    }
                })
                
                # 第三人（如果有）提出新角度
                others = [e for e in experts if e not in [aggressor, defender]]
                if others:
                    queue.append({
                        "expert": random.choice(others),
                        "mode": "new",
                        "reply_to": None
                    })
                
                print(f"   第{current_round}轮交锋：{aggressor.role} vs {defender.role}")
                return queue
        
        # 默认：选2人，1人回应，1人新观点
        if len(last_round) >= 1:
            target = last_round[-1]
            responder = random.choice([e for e in experts if e.expert_id != target["expert_id"]])
            queue.append({
                "expert": responder,
                "mode": "reply",
                "reply_to": {
                    "expert_role": target["expert_role"],
                    "content": target["content"],
                    "expert_id": target["expert_id"]
                }
            })
            
            new_speaker = random.choice([e for e in experts if e != responder])
            queue.append({
                "expert": new_speaker,
                "mode": "new",
                "reply_to": None
            })
            return queue
        
        # 保底：随机2人
        selected = random.sample(experts, min(2, len(experts)))
        return [{"expert": e, "mode": "new", "reply_to": None} for e in selected]

    def _build_context_for_expert(self, coordinator, expert, mode, reply_to, round_cache):
        """构建上下文"""
        parts = []
        
        if mode == "reply" and reply_to:
            parts.append(f"【直接回应】{reply_to['expert_role']}：{reply_to['content']}")
        
        # 添加其他人的观点（现场感）
        if round_cache:
            others = "\n".join([f"{data['expert_role']}：{data['content'][:60]}..." 
                              for eid, data in round_cache.items() 
                              if eid != expert.expert_id][-2:])
            if others:
                parts.append(f"【现场其他观点】\n{others}")
        
        return "\n".join(parts) if parts else ""

    def get_history(self, session_id: str) -> List[Dict]:
        coordinator = self.get_session(session_id)
        if not coordinator:
            return []
        return coordinator.history
    
    async def generate_summary(self, session_id: str) -> Dict:
        coordinator = self.get_session(session_id)
        if not coordinator:
            return {}
        
        stats = {
            "total_rounds": coordinator.round,
            "total_messages": len(coordinator.history),
            "expert_participation": len(set(m["expert_id"] for m in coordinator.history)),
            "key_perspectives": list(set(m["expert_role"] for m in coordinator.history))
        }
        
        return {
            "summary": f"关于'{coordinator.topic}'的跨领域研讨已完成{stats['total_rounds']}轮对话。",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

discussion_service = DiscussionService()