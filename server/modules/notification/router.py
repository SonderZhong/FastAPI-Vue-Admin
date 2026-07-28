# _*_ coding : UTF-8 _*_
# @Time : 2025/12/28
# @Author : sonder
# @File : notification.py
# @Comment : 通知管理 API

import json
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse

from annotation.auth import AuthController, Auth
from annotation.log import Log, OperationType
from modules.notification.model import NotificationStatus
from modules.notification.schema import (
    CreateNotificationParams,
    UpdateNotificationParams,
)
from modules.notification.service import NotificationService, UserNotificationService
from utils.permission import UserType
from utils.notification import ws_manager, NotificationService as PushService
from utils.response import ResponseUtil

notificationAPI = APIRouter(prefix="/notification")
notificationWsAPI = APIRouter(prefix="/notification")


# ==================== WebSocket 端点 ====================


@notificationWsAPI.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user_id = None
    try:
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

        redis = websocket.app.state.redis
        redis_token = await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}")
        if not redis_token:
            await websocket.close(code=4001, reason="会话已过期")
            return

        await ws_manager.connect(websocket, user_id)

        push_service = PushService(redis)
        await websocket.send_json(
            {"type": "connected", "data": {"message": "WebSocket 连接成功"}}
        )

        pending = await push_service.get_pending_notifications(user_id)
        if pending:
            for notification in pending:
                await websocket.send_json(notification)

        from modules import UserNotification

        unread_count = await UserNotification.filter(
            user_id=user_id,
            is_read=False,
            notification__is_del=False,
            notification__status=NotificationStatus.PUBLISHED,
        ).count()
        await websocket.send_json(
            {"type": "unread_count", "data": {"count": unread_count}}
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                continue
            try:
                message = json.loads(data)
                if message.get("type") == "request":
                    await _handle_ws_request(websocket, message, user_id, redis)
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
        except Exception:
            pass


async def _handle_ws_request(websocket: WebSocket, message: dict, user_id: str, redis):
    from utils.get_redis import RedisKeyConfig

    action = message.get("action")
    request_id = message.get("requestId")
    if not action or not request_id:
        return

    try:
        if action == "getUserInfo":
            user_info_str = await redis.get(f"{RedisKeyConfig.USER_INFO.key}:{user_id}")
            if user_info_str:
                await websocket.send_json(
                    {
                        "type": "response",
                        "requestId": request_id,
                        "data": json.loads(user_info_str),
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "response",
                        "requestId": request_id,
                        "data": {"success": False, "msg": "用户信息不存在"},
                    }
                )
        elif action == "getUserRoutes":
            routes_str = await redis.get(f"{RedisKeyConfig.USER_ROUTES.key}:{user_id}")
            if routes_str:
                await websocket.send_json(
                    {
                        "type": "response",
                        "requestId": request_id,
                        "data": json.loads(routes_str),
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "response",
                        "requestId": request_id,
                        "data": {"success": False, "msg": "路由缓存不存在"},
                    }
                )
        else:
            await websocket.send_json(
                {
                    "type": "response",
                    "requestId": request_id,
                    "data": {"success": False, "msg": f"未知操作: {action}"},
                }
            )
    except Exception as e:
        await websocket.send_json(
            {
                "type": "response",
                "requestId": request_id,
                "data": {"success": False, "msg": str(e)},
            }
        )


# ==================== 通知管理 API ====================


@notificationAPI.post("/create", response_class=JSONResponse, summary="创建通知")
@Log(title="创建通知", operation_type=OperationType.INSERT)
@Auth(permission_list=["notification:btn:add"])
async def create_notification(
    request: Request,
    params: CreateNotificationParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await NotificationService.create_notification(
        params.dict(),
        user_type=current_user.get("user_type", UserType.NORMAL_USER),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    if success:
        return ResponseUtil.success(msg="创建成功", data={"id": msg})
    return ResponseUtil.error(msg=msg)


@notificationAPI.put("/update/{id}", response_class=JSONResponse, summary="更新通知")
@Log(title="更新通知", operation_type=OperationType.UPDATE)
@Auth(permission_list=["notification:btn:update"])
async def update_notification(
    request: Request,
    params: UpdateNotificationParams,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    update_data = params.dict(exclude_none=True)
    success, msg = await NotificationService.update_notification(
        id,
        update_data,
        user_type=current_user.get("user_type", UserType.NORMAL_USER),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@notificationAPI.post("/publish/{id}", response_class=JSONResponse, summary="发布通知")
@Log(title="发布通知", operation_type=OperationType.UPDATE)
@Auth(permission_list=["notification:btn:publish"])
async def publish_notification(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg, data = await NotificationService.publish_notification(
        id, request.app.state.redis
    )
    if success:
        return ResponseUtil.success(msg=msg, data=data)
    return ResponseUtil.error(msg=msg)


@notificationAPI.post("/revoke/{id}", response_class=JSONResponse, summary="撤回通知")
@Log(title="撤回通知", operation_type=OperationType.UPDATE)
@Auth(permission_list=["notification:btn:revoke"])
async def revoke_notification(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await NotificationService.revoke_notification(
        id,
        user_type=current_user.get("user_type", UserType.NORMAL_USER),
        user_id=current_user.get("id"),
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@notificationAPI.delete("/delete/{id}", response_class=JSONResponse, summary="删除通知")
@Log(title="删除通知", operation_type=OperationType.DELETE)
@Auth(permission_list=["notification:btn:delete"])
async def delete_notification(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await NotificationService.delete_notification(
        id,
        user_type=current_user.get("user_type", UserType.NORMAL_USER),
        user_id=current_user.get("id"),
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@notificationAPI.get(
    "/list", response_class=JSONResponse, summary="获取通知列表（管理）"
)
@Log(title="获取通知列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["notification:btn:list"])
async def get_notification_list(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    type: Optional[int] = Query(default=None, description="通知类型"),
    status: Optional[int] = Query(default=None, description="状态"),
    title: Optional[str] = Query(default=None, description="标题"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    filters = {"type": type, "status": status, "title": title}
    result, total = await NotificationService.get_notification_list(
        page,
        pageSize,
        user_type=current_user.get("user_type", UserType.NORMAL_USER),
        user_id=current_user.get("id"),
        department_id=current_user.get("department_id"),
        sub_departments=current_user.get("sub_departments", []),
        filters=filters,
    )
    return ResponseUtil.success(
        data={"result": result, "total": total, "page": page, "pageSize": pageSize}
    )


@notificationAPI.get("/info/{id}", response_class=JSONResponse, summary="获取通知详情")
@Log(title="获取通知详情", operation_type=OperationType.SELECT)
async def get_notification_info(
    request: Request,
    id: str = Path(description="通知ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    data, error = await NotificationService.get_notification_info(
        id,
        user_type=current_user.get("user_type", UserType.NORMAL_USER),
        user_id=current_user.get("id"),
        department_id=current_user.get("department_id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg=error)


# ==================== 用户通知 API ====================


@notificationAPI.get(
    "/my/list", response_class=JSONResponse, summary="获取我的通知列表"
)
async def get_my_notifications(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    is_read: Optional[bool] = Query(default=None, description="是否已读"),
    type: Optional[int] = Query(default=None, description="通知类型"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    result, total = await UserNotificationService.get_my_notifications(
        page, pageSize, current_user.get("id"), is_read, type
    )
    return ResponseUtil.success(
        data={"result": result, "total": total, "page": page, "pageSize": pageSize}
    )


@notificationAPI.post(
    "/my/read/{id}", response_class=JSONResponse, summary="标记通知已读"
)
async def mark_notification_read(
    request: Request,
    id: str = Path(description="用户通知ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await UserNotificationService.mark_read(
        id, current_user.get("id"), request.app.state.redis
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@notificationAPI.post(
    "/my/read-all", response_class=JSONResponse, summary="全部标记已读"
)
async def mark_all_read(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await UserNotificationService.mark_all_read(
        current_user.get("id"), request.app.state.redis
    )
    return ResponseUtil.success(msg=msg)


@notificationAPI.get(
    "/my/unread-count", response_class=JSONResponse, summary="获取未读数量"
)
async def get_unread_count(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    count = await UserNotificationService.get_unread_count(
        current_user.get("id"), request.app.state.redis
    )
    return ResponseUtil.success(data={"count": count})


@notificationAPI.get(
    "/my/pending", response_class=JSONResponse, summary="获取待推送通知（HTTP轮询）"
)
async def get_pending_notifications(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    push_service = PushService(request.app.state.redis)
    notifications = await push_service.get_pending_notifications(current_user.get("id"))
    return ResponseUtil.success(data={"notifications": notifications})
