from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VoiceMetricsBase(BaseModel):
    # 基础语音指标
    pitch_mean: float
    pitch_std: float
    intensity_mean: float
    intensity_std: float
    jitter: float
    shimmer: float
    hnr: float
    
    # 语音质量指标
    voice_quality_score: float
    clarity_score: float
    stability_score: float
    
    # 呼吸相关指标
    breathing_rate: float
    pause_ratio: float
    speech_rate: float

class VoiceMetricsCreate(VoiceMetricsBase):
    diagnosis_id: int

class VoiceMetricsUpdate(BaseModel):
    # 所有字段都是可选的
    pitch_mean: Optional[float] = None
    pitch_std: Optional[float] = None
    intensity_mean: Optional[float] = None
    intensity_std: Optional[float] = None
    jitter: Optional[float] = None
    shimmer: Optional[float] = None
    hnr: Optional[float] = None
    voice_quality_score: Optional[float] = None
    clarity_score: Optional[float] = None
    stability_score: Optional[float] = None
    breathing_rate: Optional[float] = None
    pause_ratio: Optional[float] = None
    speech_rate: Optional[float] = None

class VoiceMetrics(VoiceMetricsBase):
    id: int
    diagnosis_id: int
    created_at: datetime

    class Config:
        from_attributes = True 