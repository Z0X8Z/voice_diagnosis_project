import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.db.models import DiagnosisSession, VoiceMetrics
import json

# 配置日志
logger = logging.getLogger(__name__)

class LLMRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_session_by_id(self, session_id: int, user_id: int) -> DiagnosisSession:
        """获取诊断会话"""
        session = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == user_id
        ).first()
        if session:
            logger.info(f"[get_session_by_id] 找到会话: session_id={session_id}, user_id={user_id}")
        else:
            logger.warning(f"[get_session_by_id] 会话不存在: session_id={session_id}, user_id={user_id}")
        return session
    
    def get_voice_metrics(self, session_id: int) -> VoiceMetrics:
        """获取语音指标"""
        metrics = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.session_id == session_id
        ).first()
        if metrics:
            logger.info(f"[get_voice_metrics] 找到语音指标: session_id={session_id}")
        else:
            logger.warning(f"[get_voice_metrics] 语音指标不存在: session_id={session_id}")
        return metrics
    
    def get_conversation_history(self, session_id: int) -> List[Dict[str, Any]]:
        """获取对话历史（已不再依赖 conversation_history 字段）"""
        logger.info(f"[get_conversation_history] 开始获取对话历史: session_id={session_id}")
        session = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id
        ).first()
        if not session:
            logger.warning(f"[get_conversation_history] 会话不存在: session_id={session_id}")
            return []
        # 仅返回诊断建议作为初始消息
        if session.diagnosis_suggestion:
            return [{
                "role": "assistant",
                "content": session.diagnosis_suggestion,
                "created_at": session.created_at
            }]
        return []
    
    def update_session_diagnosis_suggestion(self, session_id: int, suggestion: str) -> None:
        """更新会话的诊断建议"""
        logger.info(f"[update_session_diagnosis_suggestion] 开始更新诊断建议: session_id={session_id}")
        session = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id
        ).first()
        
        if session:
            session.diagnosis_suggestion = suggestion
            session.created_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"[update_session_diagnosis_suggestion] 诊断建议更新成功: session_id={session_id}")
        else:
            logger.error(f"[update_session_diagnosis_suggestion] 会话不存在，无法更新诊断建议: session_id={session_id}")
    
    def get_voice_history(
        self,
        user_id: int,
        offset: int,
        limit: int
    ) -> Tuple[List[VoiceMetrics], int]:
        """获取语音历史记录"""
        query = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).order_by(desc(VoiceMetrics.created_at))
        
        total = query.count()
        records = query.offset(offset).limit(limit).all()
        
        return records, total
    
    def get_voice_stats(self, user_id: int) -> Dict[str, Any]:
        """获取语音统计数据"""
        # 获取总分析次数
        total_analyses = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).count()
        
        # 获取最近7天的分析次数
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_analyses = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.created_at >= recent_date
        ).count()
        
        # 获取预测分布
        predictions = self.db.query(
            VoiceMetrics.model_prediction,
            VoiceMetrics.model_confidence
        ).filter(
            VoiceMetrics.user_id == user_id
        ).all()
        
        prediction_distribution = {}
        total_confidence = 0
        valid_predictions = 0
        
        for pred, conf in predictions:
            if pred and conf is not None:
                prediction_distribution[pred] = prediction_distribution.get(pred, 0) + 1
                total_confidence += conf
                valid_predictions += 1
        
        # 计算平均置信度
        average_confidence = total_confidence / valid_predictions if valid_predictions > 0 else 0
        
        return {
            "total_analyses": total_analyses,
            "recent_analyses": recent_analyses,
            "prediction_distribution": prediction_distribution,
            "average_confidence": average_confidence
        }
    #主数据流用到

    def get_analysis_history(self, user_id: int, skip: int, limit: int) -> List[Dict[str, Any]]:
        """获取分析历史"""
        sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).order_by(
            DiagnosisSession.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        history = []
        for session in sessions:
            voice_metrics = self.get_voice_metrics(session.id)
            history.append({
                "session_id": session.id,
                "created_at": session.created_at,
                "health_status": voice_metrics.model_prediction if voice_metrics else None,
                "diagnosis_suggestion": session.diagnosis_suggestion,
                "llm_processed_at": session.created_at
            })
        return history
    
    def get_display_summary(self, user_id: int) -> Dict[str, Any]:
        """获取显示摘要数据"""
        # 总诊断会话数
        total_sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).count()
        
        # 今日会话数
        today = datetime.now().date()
        today_sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id,
            DiagnosisSession.created_at >= today
        ).count()
        
        # 健康状况分布
        health_statuses = self.db.query(
            VoiceMetrics.model_prediction, 
            self.db.func.count(VoiceMetrics.id)
        ).join(
            DiagnosisSession, 
            VoiceMetrics.session_id == DiagnosisSession.id
        ).filter(
            DiagnosisSession.user_id == user_id
        ).group_by(
            VoiceMetrics.model_prediction
        ).all()
        
        health_distribution = {status: count for status, count in health_statuses}
        
        # 过去一周的会话趋势
        one_week_ago = datetime.now() - timedelta(days=7)
        session_trend = []
        
        for i in range(7):
            date = one_week_ago + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            count = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.user_id == user_id,
                DiagnosisSession.created_at >= date,
                DiagnosisSession.created_at < next_date
            ).count()
            
            session_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
        return {
            "total_sessions": total_sessions,
            "today_sessions": today_sessions,
            "health_distribution": health_distribution,
            "session_trend": session_trend
        }
    
    def get_realtime_data(self, user_id: int) -> Dict[str, Any]:
        """获取实时监控数据"""
        # 最近的诊断会话
        recent_sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).order_by(
            DiagnosisSession.created_at.desc()
        ).limit(5).all()
        
        recent_session_data = []
        for session in recent_sessions:
            voice_metrics = self.get_voice_metrics(session.id)
            
            session_data = {
                "id": session.id,
                "timestamp": session.created_at.isoformat(),
                "status": session.status,
                "health_status": voice_metrics.model_prediction if voice_metrics else "未分析"
            }
            
            recent_session_data.append(session_data)
        
        return {
            "recent_sessions": recent_session_data,
            "system_status": {
                "cpu_usage": 45,  # 模拟数据
                "memory_usage": 60,  # 模拟数据
                "storage_usage": 30,  # 模拟数据
                "active_users": 120  # 模拟数据
            }
        }
    
    def save_conversation(self, session_id: int, conversation: list) -> None:
        """保存对话历史（字段已废弃，方法保留空实现以兼容调用）"""
        logger.info(f"[save_conversation] 已废弃，不再保存对话历史: session_id={session_id}")
        pass 