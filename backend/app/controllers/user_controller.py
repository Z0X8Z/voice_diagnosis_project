from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from app.db.models import User

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
):
    """创建新用户"""
    user_service = UserService(db)
    return await user_service.create_user(user_in)

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户信息"""
    user_service = UserService(db)
    return await user_service.get_user(user_id)

@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate
):
    """更新用户信息"""
    user_service = UserService(db)
    return await user_service.update_user(user_id, user_in)

@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int
):
    """删除用户"""
    user_service = UserService(db)
    return await user_service.delete_user(user_id)

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取所有用户"""
    user_service = UserService(db)
    return await user_service.get_all_users(skip, limit)

class UserController:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[User]:
        """获取单个用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """获取用户列表"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def create_user(self, user_in: UserCreate) -> User:
        """创建新用户"""
        db_user = User(
            email=user_in.email,
            hashed_password=user_in.password,  # 注意：实际使用时需要加密
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(
        self,
        user_id: int,
        user_in: UserUpdate
    ) -> Optional[User]:
        """更新用户信息"""
        user = self.get_user(user_id)
        if not user:
            return None

        update_data = user_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get_user(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def get_user_stats(self, user_id: int) -> dict:
        """获取用户统计数据"""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # 这里可以添加更多统计数据的计算
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login
        } 