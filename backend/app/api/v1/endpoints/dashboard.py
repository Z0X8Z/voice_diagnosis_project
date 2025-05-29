from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, date
import json
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import User, DiagnosisSession, VoiceMetrics
from app.controllers.dashboard_controller import DashboardController
from app.schemas.voice import VoiceHistoryResponse, VoiceStatsResponse

router = APIRouter()

# 获取频谱分析
@router.get("/spectrum", response_model=Dict[str, Any])
async def get_spectrum_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    获取频谱分析数据，可选择日期范围
    """
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_spectrum_analysis(db, current_user.id, start_date, end_date)

# 聚类分析
@router.get("/clustering", response_model=Dict[str, Any])
async def get_clustering_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    获取聚类分析数据
    """
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_clustering_analysis(db, current_user.id, start_date, end_date)

# 趋势分析
@router.get("/trends", response_model=Dict[str, Any])
async def get_trends_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    metric: str = Query("f0", description="要分析的指标名称"),
    days: int = Query(30, description="分析的天数")
):
    """
    获取指定指标的趋势分析
    """
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_trend_analysis(db, current_user.id, days)

# 获取最近会话
@router.get("/recent-sessions", response_model=Dict[str, Any])
async def get_recent_sessions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(5, description="要返回的会话数量")
):
    """
    获取用户最近的诊断会话
    """
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_user_statistics(db, current_user.id)

def get_distribution_data(values, num_bins, label):
    """
    计算数值分布数据
    """
    if not values:
        return []
    
    import numpy as np
    hist, bin_edges = np.histogram(values, bins=num_bins)
    
    return [
        {
            "range": f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}",
            "count": int(hist[i]),
            "label": label
        }
        for i in range(len(hist))
    ] 

# 获取用户统计
@router.get("/statistics", response_model=Dict[str, Any])
async def get_user_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户统计数据"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_user_statistics(db, current_user.id)

# 获取会话历史
@router.get("/history", response_model=List[Dict[str, Any]])
async def get_session_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """获取诊断历史记录"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_session_history(db, current_user.id, skip, limit)

# 获取趋势分析
@router.get("/trend", response_model=Dict[str, Any])
async def get_trend_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365)
):
    """获取趋势分析数据"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_trend_analysis(db, current_user.id, days)

@router.get("/latest", response_model=dict)
async def get_latest_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取最新的语音分析结果"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_latest_analysis(db, current_user.id)

@router.get("/historical", response_model=dict)
async def get_historical_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取历史语音指标数据"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_historical_metrics(db, current_user.id, days)

@router.get("/history", response_model=VoiceHistoryResponse)
async def get_voice_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取语音分析历史记录"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_voice_history(db, current_user.id, skip, limit)

@router.get("/stats", response_model=VoiceStatsResponse)
async def get_voice_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取语音分析统计数据"""
    dashboard_controller = DashboardController(db)
    return await dashboard_controller.get_voice_stats(db, current_user.id)

@router.get("/overview")
async def get_dashboard_overview(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取仪表盘概览数据"""
    # 获取总诊断次数
    total_diagnoses = db.query(func.count(DiagnosisSession.id)).filter(
        DiagnosisSession.user_id == current_user.id
    ).scalar()

    # 获取最近7天的诊断次数
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_diagnoses = db.query(func.count(DiagnosisSession.id)).filter(
        DiagnosisSession.user_id == current_user.id,
        DiagnosisSession.created_at >= seven_days_ago
    ).scalar()

    # 获取平均诊断时长
    avg_duration = db.query(func.avg(DiagnosisSession.duration)).filter(
        DiagnosisSession.user_id == current_user.id
    ).scalar() or 0

    # 获取最新的诊断结果
    latest_diagnosis = db.query(DiagnosisSession).filter(
        DiagnosisSession.user_id == current_user.id
    ).order_by(DiagnosisSession.created_at.desc()).first()

    return {
        "total_diagnoses": total_diagnoses,
        "recent_diagnoses": recent_diagnoses,
        "avg_duration": float(avg_duration),
        "latest_diagnosis": {
            "id": latest_diagnosis.id,
            "created_at": latest_diagnosis.created_at,
            "status": latest_diagnosis.status
        } if latest_diagnosis else None
    }

