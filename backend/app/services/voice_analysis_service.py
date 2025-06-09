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
import librosa

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
            
            # 不再使用固定置信度，而是基于音频质量评估
            # 评估音频质量并生成置信度分数
            audio_quality_score = await self._evaluate_audio_quality(file_path)
            logger.info(f"[_predict_health_status] 音频质量评分: {audio_quality_score}")
            
            # 将音频质量评分作为置信度返回
            confidence = audio_quality_score
            
            logger.info(f"[_predict_health_status] 预测结果: {prediction_label}, 置信度(基于音频质量): {confidence}")
            
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
            
    async def _evaluate_audio_quality(self, file_path: str) -> float:
        """
        评估音频质量，生成质量评分 (0-1范围)
        
        评分标准:
        - 信噪比 (SNR)
        - 音频能量和稳定性
        - 语音频率特征
        - 静音段比例
        - 过零率规律性
        - 语音活动检测 (VAD)
        - 呼吸声特征验证
        
        质量越差，分数越低，表示分析结果越不可信
        """
        try:
            # 加载音频文件
            y, sr = librosa.load(file_path, sr=None)
            
            # 1. 计算信噪比 (估计值)
            # 使用短时能量方差作为噪声水平评估
            frame_length = int(sr * 0.025)  # 25ms 帧
            hop_length = int(sr * 0.010)    # 10ms 跨步
            
            # 计算短时能量
            energy = np.array([
                sum(abs(y[i:i+frame_length]**2)) 
                for i in range(0, len(y)-frame_length, hop_length)
            ])
            
            # 使用能量方差评估噪声
            energy_mean = np.mean(energy)
            energy_std = np.std(energy)
            energy_var = energy_std / energy_mean if energy_mean > 0 else 0
            
            # 将方差归一化为质量分数 (方差越大，质量越差)
            energy_score = max(0, 1 - min(1, energy_var * 2))
            
            # 2. 评估音频长度是否足够
            duration = len(y) / sr
            duration_score = min(1.0, duration / 2.0)
            
            # 3. 静音段比例 (静音太多质量差)
            silence_threshold = 0.01 * np.max(np.abs(y))
            silence_ratio = np.sum(np.abs(y) < silence_threshold) / len(y)
            silence_score = 1.0 - max(0, min(1.0, (silence_ratio - 0.2) / 0.6))
            
            # 如果静音比例过高，直接判定为低质量录音
            if silence_ratio > 0.7:  # 超过70%是静音
                logger.warning(f"[_evaluate_audio_quality] 检测到静音比例过高: {silence_ratio:.2f}")
                return 0.3  # 返回较低的质量分数
            
            # 4. 过零率规律性 (语音应该有一定规律性)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_std = np.std(zcr)
            zcr_score = min(1.0, zcr_std * 25)
            
            # 5. 频谱质心的变化 (自然语音有丰富的变化)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_score = min(1.0, np.std(spectral_centroid) / 400)
            
            # 6. **新增**: 语音活动检测 (VAD)
            # 使用短时能量和过零率特征进行简单VAD
            energy_frames = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # 设置能量阈值 (基于音频能量分布)
            energy_threshold = 0.05 * np.max(energy_frames)
            
            # 计算声音活动帧的比例
            active_frames = np.sum(energy_frames > energy_threshold) / len(energy_frames)
            
            # VAD得分: 至少要有一定比例的有声帧才能得到高分
            vad_score = min(1.0, active_frames / 0.3)  # 要求至少30%的帧有声音活动
            
            # 如果几乎没有声音活动，大幅降低总评分
            if active_frames < 0.1:  # 不足10%的帧有声音活动
                logger.warning(f"[_evaluate_audio_quality] 几乎没有检测到声音活动: {active_frames:.2f}")
                return 0.3  # 返回较低的质量分数
            
            # 7. **新增**: 呼吸声特征验证
            # 计算呼吸声频率范围内的能量 (典型呼吸声频率为200-800Hz)
            respiration_band = [200, 800]
            
            # 计算FFT
            n_fft = 2048
            D = np.abs(librosa.stft(y, n_fft=n_fft))
            
            # 获取频率范围
            freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
            
            # 提取呼吸声频率范围内的能量
            resp_mask = (freqs >= respiration_band[0]) & (freqs <= respiration_band[1])
            resp_energy = np.mean(D[resp_mask, :])
            
            # 计算总能量
            total_energy = np.mean(D)
            
            # 呼吸特征比例 (呼吸声频率范围内的能量占比)
            resp_ratio = resp_energy / total_energy if total_energy > 0 else 0
            
            # 呼吸声特征得分 (在呼吸声典型频率范围内应有一定能量)
            respiration_score = min(1.0, resp_ratio * 10)
            
            # 如果呼吸频率范围的能量占比太低，可能不是呼吸声或语音
            if resp_ratio < 0.05:  # 小于5%的能量在呼吸声频率范围
                logger.warning(f"[_evaluate_audio_quality] 呼吸声特征比例过低: {resp_ratio:.4f}")
                # 降低分数，但不要完全否决
                respiration_score = respiration_score * 0.5
            
            # 综合得分 (调整权重，加入VAD和呼吸声特征)
            weights = {
                'energy': 0.15,      # 降低原始指标权重
                'duration': 0.10,
                'silence': 0.15,
                'zcr': 0.10,
                'spectral': 0.10,
                'vad': 0.25,         # 语音活动检测权重较高
                'respiration': 0.15  # 呼吸声特征检测
            }
            
            quality_score = (
                weights['energy'] * energy_score +
                weights['duration'] * duration_score +
                weights['silence'] * silence_score +
                weights['zcr'] * zcr_score +
                weights['spectral'] * spectral_score +
                weights['vad'] * vad_score +
                weights['respiration'] * respiration_score
            )
            
            # 调整基础分数，考虑VAD和呼吸声特征的重要性
            base_score = 0.3
            quality_score = base_score + (1.0 - base_score) * quality_score
            
            # 应用更严格的最低标准
            quality_score = max(0.2, min(0.95, quality_score))
            
            logger.info(f"[_evaluate_audio_quality] 音频质量分析: "
                      f"能量={energy_score:.2f}, "
                      f"长度={duration_score:.2f}, "
                      f"静音={silence_score:.2f}, "
                      f"过零={zcr_score:.2f}, "
                      f"频谱={spectral_score:.2f}, "
                      f"VAD={vad_score:.2f}, "
                      f"呼吸={respiration_score:.2f}, "
                      f"总分={quality_score:.2f}")
                      
            return quality_score
            
        except Exception as e:
            logger.error(f"[_evaluate_audio_quality] 音频质量评估失败: {str(e)}", exc_info=True)
            # 默认返回中等偏低分数
            return 0.4
    
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