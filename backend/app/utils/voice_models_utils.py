import os
import librosa
import numpy as np
import joblib
import warnings
import logging
from pathlib import Path

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

MODEL_INSTANCE = None

class AnalysisModel:
    def __init__(self, model_path):
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            
            # 构建完整的模型文件路径
            model_file = os.path.join(project_root, 'ml_models', 'trained', 'voice_models', 'svm_model.pkl')
            
            logger.info(f"尝试加载模型文件: {model_file}")
            if not os.path.exists(model_file):
                raise FileNotFoundError(f"模型文件不存在: {model_file}")
            
            self.model_svm_loaded = joblib.load(model_file)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise

    def extract_features(self, data):
        # ZCR
        result = np.array([])
        zcr = np.mean(librosa.feature.zero_crossing_rate(data).T, axis=0)
        result = np.hstack((result, zcr)) # stacking horizontally
        
        # Chroma_stft
        stft = np.abs(librosa.stft(data))
        chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft).T, axis=0)
        result = np.hstack((result, chroma_stft)) # stacking horizontally
        
        # MFCC
        mfcc = np.mean(librosa.feature.mfcc(y=data).T, axis=0)
        result = np.hstack((result, mfcc)) # stacking horizontally
        
        # Root Mean Square Value
        rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
        result = np.hstack((result, rms)) # stacking horizontally
        
        # MelSpectogram
        mel = np.mean(librosa.feature.melspectrogram(y=data).T, axis=0)
        result = np.hstack((result, mel)) # stacking horizontally
        
        return result

    def get_features(self, path):
        # duration and offset are used to take care of the no audio in start and the ending of each audio files as seen above.
        data, sample_rate = librosa.load(path, duration=2.5, offset=0.6)
        
        # without augmentation
        res1 = self.extract_features(data)
        result = np.array(res1)
        
        return result

    def get_pred(self, audio_path):
        X = []
        audio_feature = self.get_features(audio_path)
        X.append(audio_feature)
        logger.info(f"处理音频文件: {audio_path}")
        result = self.model_svm_loaded.predict(X)[0]
        return result

def create_model() -> AnalysisModel:
    """
    创建并返回模型实例（全局只加载一次）
    Returns:
        AnalysisModel实例
    """
    global MODEL_INSTANCE
    if MODEL_INSTANCE is None:
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
        # 构建模型文件路径
        model_path = os.path.join(project_root, 'ml_models', 'trained', 'voice_models', 'svm_model.pkl')
        MODEL_INSTANCE = AnalysisModel(model_path)
    return MODEL_INSTANCE