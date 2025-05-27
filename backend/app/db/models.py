from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 关联诊断会话
    diagnosis_sessions = relationship("DiagnosisSession", back_populates="user")
    voice_metrics = relationship("VoiceMetrics", back_populates="user")


class VoiceMetrics(Base):
    __tablename__ = "voice_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("diagnosis_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # MFCC特征
    # 13维梅尔频率倒谱系数
    mfcc_1 = Column(Float)
    mfcc_2 = Column(Float)
    mfcc_3 = Column(Float)
    mfcc_4 = Column(Float)
    mfcc_5 = Column(Float)
    mfcc_6 = Column(Float)
    mfcc_7 = Column(Float)
    mfcc_8 = Column(Float)
    mfcc_9 = Column(Float)
    mfcc_10 = Column(Float)
    mfcc_11 = Column(Float)
    mfcc_12 = Column(Float)
    mfcc_13 = Column(Float)
    
    # 色度特征
    # 12维色谱特征
    chroma_1 = Column(Float)
    chroma_2 = Column(Float)
    chroma_3 = Column(Float)
    chroma_4 = Column(Float)
    chroma_5 = Column(Float)
    chroma_6 = Column(Float)
    chroma_7 = Column(Float)
    chroma_8 = Column(Float)
    chroma_9 = Column(Float)
    chroma_10 = Column(Float)
    chroma_11 = Column(Float)
    chroma_12 = Column(Float)
    
    # 时域特征
    rms = Column(Float)  # 均方根能量（音量）
    zcr = Column(Float)  # 过零率
    
    # 梅尔频谱特征
    mel_spectrogram = Column(Text)  # 梅尔频谱，存储为JSON字符串
    
    # AI模型预测结果
    model_prediction = Column(String(50))  # 预测的疾病类型
    model_confidence = Column(Float)  # 预测的置信度
    
    created_at = Column(DateTime, default=datetime.utcnow)


    # 关系
    session = relationship("DiagnosisSession", back_populates="voice_metrics")
    user = relationship("User", back_populates="voice_metrics")

class DiagnosisSession(Base):
    __tablename__ = "diagnosis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # 新增字段
    analysis_progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    
    # LLM诊断建议
    diagnosis_suggestion = Column(Text, nullable=True)  # LLM生成的诊断建议
    follow_up_questions = Column(Text, nullable=True)  # 后续问题
    conversation_history = Column(Text, nullable=True)  # 对话历史，存储为JSON字符串
    
    # 关系
    user = relationship("User", back_populates="diagnosis_sessions")
    voice_metrics = relationship("VoiceMetrics", back_populates="session")