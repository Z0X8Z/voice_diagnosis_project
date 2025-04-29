from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联诊断记录
    diagnoses = relationship("Diagnosis", back_populates="user")

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    voice_file_path = Column(String(200))  # 语音文件存储路径
    model_result = Column(Text)  # 模型诊断结果
    llm_analysis = Column(Text)  # 大模型分析结果
    confidence_score = Column(Float)  # 置信度分数
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联用户
    user = relationship("User", back_populates="diagnoses")
    # 关联语音指标
    voice_metrics = relationship("VoiceMetrics", back_populates="diagnosis", uselist=False)

class VoiceMetrics(Base):
    __tablename__ = "voice_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.id"), unique=True)
    
    # 基础语音指标
    pitch_mean = Column(Float)  # 平均音高
    pitch_std = Column(Float)   # 音高标准差
    intensity_mean = Column(Float)  # 平均强度
    intensity_std = Column(Float)   # 强度标准差
    jitter = Column(Float)  # 频率微扰
    shimmer = Column(Float)  # 振幅微扰
    hnr = Column(Float)  # 谐噪比
    
    # 语音质量指标
    voice_quality_score = Column(Float)  # 语音质量总分
    clarity_score = Column(Float)  # 清晰度得分
    stability_score = Column(Float)  # 稳定性得分
    
    # 呼吸相关指标
    breathing_rate = Column(Float)  # 呼吸频率
    pause_ratio = Column(Float)  # 停顿比例
    speech_rate = Column(Float)  # 语速
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联诊断记录
    diagnosis = relationship("Diagnosis", back_populates="voice_metrics")