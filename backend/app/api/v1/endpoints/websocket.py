from fastapi import APIRouter, WebSocket, Depends
from app.websockets.manager import WebSocketManager
from app.core.auth import get_current_user
from app.db.session import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
websocket_manager = WebSocketManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket连接端点"""
    try:
        # 验证用户身份
        current_user = await get_current_user(db, user_id)
        if not current_user:
            await websocket.close(code=4001, reason="未授权的访问")
            return
        
        # 建立WebSocket连接
        await websocket_manager.connect(websocket, user_id)
        
        try:
            # 保持连接活跃
            while True:
                data = await websocket.receive_text()
                # 这里可以处理来自客户端的消息
                logger.info(f"收到来自用户 {user_id} 的消息: {data}")
        except Exception as e:
            logger.error(f"WebSocket连接异常: {str(e)}")
        finally:
            # 断开连接
            websocket_manager.disconnect(user_id)
            
    except Exception as e:
        logger.error(f"WebSocket连接失败: {str(e)}")
        await websocket.close(code=4000, reason="连接失败") 