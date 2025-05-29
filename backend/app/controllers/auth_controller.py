from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
from app.core.config import settings
from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.token import Token

# 配置日志记录器
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthController:
    def __init__(self, db: Session):
        self.db = db

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, user_in: UserCreate) -> User:
        try:
            db_user = User(
                email=user_in.email,
                username=user_in.username,
                hashed_password=self.get_password_hash(user_in.password)
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Email or username already registered"
            )

    def update_user(self, user_id: int, user_in: UserUpdate) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        update_data = user_in.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = self.get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    async def login(
        self,
        username: str,
        password: str
    ) -> Token:
        """处理用户登录"""
        try:
            logger.info(f"尝试登录用户: {username}")
            
            # 先尝试用用户名查找
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                # 如果用户名没找到，尝试用邮箱查找
                user = self.db.query(User).filter(User.email == username).first()
            
            if not user:
                logger.warning(f"用户不存在: {username}")
                raise HTTPException(
                    status_code=401,
                    detail="用户名或密码错误"
                )
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"密码错误: {username}")
                raise HTTPException(
                    status_code=401,
                    detail="用户名或密码错误"
                )
            
            logger.info(f"用户登录成功: {username}")
            access_token = self.create_access_token(data={"sub": user.email})
            refresh_token = self.create_access_token(data={"sub": user.email}, expires_delta=timedelta(days=7))
            return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"登录过程发生错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"登录失败: {str(e)}"
            )

    async def get_current_user(
        self,
        current_user: User
    ) -> Dict[str, Any]:
        """获取当前用户信息"""
        try:
            return {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    async def register(
        self,
        user_in: UserCreate
    ) -> Dict[str, Any]:
        """注册新用户"""
        try:
            logger.info(f"尝试注册新用户: {user_in.email}")
            
            # 检查邮箱是否已注册
            user = self.get_user_by_email(user_in.email)
            if user:
                logger.warning(f"邮箱已被注册: {user_in.email}")
                raise HTTPException(
                    status_code=400,
                    detail="该邮箱已被注册"
                )
            
            # 检查用户名是否已被使用
            user = self.db.query(User).filter(User.username == user_in.username).first()
            if user:
                logger.warning(f"用户名已被使用: {user_in.username}")
                raise HTTPException(
                    status_code=400,
                    detail="该用户名已被使用"
                )
            
            # 创建新用户
            user = self.create_user(user_in)
            logger.info(f"新用户注册成功: {user.email}")
            
            # 返回符合schemas.User模式的字典
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"注册失败: {str(e)}"
            ) 