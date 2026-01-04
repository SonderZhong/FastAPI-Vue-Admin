# _*_ coding : UTF-8 _*_
# @Time : 2025/12/28
# @Author : sonder
# @File : notification.py
# @Comment : 通知工具类 - WebSocket 管理和 Redis 操作

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from redis.asyncio import Redis as AsyncRedis

from utils.log import logger
from utils.get_redis import RedisKeyConfig
from models import SystemNotification, UserNotification
from models.notification import NotificationType, NotificationStatus


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """建立连接"""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        logger.info(f"WebSocket 连接建立: user_id={user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """断开连接"""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WebSocket 连接断开: user_id={user_id}")
    
    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """发送消息给指定用户"""
        if user_id not in self._connections:
            return False
        
        disconnected = set()
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"发送消息失败: {e}")
                disconnected.add(ws)
        
        # 清理断开的连接
        for ws in disconnected:
            self._connections[user_id].discard(ws)
        
        return True
    
    async def send_to_users(self, user_ids: List[str], message: dict):
        """发送消息给多个用户"""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)
    
    async def broadcast(self, message: dict):
        """广播消息给所有在线用户"""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)
    
    def get_online_users(self) -> List[str]:
        """获取所有在线用户ID"""
        return list(self._connections.keys())
    
    def is_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self._connections and len(self._connections[user_id]) > 0


# 全局连接管理器实例
ws_manager = ConnectionManager()


class NotificationService:
    """通知服务"""
    
    # Redis key 前缀
    NOTIFICATION_KEY = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:notification"
    UNREAD_COUNT_KEY = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:unread_count"
    
    def __init__(self, redis: AsyncRedis):
        self._redis = redis
    
    async def push_notification(
        self,
        notification_id: str,
        title: str,
        content: str,
        notification_type: int,
        priority: int,
        target_user_ids: List[str],
        creator_name: str = "系统"
    ):
        """
        推送通知
        - 通过 WebSocket 实时推送给在线用户
        - 存储到 Redis 供离线用户获取
        """
        message = {
            "type": "notification",
            "data": {
                "id": notification_id,
                "title": title,
                "content": content[:200],  # 预览内容
                "notification_type": notification_type,
                "priority": priority,
                "creator_name": creator_name,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # 推送给在线用户
        online_users = []
        offline_users = []
        
        for user_id in target_user_ids:
            if ws_manager.is_online(user_id):
                online_users.append(user_id)
            else:
                offline_users.append(user_id)
        
        # WebSocket 推送
        if online_users:
            await ws_manager.send_to_users(online_users, message)
            logger.info(f"通知已推送给 {len(online_users)} 个在线用户")
        
        # 更新所有目标用户的未读计数
        for user_id in target_user_ids:
            await self.increment_unread_count(user_id)
        
        # 存储通知到 Redis（用于离线用户获取）
        await self._store_notification_to_redis(notification_id, message, target_user_ids)
        
        return {
            "online_count": len(online_users),
            "offline_count": len(offline_users)
        }
    
    async def _store_notification_to_redis(
        self,
        notification_id: str,
        message: dict,
        target_user_ids: List[str]
    ):
        """存储通知到 Redis"""
        # 存储通知内容（24小时过期）
        key = f"{self.NOTIFICATION_KEY}:{notification_id}"
        await self._redis.setex(
            key,
            timedelta(hours=24),
            json.dumps(message, ensure_ascii=False)
        )
        
        # 为每个用户添加待推送通知ID
        for user_id in target_user_ids:
            user_key = f"{self.NOTIFICATION_KEY}:pending:{user_id}"
            await self._redis.sadd(user_key, notification_id)
            await self._redis.expire(user_key, timedelta(hours=24))
    
    async def get_pending_notifications(self, user_id: str) -> List[dict]:
        """获取用户的待推送通知（用于 HTTP 轮询）"""
        user_key = f"{self.NOTIFICATION_KEY}:pending:{user_id}"
        notification_ids = await self._redis.smembers(user_key)
        
        notifications = []
        for nid in notification_ids:
            key = f"{self.NOTIFICATION_KEY}:{nid}"
            data = await self._redis.get(key)
            if data:
                notifications.append(json.loads(data))
        
        # 清除已获取的通知
        if notification_ids:
            await self._redis.delete(user_key)
        
        return notifications
    
    async def increment_unread_count(self, user_id: str):
        """增加用户未读计数"""
        key = f"{self.UNREAD_COUNT_KEY}:{user_id}"
        await self._redis.incr(key)
    
    async def get_unread_count(self, user_id: str) -> int:
        """获取用户未读计数"""
        key = f"{self.UNREAD_COUNT_KEY}:{user_id}"
        count = await self._redis.get(key)
        return int(count) if count else 0
    
    async def reset_unread_count(self, user_id: str):
        """重置用户未读计数"""
        key = f"{self.UNREAD_COUNT_KEY}:{user_id}"
        await self._redis.delete(key)
    
    async def decrement_unread_count(self, user_id: str, count: int = 1):
        """减少用户未读计数"""
        key = f"{self.UNREAD_COUNT_KEY}:{user_id}"
        current = await self.get_unread_count(user_id)
        new_count = max(0, current - count)
        if new_count > 0:
            await self._redis.set(key, new_count)
        else:
            await self._redis.delete(key)
    
    async def send_login_notification(
        self,
        user_id: str,
        username: str,
        login_ip: str,
        login_location: str,
        browser: str,
        os: str
    ):
        """发送登录通知 - 创建数据库记录并推送"""
        # 创建登录通知记录
        notification = await SystemNotification.create(
            title="登录提醒",
            content=f"您的账号于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 在 {login_location} 登录\n\nIP地址: {login_ip}\n浏览器: {browser}\n操作系统: {os}",
            type=NotificationType.LOGIN,
            scope=2,  # 指定用户
            scope_ids=[user_id],
            status=NotificationStatus.PUBLISHED,
            priority=0,
            publish_time=datetime.now(),
            creator_id=None  # 系统通知
        )
        
        # 创建用户通知关联
        await UserNotification.create(
            notification_id=notification.id,
            user_id=user_id
        )
        
        # 增加未读计数
        await self.increment_unread_count(user_id)
        
        # 通过 WebSocket 推送（如果用户在线）
        message = {
            "type": "login_notification",
            "data": {
                "id": str(notification.id),
                "title": "登录提醒",
                "content": f"您的账号于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 在 {login_location} 登录",
                "details": {
                    "ip": login_ip,
                    "location": login_location,
                    "browser": browser,
                    "os": os,
                    "time": datetime.now().isoformat()
                }
            }
        }
        
        if ws_manager.is_online(user_id):
            await ws_manager.send_to_user(user_id, message)
            logger.info(f"登录通知已推送给用户: {user_id}")
    
    async def get_login_notification(self, user_id: str) -> Optional[dict]:
        """获取登录通知"""
        key = f"{self.NOTIFICATION_KEY}:login:{user_id}"
        data = await self._redis.get(key)
        if data:
            await self._redis.delete(key)
            return json.loads(data)
        return None
