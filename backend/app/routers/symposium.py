"""API 路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
import asyncio

from app.models import (
    DiscussionRequest, 
    DiscussionResponse, 
    Message,
    SummaryRequest,
    SummaryResponse,
    ExpertConfig
)
from app.services.discussion import discussion_service
from app.config import settings

router = APIRouter(prefix="/symposium", tags=["symposium"])

@router.get("/experts", response_model=List[ExpertConfig])
async def get_experts():
    """获取专家配置列表"""
    return settings.EXPERTS_CONFIG

@router.post("/start", response_model=DiscussionResponse)
async def start_discussion(request: DiscussionRequest):
    """
    开始研讨（非流式，返回会话ID）
    """
    session_id = discussion_service.create_session(
        topic=request.topic,
        expert_count=request.expert_count
    )
    
    return DiscussionResponse(
        session_id=session_id,
        topic=request.topic,
        round=0,
        messages=[],
        status="ongoing"
    )

@router.post("/stream")
async def stream_discussion(request: DiscussionRequest):
    """
    流式研讨（SSE）
    
    前端通过 EventSource 接收实时数据：
    - type: host - 主持人开场
    - type: start - 专家开始发言
    - type: thought - 思维链
    - type: source - 知识来源（RAG/搜索）
    - type: content - 发言内容（流式）
    - type: done - 专家发言完成
    - type: round_complete - 轮次完成
    """
    # 创建或复用会话
    session_id = getattr(request, 'session_id', None)
    if not session_id:
        session_id = discussion_service.create_session(
            topic=request.topic,
            expert_count=request.expert_count
        )
    
    async def event_generator():
        async for chunk in discussion_service.stream_discussion(
            session_id=session_id,
            current_round=request.current_round,
            enable_search=request.enable_search,
            enable_rag=request.enable_rag
        ):
            yield chunk
            await asyncio.sleep(0.01)  # 防止阻塞
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id
        }
    )

@router.get("/history/{session_id}", response_model=List[Message])
async def get_history(session_id: str):
    """获取研讨历史"""
    history = discussion_service.get_history(session_id)
    return [Message(**msg) for msg in history]

@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """生成智能总结"""
    # 这里可以接入 LLM 生成更智能的总结
    # 简化版返回模板
    return SummaryResponse(
        consensus=f"专家团就\"{request.topic}\"达成战略共识...",
        key_insights=["技术代差成为决定性变量", "需防范灰带冲突升级"],
        perspective_analysis={},
        recommendations=["建立技术预警机制", "加强人才培养"]
    )

@router.post("/next-round")
async def next_round(session_id: str, current_round: int):
    """准备下一轮"""
    coordinator = discussion_service.get_session(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "session_id": session_id,
        "next_round": current_round + 1,
        "status": "ready"
    }

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清理会话"""
    if session_id in discussion_service.sessions:
        del discussion_service.sessions[session_id]
    return {"status": "cleared"}