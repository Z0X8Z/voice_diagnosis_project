from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,  # 连接在池中回收前的秒数
    pool_size=5,  # 连接池大小
    max_overflow=10  # 连接池溢出时允许创建的最大连接数
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 依赖函数，用于处理数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()