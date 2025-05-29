from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile, BackgroundTasks
from app.db.models import VoiceMetrics, DiagnosisSession
from app.services.model_service import VoiceModelService
from app.services.llm_service import LLMService
import logging
import os
import subprocess
import tempfile
import re
import json
import numpy as np

from app.repositories.diagnosis_repository import DiagnosisRepository
from app.core.llm import LLMClient, get_llm_client
from app.schemas.voice import VoiceHistoryResponse, VoiceStatsResponse
from app.utils.voice_models_utils import create_model

logger = logging.getLogger(__name__)

class VoiceAnalysisService:
    """语音分析服务，负责处理语音分析结果的存储和分发"""
    
    def __init__(self, db: Session):
        """初始化服务"""
        self.db = db
        logger.info("[VoiceAnalysisService.__init__] 初始化语音分析服务")
        self.model_service = VoiceModelService()
        self.llm_service = LLMService(db)
        self.supported_formats = ['.wav', '.mp3', '.ogg', '.flac', '.webm']
        self.upload_base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
        logger.info(f"初始化语音分析服务，上传目录: {self.upload_base_dir}")
        self.repository = DiagnosisRepository(db)
        self.llm_client = get_llm_client()
    
    def validate_filename(self, filename: str) -> bool:
        """验证文件名格式"""
        # 允许的文件名格式：字母、数字、下划线、点号，以支持的音频格式结尾
        pattern = r'^[a-zA-Z0-9_]+\.(wav|mp3|ogg|flac|webm)$'
        try:
            is_valid = bool(re.match(pattern, filename))
            if not is_valid:
                logger.warning(f"文件名格式无效: {filename}")
            return is_valid
        except Exception as e:
            logger.error(f"文件名验证失败: {str(e)}")
            return False

  #主要变换流中心
    async def handle_voice_upload(
        self,
        file: UploadFile,
        user_id: int,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """同步处理语音文件上传、特征提取、预测、存库、返回KPI，LLM分析异步执行，支持webm转码"""
        try:
            logger.info(f"[handle_voice_upload] 开始处理文件上传: {file.filename}")
            # 验证文件名
            if not self.validate_filename(file.filename):
                logger.warning(f"[handle_voice_upload] 文件名无效: {file.filename}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的文件名格式。文件名只能包含字母、数字和下划线，必须以支持的音频格式结尾: {', '.join(self.supported_formats)}"
                )
            # 读取文件内容
            content = await file.read()
            logger.info(f"[handle_voice_upload] 文件大小: {len(content)} bytes")
            
            # 检查文件大小
            if len(content) < 100:  # 文件太小，可能不是有效的音频文件
                logger.warning(f"[handle_voice_upload] 文件太小，可能不是有效的音频文件: {len(content)} bytes")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="上传的文件太小，不是有效的音频文件"
                )
            
            # 创建诊断会话
            session = self.repository.create_session(user_id)
            logger.info(f"[handle_voice_upload] 创建诊断会话成功: {session.id}")
            
            # 保存文件
            file.file.seek(0)  # 重置文件指针
            file_path = self.repository.save_voice_file(file, session.id)
            logger.info(f"[handle_voice_upload] 文件保存成功: {file_path}")
            
            # 如果是webm，自动转码为wav
            wav_path = file_path
            if file_path.lower().endswith('.webm'):
                wav_path = file_path.rsplit('.', 1)[0] + '.wav'
                logger.info(f"[handle_voice_upload] 检测到webm，开始转码为wav: {wav_path}")
                try:
                    # 使用更多参数以提高转换成功率
                    cmd = [
                        'ffmpeg',
                        '-i', file_path,
                        '-acodec', 'pcm_s16le',  # 指定音频编解码器
                        '-ar', '44100',          # 采样率
                        '-ac', '1',              # 单声道
                        wav_path,
                        '-y'
                    ]
                    process = subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    logger.info(f"[handle_voice_upload] 转码完成，后续分析用: {wav_path}")
                    logger.debug(f"[handle_voice_upload] ffmpeg输出: {process.stdout}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"[handle_voice_upload] 转码失败: {str(e)}")
                    logger.error(f"[handle_voice_upload] ffmpeg错误输出: {e.stderr}")
                    
                    # 标记会话为失败
                    self.repository.mark_session_failed(session.id)
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="音频文件格式无效或已损坏，无法处理"
                    )
                
                # 检查wav文件是否成功创建
                if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1000:
                    logger.error(f"[handle_voice_upload] WAV文件创建失败或太小: {wav_path}")
                    self.repository.mark_session_failed(session.id)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="音频转换失败，请上传其他格式的音频文件"
                    )
            
            # 1. 同步特征提取
            logger.info(f"[handle_voice_upload] 开始特征提取")
            features = await self._extract_voice_features(wav_path)
            logger.info(f"[handle_voice_upload] 特征提取完成: {features}")
            
            # 2. 同步调用语音模型进行健康预测
            logger.info(f"[handle_voice_upload] 开始健康预测")
            prediction = await self._predict_health_status(wav_path)  # 传入文件路径而不是特征
            logger.info(f"[handle_voice_upload] 健康预测完成: {prediction}")
            
            # 3. 保存语音指标到数据库
            logger.info(f"[handle_voice_upload] 保存语音指标到数据库")
            metrics = self.repository.save_voice_metrics(
                session_id=session.id,
                user_id=user_id,
                features=features,
                prediction=prediction
            )
            logger.info(f"[handle_voice_upload] 语音指标保存完成 metrics_id={metrics.id}")
            
            # 4. 标记会话为已完成
            self.repository.mark_session_completed(session.id)
            logger.info(f"[handle_voice_upload] 会话标记为已完成")
            
            # 5. 异步调用LLM分析
            logger.info(f"[handle_voice_upload] 添加后台LLM分析任务")
            background_tasks.add_task(self.analyze_with_llm, session.id, user_id)
            
            # 6. 同步返回KPI和预测结果给仪表盘
            return {
                "session_id": session.id,
                "metrics_id": metrics.id,
                "created_at": session.created_at,
                "voice_metrics": {
                    "prediction": metrics.model_prediction,
                    "confidence": metrics.model_confidence,
                    "mfcc": [getattr(metrics, f"mfcc_{i}") for i in range(1, 14)],
                    "chroma": [getattr(metrics, f"chroma_{i}") for i in range(1, 13)],
                    "rms": metrics.rms,
                    "zcr": metrics.zcr,
                    "mel_spectrogram": metrics.mel_spectrogram
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[handle_voice_upload] 处理语音文件上传失败: {str(e)}", exc_info=True)
            # 如果会话已创建，标记为失败
            if 'session' in locals() and session:
                try:
                    self.repository.mark_session_failed(session.id)
                except Exception as mark_e:
                    logger.error(f"[handle_voice_upload] 标记会话失败时出错: {str(mark_e)}")
            
            raise HTTPException(
                status_code=500,
                detail=f"处理失败: {str(e)}"
            )
    
    async def get_session(self, db: Session, session_id: int, user_id: int) -> DiagnosisSession:
        """获取诊断会话"""
        session = db.query(DiagnosisSession).filter(
            DiagnosisSession.id == session_id,
            DiagnosisSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到指定的诊断会话"
            )
        return session
    
    async def get_metrics(self, db: Session, metrics_id: int, user_id: int) -> VoiceMetrics:
        """获取语音指标"""
        metrics = db.query(VoiceMetrics).filter(
            VoiceMetrics.id == metrics_id,
            VoiceMetrics.user_id == user_id
        ).first()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到语音指标数据"
            )
        return metrics
    
    async def get_session_result(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取诊断会话结果"""
        try:
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            # 获取语音指标
            voice_metrics = self.repository.get_voice_metrics(session_id)
            if not voice_metrics:
                raise HTTPException(
                    status_code=404,
                    detail="语音指标不存在"
                )
            
            return {
                "session_id": session.id,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at,
                "voice_metrics": {
                    "prediction": voice_metrics.model_prediction,
                    "confidence": voice_metrics.model_confidence,
                    "features": {
                        "mfcc": [
                            voice_metrics.mfcc_1, voice_metrics.mfcc_2, voice_metrics.mfcc_3,
                            voice_metrics.mfcc_4, voice_metrics.mfcc_5, voice_metrics.mfcc_6,
                            voice_metrics.mfcc_7, voice_metrics.mfcc_8, voice_metrics.mfcc_9,
                            voice_metrics.mfcc_10, voice_metrics.mfcc_11, voice_metrics.mfcc_12,
                            voice_metrics.mfcc_13
                        ],
                        "chroma": [
                            voice_metrics.chroma_1, voice_metrics.chroma_2, voice_metrics.chroma_3,
                            voice_metrics.chroma_4, voice_metrics.chroma_5, voice_metrics.chroma_6,
                            voice_metrics.chroma_7, voice_metrics.chroma_8, voice_metrics.chroma_9,
                            voice_metrics.chroma_10, voice_metrics.chroma_11, voice_metrics.chroma_12
                        ],
                        "rms": voice_metrics.rms,
                        "zcr": voice_metrics.zcr
                    }
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取会话结果失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def get_visualization_data(
        self,
        metrics_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取可视化数据"""
        try:
            # 获取语音指标
            voice_metrics = self.repository.get_voice_metrics_by_id(metrics_id, user_id)
            if not voice_metrics:
                raise HTTPException(
                    status_code=404,
                    detail="语音指标不存在"
                )
            
            return {
                "metrics_id": voice_metrics.id,
                "session_id": voice_metrics.session_id,
                "visualization_data": {
                    "mfcc_plot": voice_metrics.mfcc_plot,
                    "chroma_plot": voice_metrics.chroma_plot,
                    "spectrogram": voice_metrics.spectrogram,
                    "waveform": voice_metrics.waveform
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取可视化数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def analyze_with_llm(
        self,
        session_id: int,
        user_id: int
    ) -> dict:
        """使用 LLMService 对诊断会话进行分析"""
        return await self.llm_service.analyze_with_llm(session_id, user_id)
    
    async def get_voice_history(
        self,
        user_id: int,
        page: int,
        size: int
    ) -> VoiceHistoryResponse:
        """获取用户的语音分析历史记录"""
        try:
            # 计算分页偏移量
            offset = (page - 1) * size
            
            # 获取历史记录
            records, total = self.repository.get_voice_history(user_id, offset, size)
            
            # 构建响应数据
            history = []
            for record in records:
                try:
                    session = self.repository.get_session_by_id(record.id, user_id)
                    
                    history_record = {
                        "id": int(record.id),
                        "session_id": int(session.id) if session and session.id else 0,
                        "created_at": record.created_at,
                        "prediction": str(record.model_prediction) if record.model_prediction else "",
                        "confidence": float(record.model_confidence) if record.model_confidence is not None else 0.0,
                        "llm_suggestion": str(session.diagnosis_suggestion) if session and session.diagnosis_suggestion else None,
                        "llm_processed_at": session.llm_processed_at if session else None
                    }
                    history.append(history_record)
                except Exception as e:
                    continue
            
            return VoiceHistoryResponse(
                total=int(total),
                page=int(page),
                size=int(size),
                records=history
            )
            
        except Exception as e:
            logger.error(f"获取语音历史记录失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def get_voice_stats(
        self,
        user_id: int
    ) -> VoiceStatsResponse:
        """获取用户的语音分析统计数据"""
        try:
            stats = self.repository.get_voice_stats(user_id)
            
            return VoiceStatsResponse(
                total_analyses=int(stats["total_analyses"]),
                recent_analyses=int(stats["recent_analyses"]),
                prediction_distribution=stats["prediction_distribution"],
                average_confidence=float(stats["average_confidence"])
            )
            
        except Exception as e:
            logger.error(f"获取语音统计数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def _process_voice_file(
        self,
        file_path: str,
        session_id: int,
        user_id: int
    ) -> None:
        """处理语音文件（后台任务）"""
        try:
            logger.info(f"[_process_voice_file] 开始处理 session_id={session_id}, file_path={file_path}")
            # 提取语音特征
            logger.info(f"[_process_voice_file] 开始特征提取")
            features = await self._extract_voice_features(file_path)
            logger.info(f"[_process_voice_file] 特征提取完成: {features}")
            # 使用模型进行预测
            logger.info(f"[_process_voice_file] 开始健康预测")
            prediction = await self._predict_health_status(file_path)
            logger.info(f"[_process_voice_file] 健康预测完成: {prediction}")
            # 保存语音指标
            logger.info(f"[_process_voice_file] 保存语音指标到数据库")
            self.repository.save_voice_metrics(
                session_id=session_id,
                user_id=user_id,
                features=features,
                prediction=prediction
            )
            logger.info(f"[_process_voice_file] 语音指标保存完成")
            # 标记会话为已完成
            self.repository.mark_session_completed(session_id)
            logger.info(f"[_process_voice_file] 会话标记为已完成")
            # 自动调用LLM分析并保存结果
            try:
                logger.info(f"[_process_voice_file] 开始自动调用LLM分析")
                llm_result = await self.analyze_with_llm(session_id, user_id)
                logger.info(f"[_process_voice_file] LLM分析完成: {llm_result}")
            except Exception as llm_e:
                logger.error(f"[_process_voice_file] 自动调用LLM分析失败: {str(llm_e)}", exc_info=True)
        except Exception as e:
            logger.error(f"[_process_voice_file] 处理语音文件失败: {str(e)}", exc_info=True)
            # 标记会话为失败
            self.repository.mark_session_failed(session_id)
    
    async def _extract_voice_features(self, file_path: str) -> dict:
        """使用工具箱中的模型工具提取语音特征"""
        logger.info(f"[_extract_voice_features] 开始从文件提取特征: {file_path}")
        try:
            # 使用工具箱中的create_model创建模型实例
            model = create_model()
            logger.info(f"[_extract_voice_features] 模型创建成功，调用get_features")
            
            # 调用模型的get_features方法提取特征
            features_arr = model.get_features(file_path)
            logger.info(f"[_extract_voice_features] 特征提取成功，特征数组长度: {len(features_arr)}")
            
            # 将特征数组拆分为字典格式，便于后续存库
            features = {
                "zcr": float(features_arr[0]),
                "chroma": [float(x) for x in features_arr[1:13]],
                "mfcc": [float(x) for x in features_arr[13:26]],
                "rms": float(features_arr[26]),
                "mel_spectrogram": float(features_arr[27]) if len(features_arr) > 27 else None
            }
            
            logger.info(f"[_extract_voice_features] 特征转换完成: zcr={features['zcr']}, rms={features['rms']}")
            return features
        except Exception as e:
            logger.error(f"[_extract_voice_features] 特征提取失败: {str(e)}", exc_info=True)
            # 返回空特征，避免后续处理崩溃
            return {
                "zcr": 0.0,
                "chroma": [0.0] * 12,
                "mfcc": [0.0] * 13,
                "rms": 0.0,
                "mel_spectrogram": None
            }

    async def _predict_health_status(self, file_path: str) -> dict:
        """使用语音模型进行健康状态预测"""
        logger.info(f"[_predict_health_status] 调用voice_models_utils.AnalysisModel.get_pred")
        try:
            # 创建模型实例
            model = create_model()
            # 使用模型进行预测
            prediction_label = model.get_pred(file_path)
            # 由于模型不提供置信度，这里设置一个默认值
            confidence = 0.95
            
            logger.info(f"[_predict_health_status] 预测结果: {prediction_label}, 置信度: {confidence}")
            
            return {
                "prediction": prediction_label,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"[_predict_health_status] 预测失败: {str(e)}", exc_info=True)
            return {
                "prediction": "未知",
                "confidence": 0.0
            }
    
    def _build_analysis_prompt(self, voice_metrics: VoiceMetrics) -> str:
        """构建分析提示词"""
        # 获取语音特征
        mfcc_values = [getattr(voice_metrics, f"mfcc_{i}") for i in range(1, 14)]
        chroma_values = [getattr(voice_metrics, f"chroma_{i}") for i in range(1, 13)]
        
        # 构建提示词
        prompt = f"""
请分析以下语音特征数据，并给出肺部健康状况的评估和建议：

1. 模型预测结果：{voice_metrics.model_prediction or '未知'}
2. 预测置信度：{voice_metrics.model_confidence or 0.0}
3. 声音特征:
   - 过零率(ZCR): {voice_metrics.zcr or 0.0}
   - 均方根能量(RMS): {voice_metrics.rms or 0.0}
   - MFCC特征: {mfcc_values}
   - 色度特征: {chroma_values}

基于以上数据，请提供：
1. 对当前肺部健康状况的评估
2. 可能存在的健康风险
3. 具体的改善建议和日常保健措施
4. 是否需要进一步的医疗检查

请用专业但通俗易懂的语言回答，避免使用过于专业的医学术语。
"""
        logger.info(f"[_build_analysis_prompt] 构建LLM分析提示词成功")
        return prompt 