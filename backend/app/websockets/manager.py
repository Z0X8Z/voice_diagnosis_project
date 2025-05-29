from fastapi import WebSocket
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # 存储所有活跃的WebSocket连接
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """建立WebSocket连接"""
        await websocket.accept()
        # 确保user_id是整数类型
        user_id = int(user_id)
        self.active_connections[user_id] = websocket
        logger.info(f"用户 {user_id} 已连接，当前连接数: {len(self.active_connections)}")
        logger.debug(f"当前活跃连接: {list(self.active_connections.keys())}")
    
    def disconnect(self, user_id: int):
        """断开WebSocket连接"""
        # 确保user_id是整数类型
        user_id = int(user_id)
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"用户 {user_id} 已断开连接，当前连接数: {len(self.active_connections)}")
            logger.debug(f"当前活跃连接: {list(self.active_connections.keys())}")
        else:
            logger.warning(f"尝试断开不存在的连接: user_id={user_id}")
    
    async def send_message(self, user_id: int, message: str):
        """向指定用户发送消息"""
        # 确保user_id是整数类型
        user_id = int(user_id)
        logger.info(f"尝试发送消息给用户 {user_id}，当前活跃连接: {list(self.active_connections.keys())}")
        
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
                logger.info(f"消息已发送给用户 {user_id}")
            except Exception as e:
                logger.error(f"发送消息给用户 {user_id} 失败: {str(e)}")
                self.disconnect(user_id)
        else:
            logger.warning(f"用户 {user_id} 未连接")
    
    async def broadcast(self, message: str):
        """向所有连接的客户端广播消息"""
        logger.info(f"广播消息给 {len(self.active_connections)} 个连接")
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
                logger.info(f"广播消息已发送给用户 {user_id}")
            except Exception as e:
                logger.error(f"广播消息给用户 {user_id} 失败: {str(e)}")
                self.disconnect(user_id)

# 全局唯一WebSocketManager实例
websocket_manager = WebSocketManager() 