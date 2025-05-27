import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import User, VoiceMetrics, DiagnosisSession
from app.controllers.diagnosis_controller import DiagnosisController
from app.schemas.voice import VoiceHistoryResponse, VoiceStatsResponse

router = APIRouter()

@router.post("/upload")
async def upload_voice_file(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """上传语音文件并创建诊断会话"""
    try:
        logger.info(f"开始处理用户 {current_user.id} 的语音文件上传")
        controller = DiagnosisController(db)
        result = await controller.upload_voice_file(file, current_user.id, background_tasks)
        logger.info(f"用户 {current_user.id} 的语音文件上传成功")
        return result
    except Exception as e:
        logger.error(f"用户 {current_user.id} 的语音文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )

@router.get("/voice-history", response_model=VoiceHistoryResponse)
async def get_voice_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """获取用户的语音分析历史记录"""
    logger.info(f"收到历史记录请求 - 用户ID: {current_user.id}, 页码: {page}, 每页大小: {size}")
    try:
        controller = DiagnosisController(db)
        return await controller.get_voice_history(current_user.id, page, size)
    except Exception as e:
        logger.error(f"获取语音历史记录失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取语音历史记录失败: {str(e)}"
        )

@router.get("/stats", response_model=VoiceStatsResponse)
async def get_voice_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的语音分析统计数据"""
    logger.info(f"收到统计数据请求 - 用户ID: {current_user.id}")
    try:
        controller = DiagnosisController(db)
        return await controller.get_voice_stats(current_user.id)
    except Exception as e:
        logger.error(f"获取语音统计数据失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取语音统计数据失败: {str(e)}"
        )

@router.get("/visualization/{metrics_id}")
async def get_visualization_data(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    metrics_id: int
):
    """获取可视化数据"""
    try:
        controller = DiagnosisController(db)
        return await controller.get_visualization_data(metrics_id, current_user.id)
    except Exception as e:
        logger.error(f"获取可视化数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取可视化数据失败: {str(e)}"
        )

@router.post("/llm/{session_id}")
async def analyze_with_llm(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: int
):
    """使用LLM对诊断会话进行分析"""
    try:
        controller = DiagnosisController(db)
        return await controller.analyze_with_llm(session_id, current_user.id)
    except Exception as e:
        logger.error(f"LLM分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM分析失败: {str(e)}"
        )
    
@router.get("/{session_id}")
async def get_diagnosis_result(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: int
):
    """获取诊断结果"""
    try:
        controller = DiagnosisController(db)
        return await controller.get_diagnosis_result(session_id, current_user.id)
    except Exception as e:
        logger.error(f"获取诊断结果失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取诊断结果失败: {str(e)}"
        )

@router.post("/analyze")
async def analyze_diagnosis(session_id: int, user_id: int, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.analyze_session(session_id, user_id)

@router.post("/follow-up")
async def follow_up(session_id: int, user_id: int, question: str, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.handle_follow_up(session_id, user_id, question)

@router.get("/history")
async def get_history(session_id: int, user_id: int, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.get_conversation_history(session_id, user_id)

@router.get("/latest-suggestion")
async def get_latest_suggestion(session_id: int, user_id: int, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.get_latest_suggestion(session_id, user_id)

@router.get("/analysis-history")
async def get_analysis_history(user_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.get_analysis_history(user_id, skip, limit)

@router.get("/display-summary")
async def get_display_summary(user_id: int, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.get_display_summary(user_id)

@router.get("/realtime-data")
async def get_realtime_data(user_id: int, db: Session = Depends(get_db)):
    controller = DiagnosisController(db)
    return await controller.get_realtime_data(user_id) 

@router.get("/latest")
async def get_latest_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户最新一次分析的KPI和LLM分析结果"""
    # 查询最新的DiagnosisSession
    session = db.query(DiagnosisSession).filter(
        DiagnosisSession.user_id == current_user.id
    ).order_by(DiagnosisSession.created_at.desc()).first()
    if not session:
        raise HTTPException(status_code=404, detail="未找到最新诊断会话")
    # 查询语音指标
    metrics = db.query(VoiceMetrics).filter(VoiceMetrics.session_id == session.id).first()
    return {
        "session_id": session.id,
        "created_at": session.created_at,
        "llm_suggestion": session.llm_suggestion,
        "conversation_history": session.conversation_history,
        "voice_metrics": {
            "prediction": metrics.model_prediction if metrics else None,
            "confidence": metrics.model_confidence if metrics else None,
            "mfcc": [getattr(metrics, f"mfcc_{i}") for i in range(1, 14)] if metrics else [],
            "chroma": [getattr(metrics, f"chroma_{i}") for i in range(1, 13)] if metrics else [],
            "rms": metrics.rms if metrics else None,
            "zcr": metrics.zcr if metrics else None,
            "mel_spectrogram": metrics.mel_spectrogram if metrics else None
        }
    } 