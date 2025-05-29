from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.db.models import User
from typing import Dict, Any, List
import logging

class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.logger = logging.getLogger(__name__)
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """创建新用户"""
        # 检查邮箱是否已存在
        if self.repository.get_by_email(user_data.email):
            raise HTTPException(
                status_code=400,
                detail="该邮箱已被注册"
            )
        
        # 检查用户名是否已存在
        if self.repository.get_by_username(user_data.username):
            raise HTTPException(
                status_code=400,
                detail="该用户名已被使用"
            )
        
        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        user = self.repository.create(user_data, hashed_password)
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active
        }
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """获取用户信息"""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active
        }
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """更新用户信息"""
        self.logger.error(f"[update_user] 进入方法 user_id={user_id}, user_data={user_data}")
        user = self.repository.get_by_id(user_id)
        if not user:
            self.logger.warning(f"[update_user] 用户不存在: user_id={user_id}")
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        update_data = user_data.dict(exclude_unset=True)
        self.logger.error(f"[update_user] update_data={update_data}")
        if "email" in update_data:
            exist = self.repository.get_by_email(update_data["email"])
            self.logger.info(f"[update_user] email check: exist={exist}")
            if exist and exist.id != user_id:
                self.logger.warning(f"[update_user] 邮箱已被注册: {update_data['email']}")
                raise HTTPException(status_code=400, detail="该邮箱已被注册")
        if "username" in update_data:
            exist = self.repository.get_by_username(update_data["username"])
            self.logger.info(f"[update_user] username check: exist={exist}")
            if exist and exist.id != user_id:
                self.logger.warning(f"[update_user] 用户名已被使用: {update_data['username']}")
                raise HTTPException(status_code=400, detail="该用户名已被使用")
        if "password" in update_data:
            self.logger.error("[update_user] 密码加密")
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        self.logger.error("[update_user] 调用repository.update")
        user = self.repository.update(user, update_data)
        self.logger.error(f"[update_user] 更新后用户: id={user.id}, email={user.email}, username={user.username}")
        return user
    
    async def delete_user(self, user_id: int) -> Dict[str, Any]:
        """删除用户"""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        
        self.repository.delete(user)
        return {"message": "用户已删除"}
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有用户"""
        users = self.repository.get_all(skip, limit)
        return [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active
            }
            for user in users
        ] 