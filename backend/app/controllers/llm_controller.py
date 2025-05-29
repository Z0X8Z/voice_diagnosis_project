from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
from app.db.models import DiagnosisSession
from app.services.llm_service import LLMService

# 配置日志
logger = logging.getLogger(__name__)

class LLMController:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)

    async def chat_with_llm(
        self,
        user_id: int,
        message: str,
        session_id: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """与LLM进行对话（带历史）"""
        try:
            logger.info(f"[LLMController.chat_with_llm] 开始处理聊天请求: user_id={user_id}, session_id={session_id}")
            result = await self.llm_service.chat_with_llm(user_id, message, session_id, history)
            logger.info(f"[LLMController.chat_with_llm] 聊天请求处理成功: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMController.chat_with_llm] 处理聊天请求失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"与AI助手对话失败: {str(e)}"
            )

    async def analyze_session(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """分析诊断会话"""
        try:
            logger.info(f"[LLMController.analyze_session] 开始分析会话: session_id={session_id}, user_id={user_id}")
            # 验证会话存在
            await self._validate_session(session_id, user_id)
            # 调用服务层进行分析
            result = await self.llm_service.analyze_with_llm(session_id, user_id)
            logger.info(f"[LLMController.analyze_session] 分析会话成功: session_id={session_id}")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[LLMController.analyze_session] 分析会话失败: {str(e)}", exc_info=True)
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
        """处理后续问题"""
        logger.info(f"[LLMController.handle_follow_up] 开始处理用户问题: session_id={session_id}, user_id={user_id}")
        try:
            # 验证会话存在
            await self._validate_session(session_id, user_id)
            # 调用服务层处理问题
            result = await self.llm_service.handle_follow_up(session_id, user_id, question)
            logger.info(f"[LLMController.handle_follow_up] 问题处理成功: session_id={session_id}")
            return result
        except HTTPException:
            raise
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
            # 验证会话存在
            await self._validate_session(session_id, user_id)
            # 获取对话历史
            history = await self.llm_service.get_conversation_history(session_id)
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
        try:
            logger.info(f"[LLMController.get_latest_suggestion] 获取最新建议: session_id={session_id}, user_id={user_id}")
            # 验证会话存在
            await self._validate_session(session_id, user_id)
            # 获取最新建议
            result = await self.llm_service.get_latest_suggestion(session_id)
            logger.info(f"[LLMController.get_latest_suggestion] 获取最新建议成功: session_id={session_id}")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[LLMController.get_latest_suggestion] 获取最新建议失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取最新建议失败: {str(e)}"
            )

    async def get_analysis_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取分析历史"""
        try:
            logger.info(f"[LLMController.get_analysis_history] 获取分析历史: user_id={user_id}, skip={skip}, limit={limit}")
            result = await self.llm_service.get_analysis_history(user_id, skip, limit)
            logger.info(f"[LLMController.get_analysis_history] 获取分析历史成功: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMController.get_analysis_history] 获取分析历史失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取分析历史失败: {str(e)}"
            )

    async def get_display_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用于显示的摘要数据"""
        try:
            logger.info(f"[LLMController.get_display_summary] 获取显示摘要: user_id={user_id}")
            result = await self.llm_service.get_display_summary(user_id)
            logger.info(f"[LLMController.get_display_summary] 获取显示摘要成功: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMController.get_display_summary] 获取显示摘要失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取显示摘要失败: {str(e)}"
            )

    async def get_realtime_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取实时监控数据"""
        try:
            logger.info(f"[LLMController.get_realtime_data] 获取实时数据: user_id={user_id}")
            result = await self.llm_service.get_realtime_data(user_id)
            logger.info(f"[LLMController.get_realtime_data] 获取实时数据成功: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMController.get_realtime_data] 获取实时数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取实时数据失败: {str(e)}"
            )

    async def save_conversation(
        self,
        session_id: int,
        user_id: int,
        user_message: Dict[str, str],
        assistant_message: Dict[str, str]
    ) -> bool:
        """保存对话历史"""
        try:
            logger.info(f"[LLMController.save_conversation] 保存对话: session_id={session_id}, user_id={user_id}")
            # 验证会话存在
            await self._validate_session(session_id, user_id)
            # 保存对话
            result = await self.llm_service.save_conversation(session_id, user_message, assistant_message)
            logger.info(f"[LLMController.save_conversation] 对话保存成功: session_id={session_id}")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[LLMController.save_conversation] 保存对话历史失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"保存对话历史失败: {str(e)}"
            )

    async def summarize_conversation(
        self,
        session_id: int,
        user_id: int,
        conversation: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """总结对话，生成诊断建议"""
        logger.info(f"[LLMController.summarize_conversation] 开始总结对话: session_id={session_id}, user_id={user_id}, 是否使用前端对话: {conversation is not None}")
        try:
            # 验证会话存在
            await self._validate_session(session_id, user_id)
            
            # 调用服务层总结对话
            result = await self.llm_service.summarize_conversation(session_id, user_id, conversation)
            logger.info(f"[LLMController.summarize_conversation] 对话总结成功: session_id={session_id}")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[LLMController.summarize_conversation] 总结对话失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"总结对话失败: {str(e)}"
            )
            
    async def _validate_session(self, session_id: int, user_id: int) -> DiagnosisSession:
        """验证会话是否存在且属于当前用户"""
        session = self.db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == user_id
        ).first()
        
        if not session:
            logger.warning(f"[LLMController._validate_session] 会话不存在或不属于当前用户: session_id={session_id}, user_id={user_id}")
            raise HTTPException(
                status_code=404,
                detail="诊断会话不存在或不属于当前用户"
            )
        
        return session 