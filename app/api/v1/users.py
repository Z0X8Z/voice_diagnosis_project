# app/main.py 或 app/api/v1/users.py 中
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.db.orm_models import User

# 确保第一次启动时创建表
Base.metadata.create_all(bind=engine)

# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
