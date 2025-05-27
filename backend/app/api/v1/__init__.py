"""
API v1版本
包含v1版本的所有API端点
"""
from fastapi import APIRouter
from app.api.v1.endpoints import diagnosis, websocket

api_router = APIRouter()
api_router.include_router(diagnosis.router, prefix="/diagnosis", tags=["diagnosis"])
api_router.include_router(websocket.router, tags=["websocket"])