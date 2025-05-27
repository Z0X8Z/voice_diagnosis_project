from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
import logging

logger = logging.getLogger(__name__)

async def get_current_user(db: Session, user_id: int) -> User:
    """
    获取当前用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        User: 用户对象
        
    Raises:
        HTTPException: 如果用户不存在
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"用户 {user_id} 不存在")
            return None
        return user
    except Exception as e:
        logger.error(f"获取用户 {user_id} 失败: {str(e)}")
        return None 