import numpy as np
from scipy import signal
from typing import Dict, Any, Tuple
import logging
import tempfile
import os
from fastapi import UploadFile, HTTPException
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)

class MicrophoneTestService:
    """麦克风质量评估服务"""
    
    def __init__(self):
        self.SAMPLE_RATE = 44100  # 采样率
        self.NOISE_RMS_THRESHOLD = 0.005  # 环境噪声RMS阈值（安静环境）
        self.BREATH_RMS_THRESHOLD = 0.01  # 呼吸音RMS阈值（最低音量）
        self.SNR_THRESHOLD = 15  # 信噪比阈值（dB）
        self.FREQ_RANGE = (100, 1000)  # 呼吸音频率范围（Hz）
        
    def calculate_rms(self, audio: np.ndarray) -> float:
        """计算音频的RMS（均方根）值，反映音量大小"""
        return float(np.sqrt(np.mean(np.square(audio))))
    
    def calculate_snr(self, signal_audio: np.ndarray, noise_audio: np.ndarray) -> float:
        """计算信噪比（SNR），单位dB"""
        signal_power = np.mean(np.square(signal_audio))
        noise_power = np.mean(np.square(noise_audio))
        if noise_power == 0:
            noise_power = 1e-10  # 避免除零
        snr = 10 * np.log10(signal_power / noise_power)
        return float(snr)
    
    def analyze_frequency(self, audio: np.ndarray, sample_rate: int, freq_range: Tuple[int, int]) -> float:
        """分析音频在指定频率范围内的能量占比"""
        try:
            freqs, psd = signal.welch(audio, sample_rate, nperseg=1024)
            freq_mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
            total_power = np.sum(psd)
            target_power = np.sum(psd[freq_mask])
            return float(target_power / total_power if total_power > 0 else 0)
        except Exception as e:
            logger.error(f"频率分析失败: {str(e)}")
            return 0.0
    
    async def analyze_microphone_quality(self, noise_file: UploadFile, breath_file: UploadFile) -> Dict[str, Any]:
        """
        分析麦克风质量
        
        Args:
            noise_file: 环境噪声音频文件
            breath_file: 呼吸音音频文件
            
        Returns:
            麦克风质量评估结果
        """
        try:
            logger.info("开始麦克风质量评估")
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as noise_temp:
                noise_content = await noise_file.read()
                noise_temp.write(noise_content)
                noise_path = noise_temp.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as breath_temp:
                breath_content = await breath_file.read()
                breath_temp.write(breath_content)
                breath_path = breath_temp.name
            
            try:
                # 加载音频文件
                noise_audio, noise_sr = librosa.load(noise_path, sr=self.SAMPLE_RATE)
                breath_audio, breath_sr = librosa.load(breath_path, sr=self.SAMPLE_RATE)
                
                # 分析环境噪声
                noise_rms = self.calculate_rms(noise_audio)
                logger.info(f"环境噪声RMS: {noise_rms:.4f}")
                
                # 分析呼吸音
                breath_rms = self.calculate_rms(breath_audio)
                snr = self.calculate_snr(breath_audio, noise_audio)
                freq_ratio = self.analyze_frequency(breath_audio, self.SAMPLE_RATE, self.FREQ_RANGE)
                
                logger.info(f"呼吸音RMS: {breath_rms:.4f}")
                logger.info(f"信噪比(SNR): {snr:.2f} dB")
                logger.info(f"呼吸音频率能量占比: {freq_ratio:.2%}")
                
                # 评估结果
                issues = []
                recommendations = []
                overall_quality = "良好"
                
                # 检查环境噪声
                if noise_rms > self.NOISE_RMS_THRESHOLD:
                    issues.append("环境噪声过高")
                    recommendations.append("请在更安静的环境中使用，关闭风扇、空调等噪音源")
                    overall_quality = "需要改善"
                
                # 检查呼吸音音量
                if breath_rms < self.BREATH_RMS_THRESHOLD:
                    issues.append("呼吸音音量过低")
                    recommendations.append("请检查麦克风灵敏度或靠近麦克风（建议距离10-20厘米）")
                    overall_quality = "需要改善"
                
                # 检查信噪比
                if snr < self.SNR_THRESHOLD:
                    issues.append("信噪比不足")
                    recommendations.append("可能受背景噪声干扰或麦克风质量不佳，请更换更好的麦克风")
                    overall_quality = "需要改善"
                
                # 检查频率特征
                if freq_ratio < 0.5:
                    issues.append("麦克风捕捉的呼吸音频率特征不足")
                    recommendations.append("请更换更灵敏的麦克风，确保能够捕捉低频呼吸音")
                    overall_quality = "需要改善"
                
                # 如果没有问题，给出积极反馈
                if not issues:
                    recommendations.append("麦克风和环境质量良好，适合录制呼吸音！")
                
                # 生成质量评分（0-100）
                quality_score = 100
                if noise_rms > self.NOISE_RMS_THRESHOLD:
                    quality_score -= 25
                if breath_rms < self.BREATH_RMS_THRESHOLD:
                    quality_score -= 25
                if snr < self.SNR_THRESHOLD:
                    quality_score -= 25
                if freq_ratio < 0.5:
                    quality_score -= 25
                
                return {
                    "overall_quality": overall_quality,
                    "quality_score": int(max(0, quality_score)),
                    "test_passed": len(issues) == 0,
                    "metrics": {
                        "noise_rms": float(noise_rms),
                        "breath_rms": float(breath_rms),
                        "snr": float(snr),
                        "frequency_ratio": float(freq_ratio)
                    },
                    "thresholds": {
                        "noise_rms_threshold": float(self.NOISE_RMS_THRESHOLD),
                        "breath_rms_threshold": float(self.BREATH_RMS_THRESHOLD),
                        "snr_threshold": float(self.SNR_THRESHOLD),
                        "frequency_ratio_threshold": 0.5
                    },
                    "issues": issues,
                    "recommendations": recommendations,
                    "detailed_analysis": {
                        "noise_analysis": "良好" if noise_rms <= self.NOISE_RMS_THRESHOLD else "噪声过高",
                        "volume_analysis": "良好" if breath_rms >= self.BREATH_RMS_THRESHOLD else "音量不足",
                        "snr_analysis": "良好" if snr >= self.SNR_THRESHOLD else "信噪比低",
                        "frequency_analysis": "良好" if freq_ratio >= 0.5 else "频率特征不足"
                    }
                }
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(noise_path)
                    os.unlink(breath_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"麦克风质量评估失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"麦克风质量评估失败: {str(e)}"
            )
    
    async def analyze_breath_quality_only(self, breath_file: UploadFile) -> Dict[str, Any]:
        """
        仅分析呼吸音质量（用于多次录音的实时检测）
        
        Args:
            breath_file: 呼吸音音频文件
            
        Returns:
            呼吸音质量评估结果
        """
        try:
            logger.info("开始单独呼吸音质量检测")
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as breath_temp:
                breath_content = await breath_file.read()
                breath_temp.write(breath_content)
                breath_path = breath_temp.name
            
            try:
                # 加载音频文件
                breath_audio, breath_sr = librosa.load(breath_path, sr=self.SAMPLE_RATE)
                
                # 分析呼吸音
                breath_rms = self.calculate_rms(breath_audio)
                freq_ratio = self.analyze_frequency(breath_audio, self.SAMPLE_RATE, self.FREQ_RANGE)
                
                # 计算音频时长
                duration = len(breath_audio) / self.SAMPLE_RATE
                
                # 分析音频的静音段比例
                silence_threshold = breath_rms * 0.1  # 静音阈值为平均音量的10%
                silence_samples = np.sum(np.abs(breath_audio) < silence_threshold)
                silence_ratio = silence_samples / len(breath_audio)
                
                logger.info(f"呼吸音RMS: {breath_rms:.4f}")
                logger.info(f"呼吸音时长: {duration:.2f}秒")
                logger.info(f"呼吸音频率能量占比: {freq_ratio:.2%}")
                logger.info(f"静音比例: {silence_ratio:.2%}")
                
                # 评估结果
                issues = []
                suggestions = []
                quality_score = 100
                
                # 检查音频时长
                if duration < 3.0:
                    issues.append("录音时长不足")
                    suggestions.append("请录制至少3-5秒的呼吸音")
                    quality_score -= 20
                elif duration > 10.0:
                    issues.append("录音时长过长")
                    suggestions.append("请控制录音时长在5-8秒内")
                    quality_score -= 10
                
                # 检查呼吸音音量
                if breath_rms < self.BREATH_RMS_THRESHOLD:
                    issues.append("呼吸音音量过低")
                    suggestions.append("请靠近麦克风（建议距离10-20厘米）或增加呼吸强度")
                    quality_score -= 30
                elif breath_rms > 0.1:  # 音量过高
                    issues.append("呼吸音音量过高")
                    suggestions.append("请适当远离麦克风或减轻呼吸强度")
                    quality_score -= 15
                
                # 检查频率特征
                if freq_ratio < 0.3:
                    issues.append("呼吸音频率特征不明显")
                    suggestions.append("请确保正常呼吸，避免屏气或过于轻微的呼吸")
                    quality_score -= 25
                
                # 检查静音比例
                if silence_ratio > 0.7:
                    issues.append("录音中静音段过多")
                    suggestions.append("请持续进行呼吸，避免长时间暂停")
                    quality_score -= 20
                
                # 检查音频一致性（标准差）
                audio_std = np.std(breath_audio)
                if audio_std < breath_rms * 0.3:
                    issues.append("呼吸音变化过小")
                    suggestions.append("请进行更明显的深呼吸动作")
                    quality_score -= 15
                
                # 音质评级
                if quality_score >= 85:
                    quality_level = "优秀"
                    is_acceptable = True
                elif quality_score >= 70:
                    quality_level = "良好"
                    is_acceptable = True
                elif quality_score >= 50:
                    quality_level = "一般"
                    is_acceptable = False
                else:
                    quality_level = "较差"
                    is_acceptable = False
                
                # 如果没有问题，给出积极反馈
                if not issues:
                    suggestions.append("呼吸音质量很好，可以用于分析！")
                
                return {
                    "is_acceptable": is_acceptable,
                    "quality_score": int(max(0, quality_score)),
                    "quality_level": quality_level,
                    "duration": float(duration),
                    "metrics": {
                        "breath_rms": float(breath_rms),
                        "frequency_ratio": float(freq_ratio),
                        "silence_ratio": float(silence_ratio),
                        "audio_std": float(audio_std)
                    },
                    "thresholds": {
                        "min_duration": 3.0,
                        "max_duration": 10.0,
                        "min_rms": float(self.BREATH_RMS_THRESHOLD),
                        "max_rms": 0.1,
                        "min_freq_ratio": 0.3,
                        "max_silence_ratio": 0.7
                    },
                    "issues": issues,
                    "suggestions": suggestions,
                    "detailed_feedback": {
                        "volume_feedback": self._get_volume_feedback(breath_rms),
                        "duration_feedback": self._get_duration_feedback(duration),
                        "quality_feedback": self._get_quality_feedback(freq_ratio, silence_ratio)
                    }
                }
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(breath_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"呼吸音质量检测失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"呼吸音质量检测失败: {str(e)}"
            )
    
    def _get_volume_feedback(self, rms: float) -> str:
        """获取音量反馈"""
        if rms < self.BREATH_RMS_THRESHOLD * 0.5:
            return "音量太低，请靠近麦克风或加大呼吸强度"
        elif rms < self.BREATH_RMS_THRESHOLD:
            return "音量偏低，建议靠近麦克风"
        elif rms > 0.1:
            return "音量过高，请适当远离麦克风"
        elif rms > 0.05:
            return "音量偏高，可以稍微远离麦克风"
        else:
            return "音量适中，很好！"
    
    def _get_duration_feedback(self, duration: float) -> str:
        """获取时长反馈"""
        if duration < 3.0:
            return "录音太短，请录制3-5秒"
        elif duration > 10.0:
            return "录音太长，建议控制在5-8秒"
        elif 4.0 <= duration <= 6.0:
            return "录音时长完美！"
        else:
            return "录音时长可接受"
    
    def _get_quality_feedback(self, freq_ratio: float, silence_ratio: float) -> str:
        """获取质量反馈"""
        if freq_ratio < 0.3:
            return "呼吸音特征不明显，请进行更深的呼吸"
        elif silence_ratio > 0.7:
            return "静音段过多，请持续呼吸"
        else:
            return "呼吸音特征良好！"
    
    def generate_test_instructions(self) -> Dict[str, Any]:
        """生成麦克风测试说明"""
        return {
            "title": "麦克风质量评估",
            "description": "为了确保最佳的语音分析效果，请按照以下步骤进行麦克风质量测试",
            "steps": [
                {
                    "step": 1,
                    "title": "环境准备",
                    "description": "请保持安静，关闭风扇、空调等噪音源",
                    "duration": "准备阶段",
                    "tips": ["选择安静的房间", "关闭门窗", "避免外界干扰"]
                },
                {
                    "step": 2,
                    "title": "环境噪声测试",
                    "description": "请保持完全安静，不要说话或产生任何声音",
                    "duration": "录制2秒",
                    "tips": ["不要移动", "不要说话", "保持静止"]
                },
                {
                    "step": 3,
                    "title": "呼吸音测试",
                    "description": "请靠近麦克风（10-20厘米），缓慢深呼吸",
                    "duration": "录制5秒",
                    "tips": ["正对麦克风", "缓慢呼吸", "保持稳定距离"]
                }
            ],
            "quality_criteria": {
                "环境噪声": f"RMS值应小于 {self.NOISE_RMS_THRESHOLD}",
                "呼吸音音量": f"RMS值应大于 {self.BREATH_RMS_THRESHOLD}",
                "信噪比": f"应大于 {self.SNR_THRESHOLD} dB",
                "频率特征": f"在{self.FREQ_RANGE[0]}-{self.FREQ_RANGE[1]} Hz范围内能量占比应大于50%"
            }
        } 