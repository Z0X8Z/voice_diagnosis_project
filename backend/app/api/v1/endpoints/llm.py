from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
from pydantic import BaseModel
import logging

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import User, DiagnosisSession, VoiceMetrics
from app.controllers.llm_controller import LLMController

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 在路由模块初始化时记录
logger.info("[llm.py] 初始化LLM路由模块")

class FollowupQuestion(BaseModel):
    question: str

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[int] = None
    history: List[Dict[str, str]] = []

class ConversationSummaryRequest(BaseModel):
    conversation: List[Dict[str, str]]

class FollowUpRequest(BaseModel):
    question: str

class SummaryResponse(BaseModel):
    session_id: int
    summary: str
    status: str

# 聊天接口
@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_llm(
    *,
    db: Session = Depends(get_db),
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """与LLM进行对话（带历史）"""
    logger.info(f"[API.chat] 接收聊天请求: user_id={current_user.id}")
    controller = LLMController(db)
    try:
        result = await controller.chat_with_llm(current_user.id, message.message, message.session_id, message.history)
        logger.info(f"[API.chat] 聊天请求处理成功: user_id={current_user.id}")
        return result
    except Exception as e:
        logger.error(f"[API.chat] 聊天请求处理失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"与AI助手对话失败: {str(e)}"
        )

# 获取显示摘要
@router.get("/summary", response_model=Dict[str, Any])
async def get_display_summary(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用于显示的摘要数据"""
    logger.info(f"[API.summary] 获取摘要数据: user_id={current_user.id}")
    controller = LLMController(db)
    return await controller.get_display_summary(current_user.id)

# 获取实时数据
@router.get("/realtime", response_model=Dict[str, Any])
async def get_realtime_data(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实时监控数据"""
    logger.info(f"[API.realtime] 获取实时数据: user_id={current_user.id}")
    controller = LLMController(db)
    return await controller.get_realtime_data(current_user.id)

# LLM分析
@router.post("/analyze/{session_id}", response_model=Dict[str, Any])
async def analyze_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分析诊断会话，使用LLM结合语音指标和历史诊断建议生成分析结果
    """
    logger.info(f"[API.analyze] 开始分析会话: session_id={session_id}, user_id={current_user.id}")
    controller = LLMController(db)
    try:
        result = await controller.analyze_session(session_id, current_user.id)
        logger.info(f"[API.analyze] 分析会话成功: session_id={session_id}")
        return result
    except Exception as e:
        logger.error(f"[API.analyze] 分析会话失败: session_id={session_id}, error={str(e)}")
        raise

# LLM后续问题
@router.post("/follow-up/{session_id}", response_model=Dict[str, Any])
async def handle_follow_up(
    session_id: int,
    request: FollowUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    处理后续问题，支持用户与LLM持续对话
    """
    logger.info(f"[API.follow-up] 接收到后续问题请求: session_id={session_id}, user_id={current_user.id}")
    controller = LLMController(db)
    try:
        result = await controller.handle_follow_up(session_id, current_user.id, request.question)
        logger.info(f"[API.follow-up] 问题处理成功: session_id={session_id}")
        return result
    except Exception as e:
        logger.error(f"[API.follow-up] 处理问题失败: session_id={session_id}, error={str(e)}")
        raise

# 获取对话历史
@router.get("/conversation/{session_id}", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取对话历史
    """
    logger.info(f"[API.conversation] 获取对话历史请求: session_id={session_id}, user_id={current_user.id}")
    controller = LLMController(db)
    try:
        history = await controller.get_conversation_history(session_id, current_user.id)
        logger.info(f"[API.conversation] 获取对话历史成功: session_id={session_id}, 消息数量={len(history)}")
        return history
    except Exception as e:
        logger.error(f"[API.conversation] 获取对话历史失败: session_id={session_id}, error={str(e)}")
        raise

# 获取最新建议
@router.get("/suggestion/{session_id}", response_model=Dict[str, Any])
async def get_latest_suggestion(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取最新的 LLM 建议
    """
    logger.info(f"[API.suggestion] 获取最新建议: session_id={session_id}, user_id={current_user.id}")
    controller = LLMController(db)
    return await controller.get_latest_suggestion(session_id, current_user.id)

# 获取分析历史
@router.get("/history", response_model=List[Dict[str, Any]])
async def get_analysis_history(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取分析历史"""
    logger.info(f"[API.history] 获取分析历史: user_id={current_user.id}, skip={skip}, limit={limit}")
    controller = LLMController(db)
    return await controller.get_analysis_history(current_user.id, skip, limit)

@router.post("/summary/{session_id}", response_model=Dict[str, Any])
async def summarize_with_llm(
    *,
    db: Session = Depends(get_db),
    session_id: int,
    request: ConversationSummaryRequest,
    current_user: User = Depends(get_current_user)
):
    """用LLM总结对话，写入诊断建议"""
    controller = LLMController(db)
    return await controller.summarize_with_llm(session_id, current_user.id, request.conversation)

@router.post("/summarize/{session_id}", response_model=SummaryResponse)
async def summarize_conversation(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    conversation: Optional[List[Dict]] = Body(default=None)
):
    """
    总结对话内容，生成最终诊断建议，用于用户点击"完成"按钮后调用
    """
    logger.info(f"[API.summarize] 总结对话请求: session_id={session_id}, user_id={current_user.id}, 是否提供conversation: {conversation is not None}")
    logger.info(f"[API.summarize] 收到的conversation类型: {type(conversation)}")
    
    controller = LLMController(db)
    try:
        result = await controller.summarize_conversation(session_id, current_user.id, conversation)
        logger.info(f"[API.summarize] 总结对话成功: session_id={session_id}")
        return result
    except Exception as e:
        logger.error(f"[API.summarize] 总结对话失败: session_id={session_id}, error={str(e)}", exc_info=True)
        raise