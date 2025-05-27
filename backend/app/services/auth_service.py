from datetime import timedelta
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging

from app.repositories.auth_repository import AuthRepository
from app.core.security import create_access_token, verify_password
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.repository = AuthRepository(db)
    
    async def login(self, username: str, password: str) -> Token:
        """处理用户登录"""
        try:
            logger.info(f"尝试登录用户: {username}")
            
            # 先尝试用用户名查找
            user = self.repository.get_user_by_username(username)
            if not user:
                # 如果用户名没找到，尝试用邮箱查找
                user = self.repository.get_user_by_email(username)
            
            if not user:
                logger.warning(f"用户不存在: {username}")
                raise HTTPException(
                    status_code=401,
                    detail="用户名或密码错误"
                )
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"密码错误: {username}")
                raise HTTPException(
                    status_code=401,
                    detail="用户名或密码错误"
                )
            
            logger.info(f"用户登录成功: {username}")
            access_token = create_access_token(data={"sub": user.email})
            return Token(access_token=access_token, token_type="bearer")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"登录过程发生错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"登录失败: {str(e)}"
            )
    
    async def get_current_user(self, current_user: User) -> Dict[str, Any]:
        """获取当前用户信息"""
        try:
            return {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username,
                "is_active": current_user.is_active,
                "is_superuser": current_user.is_superuser
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    async def register(self, user_in: UserCreate) -> User:
        """注册新用户"""
        try:
            logger.info(f"尝试注册新用户: {user_in.email}")
            
            # 检查邮箱是否已注册
            if self.repository.get_user_by_email(user_in.email):
                logger.warning(f"邮箱已被注册: {user_in.email}")
                raise HTTPException(
                    status_code=400,
                    detail="该邮箱已被注册"
                )
            
            # 检查用户名是否已被使用
            if self.repository.get_user_by_username(user_in.username):
                logger.warning(f"用户名已被使用: {user_in.username}")
                raise HTTPException(
                    status_code=400,
                    detail="该用户名已被使用"
                )
            
            # 创建新用户
            user = self.repository.create_user(user_in)
            logger.info(f"新用户注册成功: {user.email}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"注册失败: {str(e)}"
            ) 