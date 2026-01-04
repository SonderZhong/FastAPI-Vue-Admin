# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:25
# @UpdateTime : 2025/08/25 02:25
# @Author : sonder
# @File : log.py
# @Software : PyCharm
# @Comment : 本程序
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse
from jose import jwt

from annotation.auth import Auth,AuthController
from annotation.log import Log, OperationType
from models import SystemLoginLog, SystemOperationLog
from schemas.common import BaseResponse, DeleteListParams
from schemas.log import GetLoginLogResponse, GetOperationLogResponse
from utils.config import config
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil

logAPI = APIRouter(
    prefix="/log",
)


@logAPI.get(
    "/login",
    response_class=JSONResponse,
    response_model=GetLoginLogResponse,
    summary="用户获取登录日志",
)
@Log(title="用户获取登录日志", operation_type=OperationType.SELECT)
@Auth(permission_list=["login:btn:list", "GET:/log/login"])
async def get_login_log(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    username: Optional[str] = Query(default=None, description="用户账号"),
    nickname: Optional[str] = Query(default=None, description="用户昵称"),
    department_id: Optional[str] = Query(default=None, description="部门ID"),
    startTime: Optional[str] = Query(default=None, description="开始时间"),
    endTime: Optional[str] = Query(default=None, description="结束时间"),
    status: Optional[str] = Query(default=None, description="登录状态"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    async def get_online_session_ids() -> list:
        """
        获取所有在线用户的 session_id 列表
        """
        access_token_keys = await request.app.state.redis.keys(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:*"
        )
        if not access_token_keys:
            return []
        
        session_ids = []
        for key in access_token_keys:
            token = await request.app.state.redis.get(key)
            if token:
                try:
                    payload = jwt.decode(
                        token, config.jwt().secret_key, algorithms=[config.jwt().algorithm]
                    )
                    session_id = payload.get("session_id")
                    if session_id:
                        session_ids.append(session_id)
                except Exception:
                    # Token 解析失败，跳过
                    pass
        return session_ids

    sub_departments = current_user.get("sub_departments", [])
    user_id = current_user.get("id")
    user_type = current_user.get("user_type", 3)
    
    # 获取所有在线的 session_id
    online_session_ids = await get_online_session_ids()

    filterArgs = {
        f"{k}__contains": v
        for k, v in {
            "user_id__username": username,
            "user_id__nickname": nickname,
        }.items()
        if v
    }
    if status is not None:
        filterArgs["status"] = status
    if startTime and endTime:
        startTime = datetime.fromtimestamp(float(startTime) / 1000)
        endTime = datetime.fromtimestamp(float(endTime) / 1000)
        filterArgs["created_at__range"] = [startTime, endTime]

    # 根据用户身份过滤数据
    if user_type in [0, 1]:
        # 超级管理员和管理员可以查看所有用户的登录日志
        if department_id:
            filterArgs["user_id__department__id"] = department_id
        elif sub_departments:
            filterArgs["user_id__department__id__in"] = sub_departments
        # 如果 sub_departments 为空，超管/管理员不加部门过滤，可以看所有
    elif user_type == 2:
        # 部门管理员可以查看本部门及下属部门的登录日志
        if department_id:
            filterArgs["user_id__department__id"] = department_id
        elif sub_departments:
            filterArgs["user_id__department__id__in"] = sub_departments
        else:
            # 如果没有可访问的部门，返回空结果
            return ResponseUtil.success(
                data={
                    "total": 0,
                    "result": [],
                    "page": page,
                    "pageSize": pageSize,
                }
            )
    else:
        # 普通用户只能查看自己的登录日志
        filterArgs["user_id"] = user_id
        
    result = (
        await SystemLoginLog.filter(**filterArgs, user_id__is_del=False, is_del=False)
        .order_by("-created_at")
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .values(
            id="id",
            user_id="user_id_id",
            username="user_id__username",
            user_nickname="user_id__nickname",
            department_id="user_id__department__id",
            department_name="user_id__department__name",
            login_ip="login_ip",
            login_location="login_location",
            browser="browser",
            os="os",
            status="status",
            session_id="session_id",
            created_at="created_at",
            updated_at="updated_at",
        )
    )

    # 判断每条记录是否在线
    for log in result:
        log["online"] = log["session_id"] in online_session_ids
        
    return ResponseUtil.success(
        data={
            "total": await SystemLoginLog.filter(
                **filterArgs, user_id__is_del=False, is_del=False
            ).count(),
            "result": result,
            "page": page,
            "pageSize": pageSize,
        }
    )


@logAPI.delete(
    "/logout/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="用户强制退出",
)
@logAPI.post(
    "/logout/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="用户强制退出",
)
@Log(title="用户强制退出", operation_type=OperationType.DELETE)
@Auth(permission_list=["login:btn:logout", "DELETE,POST:/log/logout/*"])
async def logout_user(
    request: Request,
    id: str = Path(description="会话ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    sub_departments = current_user.get("sub_departments", [])

    # 根据用户身份验证权限
    if user_type in [0, 1, 2]:
        # 超级管理员、管理员、部门管理员：可以强退其可访问范围内的用户
        log = await SystemLoginLog.get_or_none(
            user_id__department__id__in=sub_departments, session_id=id, is_del=False
        )
    else:
        # 普通用户：只能强退自己的会话
        log = await SystemLoginLog.get_or_none(
            user_id=current_user.get("id"), session_id=id, is_del=False
        )

    if log:
        if await request.app.state.redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{id}"):
            await request.app.state.redis.delete(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{id}"
            )
            return ResponseUtil.success(msg="强退成功！")

    return ResponseUtil.failure(msg="会话不存在！")


@logAPI.delete(
    "/logoutList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="用户批量强制退出",
)
@logAPI.post(
    "/logoutList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="用户批量强制退出",
)
@Log(title="用户批量强制退出", operation_type=OperationType.DELETE)
@Auth(permission_list=["login:btn:logout", "DELETE,POST:/log/logoutList"])
async def logout_user_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    sub_departments = current_user.get("sub_departments", [])

    for id in params.ids:
        # 根据用户身份验证权限
        if user_type in [0, 1, 2]:
            # 超级管理员、管理员、部门管理员：可以强退其可访问范围内的用户
            log = await SystemLoginLog.get_or_none(
                user_id__department__id__in=sub_departments, session_id=id, is_del=False
            )
        else:
            # 普通用户：只能强退自己的会话
            log = await SystemLoginLog.get_or_none(
                user_id=current_user.get("id"), session_id=id, is_del=False
            )

        if log and await request.app.state.redis.get(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{id}"
        ):
            await request.app.state.redis.delete(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{id}"
            )

    return ResponseUtil.success(msg="批量强退成功！")


@logAPI.delete(
    "/delete/login/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户删除登录日志",
)
@logAPI.post(
    "/delete/login/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户删除登录日志",
)
@Log(title="用户删除登录日志", operation_type=OperationType.DELETE)
@Auth(permission_list=["login:btn:delete", "DELETE,POST:/log/delete/login/*"])
async def delete_login_log(
    request: Request,
    id: str = Path(..., description="登录日志ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    sub_departments = current_user.get("sub_departments", [])

    # 根据用户身份验证权限
    if user_type in [0, 1, 2]:
        # 超级管理员、管理员、部门管理员：可以删除其可访问范围内的日志
        log = await SystemLoginLog.get_or_none(
            id=id, user_id__department__id__in=sub_departments, is_del=False
        )
    else:
        # 普通用户：只能删除自己的日志
        log = await SystemLoginLog.get_or_none(
            id=id, user_id=current_user.get("id"), is_del=False
        )

    if log:
        log.is_del = True
        await log.save()
        if await request.app.state.redis.get(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
        ):
            await request.app.state.redis.delete(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
            )
        return ResponseUtil.success(msg="删除成功")
    else:
        return ResponseUtil.failure(msg="删除失败,登录日志不存在！")


@logAPI.delete(
    "/deleteList/login",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户批量删除登录日志",
)
@logAPI.post(
    "/deleteList/login",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户批量删除登录日志",
)
@Log(title="用户批量删除登录日志", operation_type=OperationType.DELETE)
@Auth(permission_list=["login:btn:delete", "DELETE,POST:/log/deleteList/login"])
async def delete_login_log_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    sub_departments = current_user.get("sub_departments", [])

    for id in set(params.ids):
        # 根据用户身份验证权限
        if user_type in [0, 1, 2]:
            # 超级管理员、管理员、部门管理员：可以删除其可访问范围内的日志
            log = await SystemLoginLog.get_or_none(
                id=id, user_id__department__id__in=sub_departments, is_del=False
            )
        else:
            # 普通用户：只能删除自己的日志
            log = await SystemLoginLog.get_or_none(
                id=id, user_id=current_user.get("id"), is_del=False
            )

        if log:
            log.is_del = True
            await log.save()
            if await request.app.state.redis.get(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
            ):
                await request.app.state.redis.delete(
                    f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
                )

    return ResponseUtil.success(msg="删除成功")


@logAPI.get(
    "/operation",
    response_class=JSONResponse,
    response_model=GetOperationLogResponse,
    summary="用户获取操作日志",
)
@Auth(permission_list=["operation:btn:list", "GET:/log/operation"])
async def get_operation_log(
    request: Request,
    page: int = Query(default=1, description="页码"),
    name: Optional[str] = Query(default=None, description="操作名称"),
    type: Optional[str] = Query(default=None, description="操作类型"),
    pageSize: int = Query(default=10, description="每页数量"),
    username: Optional[str] = Query(default=None, description="用户账号"),
    nickname: Optional[str] = Query(default=None, description="用户昵称"),
    department_id: Optional[str] = Query(default=None, description="部门ID"),
    startTime: Optional[str] = Query(default=None, description="开始时间"),
    endTime: Optional[str] = Query(default=None, description="结束时间"),
    status: Optional[str] = Query(default=None, description="登录状态"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    sub_departments = current_user.get("sub_departments", [])
    user_id = current_user.get("id")
    user_type = current_user.get("user_type", 3)

    filterArgs = {
        f"{k}__contains": v
        for k, v in {
            "operation_name": name,
            "operation_type": type,
            "operator__username": username,
            "operator__nickname": nickname,
        }.items()
        if v is not None
    }
    if status is not None:
        filterArgs["status"] = status
    if startTime and endTime:
        startTime = datetime.fromtimestamp(float(startTime) / 1000)
        endTime = datetime.fromtimestamp(float(endTime) / 1000)
        filterArgs["created_at__range"] = [startTime, endTime]

    # 根据用户身份过滤数据
    if user_type in [0, 1]:
        # 超级管理员和管理员可以查看所有用户的操作日志
        if department_id:
            filterArgs["operator__department__id"] = department_id
        elif sub_departments:
            filterArgs["operator__department__id__in"] = sub_departments
        # 如果 sub_departments 为空，超管/管理员不加部门过滤，可以看所有
    elif user_type == 2:
        # 部门管理员可以查看本部门及下属部门的操作日志
        if department_id:
            filterArgs["operator__department__id"] = department_id
        elif sub_departments:
            filterArgs["operator__department__id__in"] = sub_departments
        else:
            # 如果没有可访问的部门，返回空结果
            return ResponseUtil.success(
                data={
                    "total": 0,
                    "result": [],
                    "page": page,
                    "pageSize": pageSize,
                }
            )
    else:
        # 普通用户只能查看自己的操作日志
        filterArgs["operator_id"] = user_id
    result = (
        await SystemOperationLog.filter(
            **filterArgs, operator__is_del=False, is_del=False
        )
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .values(
            id="id",
            created_at="created_at",
            updated_at="updated_at",
            operation_name="operation_name",
            operation_type="operation_type",
            request_path="request_path",
            request_method="request_method",
            request_params="request_params",
            response_result="response_result",
            host="host",
            location="location",
            browser="browser",
            os="os",
            user_agent="user_agent",
            operator_id="operator_id",
            operator_name="operator__username",
            operator_nickname="operator__nickname",
            department_id="operator__department__id",
            department_name="operator__department__name",
            status="status",
            cost_time="cost_time",
        )
    )
    return ResponseUtil.success(
        data={
            "total": await SystemOperationLog.filter(
                **filterArgs, is_del=False, operator__is_del=False
            ).count(),
            "result": result,
            "page": page,
            "pageSize": pageSize,
        }
    )


@logAPI.delete(
    "/delete/operation/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户删除操作日志",
)
@logAPI.post(
    "/delete/operation/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户删除操作日志",
)
@Log(title="用户删除操作日志", operation_type=OperationType.DELETE)
@Auth(permission_list=["operation:btn:delete", "DELETE,POST:/log/delete/operation/*"])
async def delete_operation_log(
    request: Request,
    id: str = Path(..., description="操作日志id"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    sub_departments = current_user.get("sub_departments", [])

    # 根据用户身份验证权限
    if user_type in [0, 1, 2]:
        # 超级管理员、管理员、部门管理员：可以删除其可访问范围内的日志
        log = await SystemOperationLog.get_or_none(
            id=id, operator__department__id__in=sub_departments, is_del=False
        )
    else:
        # 普通用户：只能删除自己的日志
        log = await SystemOperationLog.get_or_none(
            id=id, operator_id=current_user.get("id"), is_del=False
        )

    if log:
        log.is_del = True
        await log.save()
        return ResponseUtil.success(msg="删除成功")
    else:
        return ResponseUtil.failure(msg="删除失败,操作日志不存在！")


@logAPI.delete(
    "/deleteList/operation",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户批量删除操作日志",
)
@logAPI.post(
    "/deleteList/operation",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="用户批量删除操作日志",
)
@Log(title="用户批量删除操作日志", operation_type=OperationType.DELETE)
@Auth(permission_list=["operation:btn:delete", "DELETE,POST:/log/deleteList/operation"])
async def delete_operation_log_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    sub_departments = current_user.get("sub_departments", [])

    # 根据用户身份过滤可删除的日志
    if user_type in [0, 1, 2]:
        # 超级管理员、管理员、部门管理员：可以删除其可访问范围内的日志
        await SystemOperationLog.filter(
            id__in=list(set(params.ids)),
            operator__department__id__in=sub_departments,
            is_del=False,
        ).update(is_del=True)
    else:
        # 普通用户：只能删除自己的日志
        await SystemOperationLog.filter(
            id__in=list(set(params.ids)),
            operator_id=current_user.get("id"),
            is_del=False,
        ).update(is_del=True)

    return ResponseUtil.success(msg="删除成功")


@logAPI.get(
    "/personal/login",
    response_class=JSONResponse,
    response_model=GetLoginLogResponse,
    summary="获取个人登录日志",
)
@Log(title="获取个人登录日志", operation_type=OperationType.SELECT)
async def get_personal_login_log(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    startTime: Optional[str] = Query(default=None, description="开始时间"),
    endTime: Optional[str] = Query(default=None, description="结束时间"),
    status: Optional[str] = Query(default=None, description="登录状态"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    async def get_online_user() -> list:
        """
        获取在线用户
        """
        access_token_keys = await request.app.state.redis.keys(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}*"
        )
        if not access_token_keys:
            access_token_keys = []
        online_users = []
        for access_token_key in access_token_keys:
            token = await request.app.state.redis.get(access_token_key)
            if token:
                try:
                    payload = jwt.decode(
                        token,
                        config.jwt().secret_key,
                        algorithms=[config.jwt().algorithm],
                    )
                    online_users.append(payload.get("session_id"))
                except Exception as e:
                    print(e)
        return online_users

    user_id = current_user.get("id")
    filterArgs = {}

    # 只查询当前用户的登录日志
    filterArgs["user_id"] = user_id

    if status is not None:
        filterArgs["status"] = status
    if startTime and endTime:
        start_time = datetime.fromisoformat(startTime.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(endTime.replace("Z", "+00:00"))
        filterArgs["created_at__range"] = (start_time, end_time)

    result = (
        await SystemLoginLog.filter(**filterArgs, user_id__is_del=False, is_del=False)
        .order_by("-created_at")
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .values(
            id="id",
            user_id="user_id_id",
            username="user_id__username",
            user_nickname="user_id__nickname",
            department_id="user_id__department__id",
            department_name="user_id__department__name",
            login_ip="login_ip",
            login_location="login_location",
            browser="browser",
            os="os",
            status="status",
            session_id="session_id",
            created_at="created_at",
            updated_at="updated_at",
        )
    )

    # 获取在线用户列表
    online_users = await get_online_user()

    data = []
    for item in result:
        item_dict = {
            **item,
            "online": item["session_id"] in online_users,
            "created_at": item["created_at"].isoformat() if item["created_at"] else "",
            "updated_at": item["updated_at"].isoformat() if item["updated_at"] else "",
        }
        data.append(item_dict)

    return ResponseUtil.success(
        data={
            "result": data,
            "total": await SystemLoginLog.filter(
                **filterArgs, user_id__is_del=False, is_del=False
            ).count(),
            "page": page,
            "pageSize": pageSize,
        }
    )


@logAPI.delete(
    "/personal/logout/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="个人强制退出",
)
@logAPI.post(
    "/personal/logout/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="个人强制退出",
)
@Log(title="个人强制退出", operation_type=OperationType.DELETE)
async def personal_logout_user(
    request: Request,
    id: str = Path(description="会话ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    if await SystemLoginLog.get_or_none(user_id=user_id, session_id=id, is_del=False):
        if await request.app.state.redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{id}"):
            await request.app.state.redis.delete(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{id}"
            )
            return ResponseUtil.success(msg="强退成功！")
        else:
            return ResponseUtil.failure(msg="强退失败,会话不存在！")
    else:
        return ResponseUtil.failure(msg="强退失败,登录日志不存在！")


@logAPI.get(
    "/personal/operation",
    response_class=JSONResponse,
    response_model=GetOperationLogResponse,
    summary="获取个人操作日志",
)
# @Log(title="获取个人操作日志", operation_type=OperationType.SELECT)
async def get_personal_operation_log(
    request: Request,
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    name: Optional[str] = Query(default=None, description="操作名称"),
    type: Optional[str] = Query(default=None, description="操作类型"),
    startTime: Optional[str] = Query(default=None, description="开始时间"),
    endTime: Optional[str] = Query(default=None, description="结束时间"),
    status: Optional[str] = Query(default=None, description="状态"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    """
    获取当前登录用户的个人操作日志
    无论用户身份如何，只返回当前用户自己的操作记录
    """
    user_id = current_user.get("id")
    
    filterArgs = {
        f"{k}__contains": v
        for k, v in {
            "operation_name": name,
            "operation_type": type,
        }.items()
        if v is not None
    }
    
    # 固定查询当前用户的操作日志
    filterArgs["operator_id"] = user_id
    
    if status is not None:
        filterArgs["status"] = status
    if startTime and endTime:
        startTime = datetime.fromtimestamp(float(startTime) / 1000)
        endTime = datetime.fromtimestamp(float(endTime) / 1000)
        filterArgs["created_at__range"] = [startTime, endTime]
    
    result = (
        await SystemOperationLog.filter(**filterArgs, operator__is_del=False, is_del=False)
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .order_by("-created_at")
        .values(
            id="id",
            created_at="created_at",
            updated_at="updated_at",
            operation_name="operation_name",
            operation_type="operation_type",
            request_path="request_path",
            request_method="request_method",
            request_params="request_params",
            response_result="response_result",
            host="host",
            location="location",
            browser="browser",
            os="os",
            user_agent="user_agent",
            operator_id="operator_id",
            operator_name="operator__username",
            operator_nickname="operator__nickname",
            department_id="operator__department__id",
            department_name="operator__department__name",
            status="status",
            cost_time="cost_time",
        )
    )
    
    # 计算今日操作数
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await SystemOperationLog.filter(
        operator_id=user_id,
        is_del=False,
        operator__is_del=False,
        created_at__gte=today_start
    ).count()
    
    return ResponseUtil.success(
        data={
            "total": await SystemOperationLog.filter(
                **filterArgs, is_del=False, operator__is_del=False
            ).count(),
            "result": result,
            "page": page,
            "pageSize": pageSize,
            "todayCount": today_count,
        }
    )
