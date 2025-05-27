from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import DiagnosisSession
from app.services.llm_service import LLMService
import json
import logging

# 配置日志
logger = logging.getLogger(__name__)

class LLMController:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)

    async def analyze_session(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """分析诊断会话"""
        try:
            session = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id,
                DiagnosisSession.user_id == user_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            # 这里添加实际的 LLM 分析逻辑
            # 示例：生成诊断建议
            diagnosis_suggestion = "根据语音分析，建议进行进一步检查..."
            follow_up_questions = ["您最近是否有其他症状？", "症状持续多久了？"]
            
            # 更新会话
            session.diagnosis_suggestion = diagnosis_suggestion
            session.follow_up_questions = json.dumps(follow_up_questions)
            session.conversation_history = json.dumps([
                {"role": "system", "content": "您是一位专业的医疗顾问。"},
                {"role": "assistant", "content": diagnosis_suggestion}
            ])
            
            self.db.commit()
            
            return {
                "session_id": session.id,
                "diagnosis_suggestion": diagnosis_suggestion,
                "follow_up_questions": follow_up_questions
            }
        except Exception as e:
            logger.error(f"[LLMController.analyze_session] 处理分析会话失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"分析会话失败: {str(e)}"
            )

    async def handle_follow_up(
        self,
        session_id: int,
        user_id: int,
        question: str
    ) -> Dict[str, Any]:
        """处理后续问题，保存对话历史"""
        logger.info(f"[LLMController.handle_follow_up] 开始处理用户问题: session_id={session_id}, user_id={user_id}")
        try:
            # 调用LLM服务处理问题
            result = await self.llm_service.handle_follow_up(session_id, user_id, question)
            logger.info(f"[LLMController.handle_follow_up] 问题处理成功: session_id={session_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMController.handle_follow_up] 处理问题失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"处理问题失败: {str(e)}"
            )

    async def get_conversation_history(
        self,
        session_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        logger.info(f"[LLMController.get_conversation_history] 获取对话历史: session_id={session_id}, user_id={user_id}")
        try:
            # 验证会话所有权
            session = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id,
                DiagnosisSession.user_id == user_id
            ).first()
            
            if not session:
                logger.warning(f"[LLMController.get_conversation_history] 会话不存在: session_id={session_id}, user_id={user_id}")
                raise HTTPException(
                    status_code=404,
                    detail="会话不存在"
                )
            
            # 使用仓库获取对话历史
            history = self.llm_service.repository.get_conversation_history(session_id)
            logger.info(f"[LLMController.get_conversation_history] 获取到对话历史: session_id={session_id}, 消息数量={len(history)}")
            return history
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[LLMController.get_conversation_history] 获取对话历史失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取对话历史失败: {str(e)}"
            )

    async def get_latest_suggestion(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取最新的 LLM 建议"""
        session = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        return {
            "session_id": session.id,
            "diagnosis_suggestion": session.diagnosis_suggestion,
            "follow_up_questions": json.loads(session.follow_up_questions or "[]")
        }

    async def get_analysis_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取分析历史"""
        sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).order_by(
            DiagnosisSession.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": session.id,
                "created_at": session.created_at,
                "analysis_progress": session.analysis_progress,
                "diagnosis_suggestion": session.diagnosis_suggestion
            }
            for session in sessions
        ]

    async def get_display_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用于显示的摘要数据"""
        total_sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).count()
        
        completed_sessions = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id,
            DiagnosisSession.analysis_progress == 100
        ).count()
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        }

    async def get_realtime_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取实时监控数据"""
        # 这里可以添加实时数据的获取逻辑
        return {
            "active_sessions": 0,
            "processing_sessions": 0,
            "completed_today": 0
        }

    async def save_conversation(
        self,
        session_id: int,
        user_id: int,
        user_message: Dict[str, str],
        assistant_message: Dict[str, str]
    ) -> bool:
        """保存对话历史"""
        try:
            session = self.db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id,
                DiagnosisSession.user_id == user_id
            ).first()
            
            if not session:
                raise ValueError(f"找不到会话ID: {session_id}")
            
            # 获取现有对话历史
            conversation_history = json.loads(session.conversation_history or "[]")
            
            # 添加用户消息和助手消息
            conversation_history.append(user_message)
            conversation_history.append(assistant_message)
            
            # 更新会话
            session.conversation_history = json.dumps(conversation_history)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"保存对话历史失败: {str(e)}"
            )

    async def summarize_conversation(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """总结对话，生成诊断建议"""
        logger.info(f"[LLMController.summarize_conversation] 开始总结对话: session_id={session_id}, user_id={user_id}")
        try:
            # 调用LLM服务总结对话
            result = await self.llm_service.summarize_conversation(session_id, user_id)
            logger.info(f"[LLMController.summarize_conversation] 对话总结成功: session_id={session_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMController.summarize_conversation] 总结对话失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"总结对话失败: {str(e)}"
            ) 