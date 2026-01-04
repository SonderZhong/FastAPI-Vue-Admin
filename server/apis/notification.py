# _*_ coding : UTF-8 _*_
# @Time : 2025/12/28
# @Author : sonder
# @File : notification.py
# @Comment : 通知管理 API

import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Path, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from tortoise.models import Q

from annotation.auth import AuthController, Auth
from annotation.log import Log, OperationType
from models import SystemNotification, UserNotification, SystemUser
from models.notification import NotificationType, NotificationScope, NotificationStatus
from utils.casbin import DepartmentHelper
from utils.notification import ws_manager, NotificationService
from utils.response import ResponseUtil

notificationAPI = APIRouter(prefix="/notification")

# WebSocket 路由（不需要认证依赖，在内部处理）
notificationWsAPI = APIRouter(prefix="/notification")


# ==================== 请求参数模型 ====================

class CreateNotificationParams(BaseModel):
    """创建通知参数"""
    title: str
    content: str
    type: int = NotificationType.MESSAGE
    scope: int = NotificationScope.ALL
    scope_ids: List[str] = []
    priority: int = 0
    expire_time: Optional[str] = None


class UpdateNotificationParams(BaseModel):
    """更新通知参数"""
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[int] = None
    scope: Optional[int] = None
    scope_ids: Optional[List[str]] = None
    priority: Optional[int] = None
    expire_time: Optional[str] = None


# ==================== WebSocket 端点 ====================

