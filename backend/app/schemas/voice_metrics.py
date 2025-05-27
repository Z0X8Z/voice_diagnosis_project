from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class VoiceMetricsBase(BaseModel):
    # MFCC及其动态特征
    mfcc_1: float
    mfcc_2: float
    mfcc_3: float
    mfcc_4: float
    mfcc_5: float
    mfcc_6: float
    mfcc_7: float
    mfcc_8: float
    mfcc_9: float
    mfcc_10: float
    mfcc_11: float
    mfcc_12: float
    mfcc_13: float
    
    # MFCC的一阶差分（Δ）
    delta_1: float
    delta_2: float
    delta_3: float
    delta_4: float
    delta_5: float
    delta_6: float
    delta_7: float
    delta_8: float
    delta_9: float
    delta_10: float
    delta_11: float
    delta_12: float
    delta_13: float
    
    # MFCC的二阶差分（ΔΔ）
    delta2_1: float
    delta2_2: float
    delta2_3: float
    delta2_4: float
    delta2_5: float
    delta2_6: float
    delta2_7: float
    delta2_8: float
    delta2_9: float
    delta2_10: float
    delta2_11: float
    delta2_12: float
    delta2_13: float
    
    # 色度特征
    chroma_1: float
    chroma_2: float
    chroma_3: float
    chroma_4: float
    chroma_5: float
    chroma_6: float
    chroma_7: float
    chroma_8: float
    chroma_9: float
    chroma_10: float
    chroma_11: float
    chroma_12: float
    
    # 梅尔频谱特征
    log_mel: str  # JSON字符串
    
    # 频谱对比度
    contrast: float
    
    # 调性特征
    tonnetz_1: float
    tonnetz_2: float
    tonnetz_3: float
    tonnetz_4: float
    tonnetz_5: float
    tonnetz_6: float
    
    # 时域特征
    rms: float  # 均方根能量（音量）
    zcr: float  # 过零率
    
    # 频谱形状特征
    bandwidth: float  # 频谱带宽
    centroid: float  # 频谱质心
    rolloff: float  # 频谱滚降点
    
    # AI模型预测结果
    model_prediction: str
    model_confidence: float

class VoiceMetricsCreate(VoiceMetricsBase):
    session_id: int
    voice_file_path: str

class VoiceMetricsUpdate(BaseModel):
    # 所有字段都是可选的
    # MFCC及其动态特征
    mfcc_1: Optional[float] = None
    mfcc_2: Optional[float] = None
    mfcc_3: Optional[float] = None
    mfcc_4: Optional[float] = None
    mfcc_5: Optional[float] = None
    mfcc_6: Optional[float] = None
    mfcc_7: Optional[float] = None
    mfcc_8: Optional[float] = None
    mfcc_9: Optional[float] = None
    mfcc_10: Optional[float] = None
    mfcc_11: Optional[float] = None
    mfcc_12: Optional[float] = None
    mfcc_13: Optional[float] = None
    
    # MFCC的一阶差分（Δ）
    delta_1: Optional[float] = None
    delta_2: Optional[float] = None
    delta_3: Optional[float] = None
    delta_4: Optional[float] = None
    delta_5: Optional[float] = None
    delta_6: Optional[float] = None
    delta_7: Optional[float] = None
    delta_8: Optional[float] = None
    delta_9: Optional[float] = None
    delta_10: Optional[float] = None
    delta_11: Optional[float] = None
    delta_12: Optional[float] = None
    delta_13: Optional[float] = None
    
    # MFCC的二阶差分（ΔΔ）
    delta2_1: Optional[float] = None
    delta2_2: Optional[float] = None
    delta2_3: Optional[float] = None
    delta2_4: Optional[float] = None
    delta2_5: Optional[float] = None
    delta2_6: Optional[float] = None
    delta2_7: Optional[float] = None
    delta2_8: Optional[float] = None
    delta2_9: Optional[float] = None
    delta2_10: Optional[float] = None
    delta2_11: Optional[float] = None
    delta2_12: Optional[float] = None
    delta2_13: Optional[float] = None
    
    # 色度特征
    chroma_1: Optional[float] = None
    chroma_2: Optional[float] = None
    chroma_3: Optional[float] = None
    chroma_4: Optional[float] = None
    chroma_5: Optional[float] = None
    chroma_6: Optional[float] = None
    chroma_7: Optional[float] = None
    chroma_8: Optional[float] = None
    chroma_9: Optional[float] = None
    chroma_10: Optional[float] = None
    chroma_11: Optional[float] = None
    chroma_12: Optional[float] = None
    
    # 梅尔频谱特征
    log_mel: Optional[str] = None
    
    # 频谱对比度
    contrast: Optional[float] = None
    
    # 调性特征
    tonnetz_1: Optional[float] = None
    tonnetz_2: Optional[float] = None
    tonnetz_3: Optional[float] = None
    tonnetz_4: Optional[float] = None
    tonnetz_5: Optional[float] = None
    tonnetz_6: Optional[float] = None
    
    # 时域特征
    rms: Optional[float] = None
    zcr: Optional[float] = None
    
    # 频谱形状特征
    bandwidth: Optional[float] = None
    centroid: Optional[float] = None
    rolloff: Optional[float] = None
    
    # AI模型预测结果
    model_prediction: Optional[str] = None
    model_confidence: Optional[float] = None

class VoiceMetrics(VoiceMetricsBase):
    id: int
    session_id: int
    voice_file_path: str
    created_at: datetime

    class Config:
        from_attributes = True 