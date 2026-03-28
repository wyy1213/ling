"""主持人协调器 - 管理研讨流程"""
from typing import List, Dict, Optional
from app.agents.experts import create_expert
from app.config import settings
import random

class SymposiumCoordinator:
    """研讨协调器"""
    
    def __init__(self, topic: str, expert_count: int = 6):
        self.topic = topic
        self.expert_count = expert_count
        self.round = 0
        self.experts: List = []
        self.history: List[Dict] = []
        self.last_speaker: Optional[Dict] = None
        
        self._init_experts()
    
    def _init_experts(self):
        """初始化专家团"""
        configs = settings.EXPERTS_CONFIG[:self.expert_count]
        for config in configs:
            expert = create_expert(config)
            self.experts.append(expert)
    
    def get_host_opening(self) -> str:
        """生成主持人开场白"""
        openings = [
            f"各位首长、专家，本次联合兵棋推演正式启动。当前全局研判代号：【{self.topic}】。请各领域专家基于最新情报，接入作战回路并发表专业研判。",
            f"欢迎来到灵境Symposium。今天我们将围绕【{self.topic}】展开深度研讨。请各位专家从各自专业视角切入，提供基于事实的权威分析。",
            f"作战想定已下达：【{self.topic}】。请专家组成员结合实时情报和理论知识，准备第一轮态势研判。"
        ]
        return random.choice(openings)
    
    def generate_speaking_queue(self, current_round: int) -> List[Dict]:
        """
        生成发言队列
        
        策略：
        1. 第一轮：所有专家依次发言（随机顺序）
        2. 后续轮次：基础发言 + 追加交锋
        """
        queue = []
        
        # 基础发言：所有专家
        base_speakers = random.sample(self.experts, len(self.experts))
        for expert in base_speakers:
            queue.append({
                "expert": expert,
                "type": "opening",
                "reply_to": None
            })
        
        # 追加交锋：随机选择2-4次回应
        if current_round > 1 or random.random() > 0.3:
            extra_turns = random.randint(2, 4)
            for _ in range(extra_turns):
                # 随机选择回应者和被回应者
                candidates = [e for e in self.experts if e != self.last_speaker]
                if candidates and self.last_speaker:
                    responder = random.choice(candidates)
                    queue.append({
                        "expert": responder,
                        "type": "reply",
                        "reply_to": {
                            "expert_id": self.last_speaker.expert_id,
                            "expert_role": self.last_speaker.role,
                            "content": self._get_last_content(self.last_speaker.expert_id)
                        }
                    })
        
        return queue
    
    def _get_last_content(self, expert_id: str) -> str:
        """获取某专家最后一次发言内容"""
        for msg in reversed(self.history):
            if msg.get("expert_id") == expert_id:
                return msg.get("content", "")
        return ""
    
    def add_to_history(self, message: Dict):
        """添加消息到历史"""
        self.history.append(message)
        # 更新最后发言者
        for expert in self.experts:
            if expert.expert_id == message.get("expert_id"):
                self.last_speaker = expert
                break
    
    def generate_summary(self) -> Dict:
        """生成会议总结"""
        if not self.history:
            return {}
        
        # 统计各专家发言次数
        perspective_stats = {}
        for msg in self.history:
            pid = msg.get("expert_id")
            if pid:
                perspective_stats[pid] = perspective_stats.get(pid, 0) + 1
        
        return {
            "total_messages": len(self.history),
            "rounds": self.round,
            "perspective_distribution": perspective_stats,
            "topic": self.topic
        }