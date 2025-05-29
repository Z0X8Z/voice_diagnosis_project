from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.db.models import VoiceMetrics, DiagnosisSession
import os
import logging

class DiagnosisRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_voice_metrics(self, user_id: int, voice_file_path: str) -> VoiceMetrics:
        """创建语音指标记录"""
        metrics = VoiceMetrics(
            user_id=user_id,
            voice_file_path=voice_file_path
        )
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        return metrics
    
    def create_diagnosis_session(self, user_id: int, metrics_id: int) -> DiagnosisSession:
        """创建诊断会话"""
        session = DiagnosisSession(
            user_id=user_id,
            metrics_id=metrics_id,
            status="pending"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session_by_id(self, session_id: int, user_id: int) -> Optional[DiagnosisSession]:
        """获取诊断会话"""
        return self.db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == user_id
        ).first()
    
    def get_metrics_by_id(self, metrics_id: int, user_id: int) -> Optional[VoiceMetrics]:
        """获取语音指标"""
        return self.db.query(VoiceMetrics).filter(
            VoiceMetrics.id == metrics_id,
            VoiceMetrics.user_id == user_id
        ).first()
    
    def update_voice_metrics(self, metrics: VoiceMetrics, update_data: dict) -> VoiceMetrics:
        """更新语音指标"""
        for field, value in update_data.items():
            setattr(metrics, field, value)
        self.db.commit()
        self.db.refresh(metrics)
        return metrics
    
    def update_diagnosis_session(self, session: DiagnosisSession, update_data: dict) -> DiagnosisSession:
        """更新诊断会话"""
        for field, value in update_data.items():
            setattr(session, field, value)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_voice_history(self, user_id: int, offset: int, limit: int) -> tuple[List[VoiceMetrics], int]:
        """获取语音历史记录"""
        total = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).count()
        
        records = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).order_by(
            VoiceMetrics.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return records, total
    
    def get_voice_stats(self, user_id: int) -> Dict[str, Any]:
        """获取语音统计数据"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # 总分析次数
        total_analyses = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).count()
        
        # 最近30天分析次数
        recent_analyses = self.db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.created_at >= thirty_days_ago
        ).count()
        
        # 预测结果分布
        predictions = self.db.query(
            VoiceMetrics.model_prediction,
            func.count(VoiceMetrics.id)
        ).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.model_prediction.isnot(None)
        ).group_by(
            VoiceMetrics.model_prediction
        ).all()
        
        prediction_distribution = {
            str(pred): int(count) for pred, count in predictions if pred is not None
        }
        
        # 平均置信度
        avg_confidence = self.db.query(
            func.avg(VoiceMetrics.model_confidence)
        ).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.model_confidence.isnot(None)
        ).scalar() or 0.0
        
        return {
            "total_analyses": total_analyses,
            "recent_analyses": recent_analyses,
            "prediction_distribution": prediction_distribution,
            "average_confidence": avg_confidence
        }
    #主数据流用到
    def create_session(self, user_id: int):
        session = DiagnosisSession(
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def save_voice_file(self, file, session_id: int) -> str:
        """保存上传的语音文件到本地并返回文件路径"""
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[-1]
        file_path = os.path.join(upload_dir, f"voice_{session_id}{file_ext}")
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return file_path

    def save_voice_metrics(self, session_id: int, user_id: int, features: dict, prediction: dict):
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"[save_voice_metrics] session_id={session_id}, user_id={user_id},  prediction={prediction}")
            metrics = VoiceMetrics(
                session_id=session_id,
                user_id=user_id,
                mfcc_1=features.get("mfcc", [None]*13)[0],
                mfcc_2=features.get("mfcc", [None]*13)[1],
                mfcc_3=features.get("mfcc", [None]*13)[2],
                mfcc_4=features.get("mfcc", [None]*13)[3],
                mfcc_5=features.get("mfcc", [None]*13)[4],
                mfcc_6=features.get("mfcc", [None]*13)[5],
                mfcc_7=features.get("mfcc", [None]*13)[6],
                mfcc_8=features.get("mfcc", [None]*13)[7],
                mfcc_9=features.get("mfcc", [None]*13)[8],
                mfcc_10=features.get("mfcc", [None]*13)[9],
                mfcc_11=features.get("mfcc", [None]*13)[10],
                mfcc_12=features.get("mfcc", [None]*13)[11],
                mfcc_13=features.get("mfcc", [None]*13)[12],
                chroma_1=features.get("chroma", [None]*12)[0],
                chroma_2=features.get("chroma", [None]*12)[1],
                chroma_3=features.get("chroma", [None]*12)[2],
                chroma_4=features.get("chroma", [None]*12)[3],
                chroma_5=features.get("chroma", [None]*12)[4],
                chroma_6=features.get("chroma", [None]*12)[5],
                chroma_7=features.get("chroma", [None]*12)[6],
                chroma_8=features.get("chroma", [None]*12)[7],
                chroma_9=features.get("chroma", [None]*12)[8],
                chroma_10=features.get("chroma", [None]*12)[9],
                chroma_11=features.get("chroma", [None]*12)[10],
                chroma_12=features.get("chroma", [None]*12)[11],
                rms=features.get("rms"),
                zcr=features.get("zcr"),
                mel_spectrogram=features.get("mel_spectrogram"),
                model_prediction=prediction.get("prediction"),
                model_confidence=prediction.get("confidence"),
                created_at=datetime.utcnow()
            )
            self.db.add(metrics)
            self.db.commit()
            self.db.refresh(metrics)
            logger.info(f"[save_voice_metrics] 保存成功 metrics_id={metrics.id}")
            return metrics
        except Exception as e:
            logger.error(f"[save_voice_metrics] 保存失败: {str(e)}", exc_info=True)
            raise 

    def mark_session_completed(self, session_id: int) -> DiagnosisSession:
        """标记诊断会话为已完成"""
        logger = logging.getLogger(__name__)
        try:
            session = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id
            ).first()
            
            if not session:
                logger.warning(f"[mark_session_completed] 会话不存在: {session_id}")
                return None
                
            session.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"[mark_session_completed] 会话已标记为完成: {session_id}")
            return session
        except Exception as e:
            logger.error(f"[mark_session_completed] 标记会话失败: {str(e)}", exc_info=True)
            raise
    
    def mark_session_failed(self, session_id: int) -> DiagnosisSession:
        """标记诊断会话为失败（已移除 error_message 字段，仅更新时间）"""
        logger = logging.getLogger(__name__)
        try:
            session = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id
            ).first()
            if not session:
                logger.warning(f"[mark_session_failed] 会话不存在: {session_id}")
                return None
            session.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"[mark_session_failed] 会话已标记为失败: {session_id}")
            return session
        except Exception as e:
            logger.error(f"[mark_session_failed] 标记会话失败: {str(e)}", exc_info=True)
            raise
    
    def get_voice_metrics(self, session_id: int) -> Optional[VoiceMetrics]:
        """通过会话ID获取语音指标"""
        logger = logging.getLogger(__name__)
        try:
            metrics = self.db.query(VoiceMetrics).filter(
                VoiceMetrics.session_id == session_id
            ).first()
            return metrics
        except Exception as e:
            logger.error(f"[get_voice_metrics] 获取语音指标失败: {str(e)}", exc_info=True)
            return None
    
    def update_session_llm_suggestion(self, session_id: int, llm_suggestion: str) -> DiagnosisSession:
        """更新会话的LLM建议"""
        logger = logging.getLogger(__name__)
        try:
            session = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id
            ).first()
            
            if not session:
                logger.warning(f"[update_session_llm_suggestion] 会话不存在: {session_id}")
                return None
                
            session.diagnosis_suggestion = llm_suggestion
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"[update_session_llm_suggestion] 更新LLM建议成功: {session_id}")
            return session
        except Exception as e:
            logger.error(f"[update_session_llm_suggestion] 更新LLM建议失败: {str(e)}", exc_info=True)
            raise 