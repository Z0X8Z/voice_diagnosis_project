from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.controllers.user_controller import UserController
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
async def get_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    controller = UserController(db)
    return controller.get_users(skip, limit)

@router.post("/", response_model=UserSchema)
async def create_user(
    db: Session = Depends(get_db),
    user_in: UserCreate = None,
    current_user: User = Depends(get_current_user)
):
    """创建新用户"""
    controller = UserController(db)
    return controller.create_user(user_in)

@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个用户"""
    controller = UserController(db)
    user = controller.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    controller = UserController(db)
    user = controller.update_user(user_id, user_in)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户"""
    controller = UserController(db)
    if not controller.delete_user(user_id):
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return {"status": "success"}

@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户统计数据"""
    controller = UserController(db)
    return controller.get_user_stats(user_id) 