@router.get("/trends")
async def get_diagnosis_trends(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 7
) -> List[Dict[str, Any]]:
    """获取诊断趋势数据"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 按日期分组统计诊断次数
    daily_stats = db.query(
        func.date(DiagnosisSession.created_at).label('date'),
        func.count(DiagnosisSession.id).label('count')
    ).filter(
        DiagnosisSession.user_id == current_user.id,
        DiagnosisSession.created_at >= start_date
    ).group_by(
        func.date(DiagnosisSession.created_at)
    ).all()

    return [
        {
            "date": stat.date.strftime("%Y-%m-%d"),
            "count": stat.count
        }
        for stat in daily_stats
    ]

@router.get("/metrics")
async def get_voice_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取语音指标数据"""
    # 获取最新的语音指标
    latest_metrics = db.query(VoiceMetrics).filter(
        VoiceMetrics.user_id == current_user.id
    ).order_by(VoiceMetrics.created_at.desc()).first()

    if not latest_metrics:
        raise HTTPException(
            status_code=404,
            detail="No voice metrics found"
        )

    return {
        "id": latest_metrics.id,
        "session_id": latest_metrics.session_id,
        "prediction": latest_metrics.model_prediction,
        "confidence": latest_metrics.model_confidence,
        "created_at": latest_metrics.created_at,
        "mfcc": [
            latest_metrics.mfcc_1,
            latest_metrics.mfcc_2,
            latest_metrics.mfcc_3,
            latest_metrics.mfcc_4,
            latest_metrics.mfcc_5,
            latest_metrics.mfcc_6,
            latest_metrics.mfcc_7,
            latest_metrics.mfcc_8,
            latest_metrics.mfcc_9,
            latest_metrics.mfcc_10,
            latest_metrics.mfcc_11,
            latest_metrics.mfcc_12,
            latest_metrics.mfcc_13
        ],
        "chroma": [
            latest_metrics.chroma_1,
            latest_metrics.chroma_2,
            latest_metrics.chroma_3,
            latest_metrics.chroma_4,
            latest_metrics.chroma_5,
            latest_metrics.chroma_6,
            latest_metrics.chroma_7,
            latest_metrics.chroma_8,
            latest_metrics.chroma_9,
            latest_metrics.chroma_10,
            latest_metrics.chroma_11,
            latest_metrics.chroma_12
        ],
        "rms": latest_metrics.rms,
        "zcr": latest_metrics.zcr
    }

@router.get("/latest-session", response_model=dict)
async def get_latest_session(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取最新的诊断会话，包含诊断建议和关联的语音指标"""
    latest_session = db.query(DiagnosisSession).filter(
        DiagnosisSession.user_id == current_user.id
    ).order_by(DiagnosisSession.created_at.desc()).first()

    if not latest_session:
        return None

    # 直接通过 session_id 查找 voice_metrics
    metrics = db.query(VoiceMetrics).filter(
        VoiceMetrics.session_id == latest_session.id
    ).first()

    result = {
        "session_id": latest_session.id,
        "created_at": latest_session.created_at,
        "diagnosis_suggestion": latest_session.diagnosis_suggestion,
        "metrics": None
    }
    
    if metrics:
        result["metrics"] = {
            "model_prediction": metrics.model_prediction,
            "model_confidence": metrics.model_confidence,
            "rms": metrics.rms,
            "zcr": metrics.zcr,
            # MFCC 1-13
            **{f"mfcc_{i}": getattr(metrics, f"mfcc_{i}", None) for i in range(1, 14)},
            # Chroma 1-12
            **{f"chroma_{i}": getattr(metrics, f"chroma_{i}", None) for i in range(1, 13)}
        }
    
    return result 