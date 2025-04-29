# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建引擎，pool_pre_ping=True 可以自动检测断开的连接
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,          # SQLAlchemy 2.0 风格（可选）
)

# SessionLocal 用来在请求里创建、关闭 session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
