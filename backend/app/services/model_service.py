"""
模型服务
负责加载和使用语音诊断模型
"""

import os
import logging
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.utils.voice_models_utils import AnalysisModel

class VoiceModelService:
    """语音模型服务，负责加载和使用语音诊断模型"""
    
    def __init__(self):
        """初始化模型服务"""
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
        
        # 初始化模型
        model_path = os.path.join(project_root, 'ml_models', 'trained', 'voice_models', 'svm_model.pkl')
        self.model = AnalysisModel(model_path)
        logger.info("初始化语音模型服务")
        
    def analyze_voice(self, audio_path: str) -> Dict[str, Any]:
        """
        分析语音文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            分析结果，包含预测标签、置信度、特征和建议
        """
        try:
            # 使用模型进行预测
            prediction = self.model.get_pred(audio_path)
            
            # 获取特征
            features = self.model.get_features(audio_path)
    
            # 构建结果
            result = {
                "prediction": prediction,
                "confidence": 1.0,  # 由于新模型不支持概率预测，暂时设为1.0
                "status": "success",
                "features": {
                    "mfcc": features[20:40].tolist(),  # 假设MFCC特征在20-40位置
                    "chroma": features[0:12].tolist(),  # 假设色度特征在0-12位置
                    "zcr": float(features[12]),  # 假设ZCR在12位置
                    "rms": float(features[13]),  # 假设RMS在13位置
                    "mel": features[14:].tolist()  # 假设梅尔频谱在14之后
                }
            }
            
            # 添加建议
            result['suggestions'] = self._generate_suggestions(result['prediction'])
            
            return result
            
        except Exception as e:
            logger.error(f"语音分析失败: {str(e)}")
        return {
                "prediction": None,
                "confidence": None,
                "status": "error",
                "error": str(e),
                "suggestions": []
        }
    
    def _generate_suggestions(self, prediction: str) -> List[str]:
        """根据预测结果生成建议"""
        if prediction == "健康":
            return ["声音状态良好，继续保持良好的发声习惯"]
        else:
            return [
                "建议注意休息，避免声带过度使用",
                "保持充分的水分摄入",
                "避免在嘈杂环境中提高嗓音",
                "如症状持续，建议咨询专业医生"
            ] 