# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:25
# @UpdateTime : 2025/08/25 02:25
# @Author : sonder
# @File : log.py
# @Comment : 本程序
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse, DeleteListParams
from modules.log.schema import GetLoginLogResponse, GetOperationLogResponse
from modules.log.service import LoginLogService, OperationLogService
from utils.response import ResponseUtil

logAPI = APIRouter(
    prefix="/log",
)


def _build_filters(
    username: Optional[str] = None,
    nickname: Optional[str] = None,
    name: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None,
    username_field: str = "user_id__username",
    nickname_field: str = "user_id__nickname",
) -> dict:
    filter_args = {
        f"{k}__contains": v
        for k, v in {
            username_field: username,
            nickname_field: nickname,
            "operation_name": name,
            "operation_type": type,
        }.items()
        if v
    }
    if status is not None:
        filter_args["status"] = status
    if startTime and endTime:
        start_dt = datetime.fromtimestamp(float(startTime) / 1000)
        end_dt = datetime.fromtimestamp(float(endTime) / 1000)
        filter_args["created_at__range"] = [start_dt, end_dt]
    return filter_args


@logAPI.get(
    "/login",
    response_class=JSONResponse,
    response_model=GetLoginLogResponse,
    summary="用户获取登录日志",
)
@Log(title="用户获取登录日志", operation_type=OperationType.SELECT)
@Auth(permission_list=['login:btn:list'])
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
    redis = request.app.state.redis
    online_session_ids = await LoginLogService.get_online_session_ids(redis)
    filter_args = _build_filters(username=username, nickname=nickname, status=status, startTime=startTime, endTime=endTime)

    result, total = await LoginLogService.get_login_log_list(
        page, pageSize, filter_args,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
        department_id=department_id,
        online_session_ids=online_session_ids,
    )

    return ResponseUtil.success(data={"total": total, "result": result, "page": page, "pageSize": pageSize})


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
@Auth(permission_list=['login:btn:logout'])
async def logout_user(
    request: Request,
    id: str = Path(description="会话ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await LoginLogService.force_logout(
        id, request.app.state.redis,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.failure(msg=msg)


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
@Auth(permission_list=['login:btn:logout'])
async def logout_user_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await LoginLogService.batch_force_logout(
        params.ids, request.app.state.redis,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg)


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
@Auth(permission_list=['login:btn:delete'])
async def delete_login_log(
    request: Request,
    id: str = Path(..., description="登录日志ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await LoginLogService.delete_login_log(
        id, request.app.state.redis,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.failure(msg=msg)


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
@Auth(permission_list=['login:btn:delete'])
async def delete_login_log_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await LoginLogService.batch_delete_login_log(
        params.ids, request.app.state.redis,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg)


@logAPI.get(
    "/operation",
    response_class=JSONResponse,
    response_model=GetOperationLogResponse,
    summary="用户获取操作日志",
)
@Auth(permission_list=['operation:btn:list'])
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
    filter_args = _build_filters(
        username=username, nickname=nickname, name=name, type=type,
        status=status, startTime=startTime, endTime=endTime,
        username_field="operator__username", nickname_field="operator__nickname",
    )

    result, total = await OperationLogService.get_operation_log_list(
        page, pageSize, filter_args,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
        department_id=department_id,
    )

    return ResponseUtil.success(data={"total": total, "result": result, "page": page, "pageSize": pageSize})


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
@Auth(permission_list=['operation:btn:delete'])
async def delete_operation_log(
    request: Request,
    id: str = Path(..., description="操作日志id"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await OperationLogService.delete_operation_log(
        id,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.failure(msg=msg)


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
@Auth(permission_list=['operation:btn:delete'])
async def delete_operation_log_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await OperationLogService.batch_delete_operation_log(
        params.ids,
        user_type=current_user.get("user_type", 3),
        user_id=current_user.get("id"),
        sub_departments=current_user.get("sub_departments", []),
    )
    return ResponseUtil.success(msg=msg)


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
    user_id = current_user.get("id")
    filter_args = {}
    if status is not None:
        filter_args["status"] = status
    if startTime and endTime:
        start_time = datetime.fromisoformat(startTime.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(endTime.replace("Z", "+00:00"))
        filter_args["created_at__range"] = (start_time, end_time)

    result, total = await LoginLogService.get_personal_login_log(page, pageSize, user_id, filter_args)

    redis = request.app.state.redis
    online_session_ids = await LoginLogService.get_online_session_ids(redis)

    data = []
    for item in result:
        item_dict = {
            **item,
            "online": item["session_id"] in online_session_ids,
            "created_at": item["created_at"].isoformat() if item["created_at"] else "",
            "updated_at": item["updated_at"].isoformat() if item["updated_at"] else "",
        }
        data.append(item_dict)

    return ResponseUtil.success(data={"result": data, "total": total, "page": page, "pageSize": pageSize})


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
    success, msg = await LoginLogService.personal_force_logout(
        id, current_user.get("id"), request.app.state.redis
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.failure(msg=msg)


@logAPI.get(
    "/personal/operation",
    response_class=JSONResponse,
    response_model=GetOperationLogResponse,
    summary="获取个人操作日志",
)
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
    user_id = current_user.get("id")

    filter_args = {
        f"{k}__contains": v
        for k, v in {
            "operation_name": name,
            "operation_type": type,
        }.items()
        if v is not None
    }
    if status is not None:
        filter_args["status"] = status
    if startTime and endTime:
        start_dt = datetime.fromtimestamp(float(startTime) / 1000)
        end_dt = datetime.fromtimestamp(float(endTime) / 1000)
        filter_args["created_at__range"] = [start_dt, end_dt]

    result, total, today_count = await OperationLogService.get_personal_operation_log(
        page, pageSize, user_id, filter_args
    )

    return ResponseUtil.success(data={
        "total": total,
        "result": result,
        "page": page,
        "pageSize": pageSize,
        "todayCount": today_count,
    })
