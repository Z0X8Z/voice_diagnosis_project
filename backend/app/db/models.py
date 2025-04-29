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