@notificationWsAPI.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket 连接端点"""
    user_id = None
    try:
        # 验证 token 获取用户信息
        from jose import jwt
        from utils.config import config
        from utils.get_redis import RedisKeyConfig
        
        payload = jwt.decode(
            token=token,
            key=config.jwt().secret_key,
            algorithms=[config.jwt().algorithm],
        )
        user_id = payload.get("id")
        session_id = payload.get("session_id")
        
        if not user_id:
            await websocket.close(code=4001, reason="无效的 token")
            return
        
        # 验证 session 是否有效
        redis = websocket.app.state.redis
        redis_token = await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}")
        if not redis_token:
            await websocket.close(code=4001, reason="会话已过期")
            return
        
        await ws_manager.connect(websocket, user_id)
        
        # 获取通知服务
        notification_service = NotificationService(redis)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "WebSocket 连接成功"}
        })
        
        # 发送待推送的通知
        pending = await notification_service.get_pending_notifications(user_id)
        if pending:
            for notification in pending:
                await websocket.send_json(notification)
        
        # 从数据库查询实际未读数量
        unread_count = await UserNotification.filter(
            user_id=user_id,
            is_read=False,
            notification__is_del=False,
            notification__status=NotificationStatus.PUBLISHED
        ).count()
        
        await websocket.send_json({
            "type": "unread_count",
            "data": {"count": unread_count}
        })
        
        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 处理心跳
            if data == "ping":
                await websocket.send_text("pong")
                continue
            
            # 处理请求-响应模式
            try:
                message = json.loads(data)
                if message.get("type") == "request":
                    await handle_ws_request(websocket, message, user_id, redis)
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        if user_id:
            ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        if user_id:
            ws_manager.disconnect(websocket, user_id)
        try:
            await websocket.close(code=4001, reason=str(e))
        except:
            pass


async def handle_ws_request(websocket: WebSocket, message: dict, user_id: str, redis):
    """处理 WebSocket 请求"""
    import json
    from utils.get_redis import RedisKeyConfig
    
    action = message.get("action")
    request_id = message.get("requestId")
    
    if not action or not request_id:
        return
    
    try:
        if action == "getUserInfo":
            # 从 Redis 获取用户信息
            user_info_str = await redis.get(f"{RedisKeyConfig.USER_INFO.key}:{user_id}")
            if user_info_str:
                user_info = json.loads(user_info_str)
                await websocket.send_json({
                    "type": "response",
                    "requestId": request_id,
                    "data": user_info
                })
            else:
                await websocket.send_json({
                    "type": "response",
                    "requestId": request_id,
                    "data": {"success": False, "msg": "用户信息不存在"}
                })
        
        elif action == "getUserRoutes":
            # 从 Redis 获取用户路由
            routes_str = await redis.get(f"{RedisKeyConfig.USER_ROUTES.key}:{user_id}")
            if routes_str:
                routes = json.loads(routes_str)
                await websocket.send_json({
                    "type": "response",
                    "requestId": request_id,
                    "data": routes
                })
            else:
                # 路由缓存不存在，返回空让前端回退到 HTTP
                await websocket.send_json({
                    "type": "response",
                    "requestId": request_id,
                    "data": {"success": False, "msg": "路由缓存不存在"}
                })
        
        else:
            await websocket.send_json({
                "type": "response",
                "requestId": request_id,
                "data": {"success": False, "msg": f"未知操作: {action}"}
            })
    
    except Exception as e:
        await websocket.send_json({
            "type": "response",
            "requestId": request_id,
            "data": {"success": False, "msg": str(e)}
        })


# ==================== 通知管理 API ====================

@notificationAPI.post("/create", response_class=JSONResponse, summary="创建通知")
@Log(title="创建通知", operation_type=OperationType.INSERT)
@Auth(permission_list=["notification:btn:add", "POST:/notification/create"])
async def create_notification(
    request: Request,
    params: CreateNotificationParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """创建通知（草稿状态）"""
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    sub_departments = current_user.get("sub_departments", [])
    
    # 权限检查
    if user_type == 3:
        return ResponseUtil.error(msg="普通用户无权创建通知")
    
    # 部门管理员只能创建部门范围的通知
    if user_type == 2:
        if params.scope == NotificationScope.ALL:
            return ResponseUtil.error(msg="部门管理员无权创建全局通知")
        if params.scope == NotificationScope.DEPARTMENT:
            # 检查目标部门是否在可管理范围内
            for dept_id in params.scope_ids:
                if dept_id not in sub_departments:
                    return ResponseUtil.error(msg="无权向该部门发送通知")
    
    # 解析过期时间
    expire_time = None
    if params.expire_time:
        try:
            expire_time = datetime.fromisoformat(params.expire_time.replace("Z", "+00:00"))
        except:
            pass
    
    notification = await SystemNotification.create(
        title=params.title,
        content=params.content,
        type=params.type,
        scope=params.scope,
        scope_ids=params.scope_ids,
        priority=params.priority,
        expire_time=expire_time,
        status=NotificationStatus.DRAFT,
        creator_id=user_id
    )
    
    return ResponseUtil.success(msg="创建成功", data={"id": str(notification.id)})


@notificationAPI.put("/update/{id}", response_class=JSONResponse, summary="更新通知")
@Log(title="更新通知", operation_type=OperationType.UPDATE)
@Auth(permission_list=["notification:btn:update", "PUT:/notification/update/*"])
async def update_notification(
    request: Request,
    params: UpdateNotificationParams,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """更新通知（仅草稿状态可更新）"""
    notification = await SystemNotification.get_or_none(id=id, is_del=False)
    if not notification:
        return ResponseUtil.error(msg="通知不存在")
    
    if notification.status != NotificationStatus.DRAFT:
        return ResponseUtil.error(msg="只有草稿状态的通知可以编辑")
    
    # 权限检查
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    
    if user_type >= 2 and str(notification.creator_id) != user_id:
        return ResponseUtil.error(msg="无权编辑此通知")
    
    update_data = params.dict(exclude_none=True)
    if "expire_time" in update_data and update_data["expire_time"]:
        try:
            update_data["expire_time"] = datetime.fromisoformat(
                update_data["expire_time"].replace("Z", "+00:00")
            )
        except:
            del update_data["expire_time"]
    
    if update_data:
        await notification.update_from_dict(update_data)
        await notification.save()
    
    return ResponseUtil.success(msg="更新成功")


@notificationAPI.post("/publish/{id}", response_class=JSONResponse, summary="发布通知")
@Log(title="发布通知", operation_type=OperationType.UPDATE)
@Auth(permission_list=["notification:btn:publish", "POST:/notification/publish/*"])
async def publish_notification(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """发布通知"""
    notification = await SystemNotification.get_or_none(id=id, is_del=False)
    if not notification:
        return ResponseUtil.error(msg="通知不存在")
    
    if notification.status != NotificationStatus.DRAFT:
        return ResponseUtil.error(msg="只有草稿状态的通知可以发布")
    
    # 获取目标用户列表
    target_user_ids = await _get_target_users(notification)
    
    if not target_user_ids:
        return ResponseUtil.error(msg="没有符合条件的目标用户")
    
    # 更新通知状态
    notification.status = NotificationStatus.PUBLISHED
    notification.publish_time = datetime.now()
    await notification.save()
    
    # 创建用户通知关联
    for user_id in target_user_ids:
        await UserNotification.get_or_create(
            notification_id=notification.id,
            user_id=user_id
        )
    
    # 推送通知
    notification_service = NotificationService(request.app.state.redis)
    creator = await SystemUser.get_or_none(id=notification.creator_id)
    creator_name = creator.nickname if creator else "系统"
    
    result = await notification_service.push_notification(
        notification_id=str(notification.id),
        title=notification.title,
        content=notification.content,
        notification_type=notification.type,
        priority=notification.priority,
        target_user_ids=target_user_ids,
        creator_name=creator_name
    )
    
    return ResponseUtil.success(
        msg="发布成功",
        data={
            "total_users": len(target_user_ids),
            "online_count": result["online_count"],
            "offline_count": result["offline_count"]
        }
    )


@notificationAPI.post("/revoke/{id}", response_class=JSONResponse, summary="撤回通知")
@Log(title="撤回通知", operation_type=OperationType.UPDATE)
@Auth(permission_list=["notification:btn:revoke", "POST:/notification/revoke/*"])
async def revoke_notification(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """撤回通知"""
    notification = await SystemNotification.get_or_none(id=id, is_del=False)
    if not notification:
        return ResponseUtil.error(msg="通知不存在")
    
    if notification.status != NotificationStatus.PUBLISHED:
        return ResponseUtil.error(msg="只有已发布的通知可以撤回")
    
    notification.status = NotificationStatus.REVOKED
    await notification.save()
    
    return ResponseUtil.success(msg="撤回成功")


@notificationAPI.delete("/delete/{id}", response_class=JSONResponse, summary="删除通知")
@Log(title="删除通知", operation_type=OperationType.DELETE)
@Auth(permission_list=["notification:btn:delete", "DELETE:/notification/delete/*"])
async def delete_notification(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """删除通知"""
    notification = await SystemNotification.get_or_none(id=id, is_del=False)
    if not notification:
        return ResponseUtil.error(msg="通知不存在")
    
    notification.is_del = True
    await notification.save()
    
    return ResponseUtil.success(msg="删除成功")


@notificationAPI.get("/list", response_class=JSONResponse, summary="获取通知列表（管理）")
@Log(title="获取通知列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["notification:btn:list", "GET:/notification/list"])
async def get_notification_list(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    type: Optional[int] = Query(default=None, description="通知类型"),
    status: Optional[int] = Query(default=None, description="状态"),
    title: Optional[str] = Query(default=None, description="标题"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取通知列表（管理端）"""
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    
    filter_args = {"is_del": False}
    
    if type is not None:
        filter_args["type"] = type
    if status is not None:
        filter_args["status"] = status
    if title:
        filter_args["title__icontains"] = title
    
    # 部门管理员只能看自己创建的
    if user_type >= 2:
        filter_args["creator_id"] = user_id
    
    total = await SystemNotification.filter(**filter_args).count()
    result = await SystemNotification.filter(**filter_args).offset(
        (page - 1) * pageSize
    ).limit(pageSize).prefetch_related("creator").values(
        "id", "title", "content", "type", "scope", "scope_ids",
        "status", "priority", "publish_time", "expire_time",
        "created_at", "updated_at",
        creator_id="creator_id",
        creator_name="creator__nickname"
    )
    
    return ResponseUtil.success(data={
        "result": result,
        "total": total,
        "page": page,
        "pageSize": pageSize
    })


