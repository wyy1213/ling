"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class ExpertType(str, Enum):
    MILITARY = "military"
    TECH = "tech"
    INTEL = "intel"
    CMD = "cmd"
    COMPUTER = "computer"
    HIST = "hist"

class ExpertConfig(BaseModel):
    id: str
    role: str
    perspective: ExpertType
    avatar: str
    color: str
    desc: str

class Message(BaseModel):
    expert_id: str
    expert_role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_reply: bool = False
    reply_to: Optional[str] = None
    sources: List[str] = []  # 引用来源
    thought_chain: List[str] = []  # 思维链

class DiscussionRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    expert_count: int = Field(default=6, ge=3, le=6)
    current_round: int = Field(default=1)
    history: List[Message] = []
    enable_search: bool = True  # 是否启用联网搜索
    enable_rag: bool = True     # 是否启用知识库

class DiscussionResponse(BaseModel):
    session_id: str
    topic: str
    round: int
    messages: List[Message]
    status: Literal["ongoing", "completed", "error"]

class StreamChunk(BaseModel):
    type: Literal["thought", "content", "source", "complete", "error"]
    expert_id: Optional[str] = None
    data: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SummaryRequest(BaseModel):
    topic: str
    messages: List[Message]
    rounds: int

class SummaryResponse(BaseModel):
    consensus: str
    key_insights: List[str]
    perspective_analysis: dict
    recommendations: List[str]