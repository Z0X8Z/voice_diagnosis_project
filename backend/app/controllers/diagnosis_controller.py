from fastapi import APIRouter, Depends, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.voice_analysis_service import VoiceAnalysisService
from app.schemas.voice import VoiceHistoryResponse, VoiceStatsResponse
from typing import Dict, Any, List
from app.services.llm_service import LLMService
from app.repositories.llm_repository import LLMRepository



class DiagnosisController:
    """诊断控制器，负责协调语音分析和 LLM 服务"""
    
    def __init__(self, db: Session):
        """
        初始化诊断控制器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.llm_repository = LLMRepository(db)
        self.llm_service = LLMService(db)
        self.voice_analysis_service = VoiceAnalysisService(db)
    
    async def analyze_session(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        分析诊断会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            分析结果
        """
        return await self.llm_service.analyze_session(session_id, user_id)
    
    async def handle_follow_up(
        self,
        session_id: int,
        user_id: int,
        question: str
    ) -> Dict[str, Any]:
        """
        处理后续问题
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            question: 用户问题
            
        Returns:
            回答结果
        """
        return await self.llm_service.handle_follow_up(session_id, user_id, question)
    
    async def get_conversation_history(
        self,
        session_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            对话历史记录
        """
        return await self.llm_service.get_conversation_history(session_id, user_id)
    
    async def get_latest_suggestion(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取最新的 LLM 建议
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            最新建议
        """
        return await self.llm_service.get_latest_suggestion(session_id, user_id)
    
    async def get_analysis_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取分析历史
        
        Args:
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            分析历史记录
        """
        return await self.llm_service.get_analysis_history(user_id, skip, limit)
    
    async def get_display_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取显示摘要数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            显示摘要数据
        """
        return await self.llm_service.get_display_summary(user_id)
    
    async def get_realtime_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取实时监控数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            实时监控数据
        """
        return await self.llm_service.get_realtime_data(user_id) 
#主数据流用到
    async def upload_voice_file(self, file, user_id, background_tasks):
        """上传语音文件并处理"""
        return await self.voice_analysis_service.handle_voice_upload(file, user_id, background_tasks) 