@notificationAPI.get("/info/{id}", response_class=JSONResponse, summary="获取通知详情")
@Log(title="获取通知详情", operation_type=OperationType.SELECT)
async def get_notification_info(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取通知详情"""
    notification = await SystemNotification.get_or_none(
        id=id, is_del=False
    ).prefetch_related("creator")
    
    if not notification:
        return ResponseUtil.error(msg="通知不存在")
    
    # 获取已读统计
    total_count = await UserNotification.filter(notification_id=id).count()
    read_count = await UserNotification.filter(notification_id=id, is_read=True).count()
    
    return ResponseUtil.success(data={
        "id": str(notification.id),
        "title": notification.title,
        "content": notification.content,
        "type": notification.type,
        "scope": notification.scope,
        "scope_ids": notification.scope_ids,
        "status": notification.status,
        "priority": notification.priority,
        "publish_time": notification.publish_time,
        "expire_time": notification.expire_time,
        "created_at": notification.created_at,
        "updated_at": notification.updated_at,
        "creator_id": str(notification.creator_id) if notification.creator_id else None,
        "creator_name": notification.creator.nickname if notification.creator else None,
        "statistics": {
            "total": total_count,
            "read": read_count,
            "unread": total_count - read_count
        }
    })


# ==================== 用户通知 API ====================

@notificationAPI.get("/my/list", response_class=JSONResponse, summary="获取我的通知列表")
async def get_my_notifications(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    is_read: Optional[bool] = Query(default=None, description="是否已读"),
    type: Optional[int] = Query(default=None, description="通知类型"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取当前用户的通知列表"""
    user_id = current_user.get("id")
    
    # 基础过滤条件
    base_filter = Q(user_id=user_id) & Q(notification__is_del=False) & Q(notification__status=NotificationStatus.PUBLISHED)
    
    if is_read is not None:
        base_filter &= Q(is_read=is_read)
    if type is not None:
        base_filter &= Q(notification__type=type)
    
    # 过期时间条件：未过期 或 没有设置过期时间
    expire_filter = Q(notification__expire_time__isnull=True) | Q(notification__expire_time__gt=datetime.now())
    
    final_filter = base_filter & expire_filter
    
    total = await UserNotification.filter(final_filter).count()
    
    result = await UserNotification.filter(final_filter).order_by(
        "-created_at"
    ).offset((page - 1) * pageSize).limit(pageSize).prefetch_related(
        "notification", "notification__creator"
    ).values(
        "id", "is_read", "read_time", "created_at",
        notification_id="notification_id",
        title="notification__title",
        content="notification__content",
        notification_type="notification__type",
        priority="notification__priority",
        publish_time="notification__publish_time",
        creator_name="notification__creator__nickname"
    )
    
    return ResponseUtil.success(data={
        "result": result,
        "total": total,
        "page": page,
        "pageSize": pageSize
    })


@notificationAPI.post("/my/read/{id}", response_class=JSONResponse, summary="标记通知已读")
async def mark_notification_read(
    request: Request,
    id: str = Path(description="用户通知ID"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """标记通知为已读"""
    user_id = current_user.get("id")
    
    user_notification = await UserNotification.get_or_none(
        id=id, user_id=user_id
    )
    
    if not user_notification:
        return ResponseUtil.error(msg="通知不存在")
    
    if not user_notification.is_read:
        user_notification.is_read = True
        user_notification.read_time = datetime.now()
        await user_notification.save()
        
        # 减少未读计数
        notification_service = NotificationService(request.app.state.redis)
        await notification_service.decrement_unread_count(user_id)
    
    return ResponseUtil.success(msg="已标记为已读")


@notificationAPI.post("/my/read-all", response_class=JSONResponse, summary="全部标记已读")
async def mark_all_read(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """全部标记为已读"""
    user_id = current_user.get("id")
    
    count = await UserNotification.filter(
        user_id=user_id, is_read=False
    ).update(is_read=True, read_time=datetime.now())
    
    # 重置未读计数
    notification_service = NotificationService(request.app.state.redis)
    await notification_service.reset_unread_count(user_id)
    
    return ResponseUtil.success(msg=f"已将 {count} 条通知标记为已读")


@notificationAPI.get("/my/unread-count", response_class=JSONResponse, summary="获取未读数量")
async def get_unread_count(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取未读通知数量"""
    user_id = current_user.get("id")
    
    # 从数据库查询实际未读数量
    count = await UserNotification.filter(
        user_id=user_id,
        is_read=False,
        notification__is_del=False,
        notification__status=NotificationStatus.PUBLISHED
    ).count()
    
    # 同步更新 Redis 缓存
    notification_service = NotificationService(request.app.state.redis)
    if count > 0:
        await request.app.state.redis.set(
            f"{notification_service.UNREAD_COUNT_KEY}:{user_id}",
            count
        )
    else:
        await request.app.state.redis.delete(
            f"{notification_service.UNREAD_COUNT_KEY}:{user_id}"
        )
    
    return ResponseUtil.success(data={"count": count})


@notificationAPI.get("/my/pending", response_class=JSONResponse, summary="获取待推送通知（HTTP轮询）")
async def get_pending_notifications(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取待推送的通知（用于 HTTP 轮询方式）"""
    user_id = current_user.get("id")
    
    notification_service = NotificationService(request.app.state.redis)
    notifications = await notification_service.get_pending_notifications(user_id)
    
    return ResponseUtil.success(data={"notifications": notifications})


# ==================== 辅助函数 ====================

async def _get_target_users(notification: SystemNotification) -> List[str]:
    """获取通知的目标用户列表"""
    if notification.scope == NotificationScope.ALL:
        # 全部用户
        users = await SystemUser.filter(is_del=False, status=1).values_list("id", flat=True)
        return [str(u) for u in users]
    
    elif notification.scope == NotificationScope.DEPARTMENT:
        # 指定部门（含下属）
        all_dept_ids = set()
        for dept_id in notification.scope_ids:
            child_ids = await DepartmentHelper.get_child_department_ids(dept_id)
            all_dept_ids.update(child_ids)
        
        users = await SystemUser.filter(
            is_del=False, status=1, department_id__in=list(all_dept_ids)
        ).values_list("id", flat=True)
        return [str(u) for u in users]
    
    elif notification.scope == NotificationScope.USER:
        # 指定用户
        return notification.scope_ids
    
    return []
