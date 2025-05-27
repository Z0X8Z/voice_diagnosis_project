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
from app.services.llm_service import LLMService
from app.controllers.llm_controller import LLMController
from app.core.llm import LLMClient

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

class FollowupQuestion(BaseModel):
    question: str

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[int] = None

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
    """与LLM进行对话"""
    try:
        llm_client = LLMClient()
        
        # 构建提示词
        prompt = f"""
用户ID: {current_user.id}
用户问题: {message.message}

请根据用户的问题提供关于语音健康分析的回答。
如果问题与语音健康无关，请礼貌地引导用户询问与语音健康相关的问题。
"""
        
        # 调用LLM
        analysis = await llm_client.analyze(prompt)
        
        # 如果提供了session_id，将对话保存到会话历史记录中
        if message.session_id:
            controller = LLMController(db)
            await controller.save_conversation(
                message.session_id, 
                current_user.id, 
                {"role": "user", "content": message.message},
                {"role": "assistant", "content": analysis}
            )
        
        return {
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
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
        result = await controller.llm_service.analyze_with_llm(session_id, current_user.id)
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
    current_user: User = Depends(get_current_user)
):
    """
    总结对话内容，生成最终诊断建议，用于用户点击"完成"按钮后调用
    """
    logger.info(f"[API.summarize] 总结对话请求: session_id={session_id}, user_id={current_user.id}")
    controller = LLMController(db)
    try:
        result = await controller.summarize_conversation(session_id, current_user.id)
        logger.info(f"[API.summarize] 总结对话成功: session_id={session_id}")
        return result
    except Exception as e:
        logger.error(f"[API.summarize] 总结对话失败: session_id={session_id}, error={str(e)}")
        raise