from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.core.config import settings
from app.core.security import create_access_token, oauth2_scheme, get_current_user
from app.db.session import get_db
from app.db.models import User
from app.controllers.auth_controller import AuthController
from app.schemas.user import UserCreate, User
from app.schemas.token import Token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """用户登录"""
    controller = AuthController(db)
    return await controller.login(form_data.username, form_data.password)

@router.post("/register", response_model=User)
async def register(
    db: Session = Depends(get_db),
    user_in: UserCreate = None
):
    """用户注册"""
    controller = AuthController(db)
    return await controller.register(user_in)

@router.get("/me", response_model=User)
async def read_users_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    controller = AuthController(db)
    return await controller.get_current_user(current_user) 