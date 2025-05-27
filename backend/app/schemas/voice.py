from typing import List, Dict, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

class VoiceHistoryRecord(BaseModel):
    """语音分析历史记录"""
    id: int
    session_id: Optional[int] = 0
    created_at: datetime
    prediction: str = ""
    confidence: float = 0.0
    llm_suggestion: Optional[str] = None
    llm_processed_at: Optional[datetime] = None

class VoiceHistoryResponse(BaseModel):
    """语音历史记录响应"""
    total: int
    page: int
    size: int
    records: List[VoiceHistoryRecord]

class VoiceStatsResponse(BaseModel):
    """语音统计数据响应"""
    total_analyses: int = Field(default=0)
    recent_analyses: int = Field(default=0)
    prediction_distribution: Dict[str, int] = Field(default_factory=dict)
    average_confidence: float = Field(default=0.0) 