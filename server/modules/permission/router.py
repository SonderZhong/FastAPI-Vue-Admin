# _*_ coding : UTF-8 _*_

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from modules import SystemPermission
from modules.permission.model import PermissionType
from core.common import BaseResponse
from modules.permission.schema import (
    AddPermissionParams,
    GetPermissionInfoResponse,
    GetPermissionListResponse,
)
from modules.permission.service import PermissionService
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil


permissionAPI = APIRouter(
    prefix="/permission",
    dependencies=[Depends(AuthController.get_current_user)],
)


PERMISSION_VALUE_FIELDS = (
    "id",
    "created_at",
    "updated_at",
    "menu_type",
    "code",
    "parent_id",
    "component",
    "name",
    "title",
    "path",
    "icon",
    "showBadge",
    "showTextBadge",
    "isHide",
    "isHideTab",
    "link",
    "isIframe",
    "keepAlive",
    "isFirstLevel",
    "fixedTab",
    "activePath",
    "isFullPage",
    "order",
    "api_path",
    "api_method",
    "remark",
)


def normalize_permission_payload(payload: dict) -> dict:
    return PermissionService.normalize_payload(payload)


async def clear_user_cache(request: Request):
    if user_infos := await request.app.state.redis.keys(
        f"{RedisKeyConfig.USER_INFO.key}:*"
    ):
        await request.app.state.redis.delete(*user_infos)
    if user_routes := await request.app.state.redis.keys(
        f"{RedisKeyConfig.USER_ROUTES.key}:*"
    ):
        await request.app.state.redis.delete(*user_routes)


async def delete_permission_recursive(permission_id: str):
    return await PermissionService.delete_permission_recursive(permission_id)


@permissionAPI.post(
    "/add", response_model=BaseResponse, response_class=JSONResponse, summary="新增权限"
)
@Log(title="新增权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["permission:btn:add"])
async def add_permission(request: Request, params: AddPermissionParams):
    permission = await PermissionService.create_permission(
        params.model_dump(exclude_none=True)
    )
    if permission:
        await clear_user_cache(request)
        return ResponseUtil.success(code=200, msg="新增成功")
    return ResponseUtil.error(code=500, msg="新增失败")


@permissionAPI.delete(
    "/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除权限",
)
@permissionAPI.post(
    "/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除权限",
)
@Log(title="删除权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["permission:btn:delete"])
async def delete_permission(request: Request, id: str = Path(description="权限ID")):
    permission = await SystemPermission.get_or_none(id=id, is_del=False)
    if not permission:
        return ResponseUtil.error(msg="删除权限失败，权限不存在")
    await PermissionService.delete_permission_recursive(str(permission.id))
    await clear_user_cache(request)
    return ResponseUtil.success(msg="删除权限成功")


@permissionAPI.put(
    "/update/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="更新权限",
)
@permissionAPI.post(
    "/update/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="更新权限",
)
@Log(title="更新权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["permission:btn:update"])
async def update_permission(
    request: Request, params: AddPermissionParams, id: str = Path(description="权限ID")
):
    permission = await SystemPermission.get_or_none(id=id, is_del=False)
    if not permission:
        return ResponseUtil.error(msg="更新权限失败，权限不存在")

    await PermissionService.update_permission(
        permission, params.model_dump(exclude_unset=True, exclude_none=True)
    )
    await clear_user_cache(request)
    return ResponseUtil.success(msg="更新权限成功")


@permissionAPI.get(
    "/info/{id}",
    response_model=GetPermissionInfoResponse,
    response_class=JSONResponse,
    summary="查询权限详情",
)
@Log(title="查询权限详情", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:info"])
async def get_permission(request: Request, id: str = Path(description="权限ID")):
    data = await SystemPermission.filter(id=id, is_del=False).values(
        *PERMISSION_VALUE_FIELDS
    )
    if not data:
        return ResponseUtil.error(msg="查询权限详情失败，权限不存在")
    return ResponseUtil.success(msg="查询权限详情成功", data=data[0])


@permissionAPI.get(
    "/list",
    response_model=GetPermissionListResponse,
    response_class=JSONResponse,
    summary="查询权限列表",
)
@Log(title="查询权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list"])
async def get_permission_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    menu_type: Optional[int] = Query(default=None, description="0菜单 1按钮 2接口"),
    parent_id: Optional[str] = Query(default=None, description="父权限ID"),
    code: Optional[str] = Query(default=None, description="权限编码"),
    name: Optional[str] = Query(default=None, description="权限名称"),
    title: Optional[str] = Query(default=None, description="菜单标题"),
    path: Optional[str] = Query(default=None, description="权限路径"),
    icon: Optional[str] = Query(default=None, description="图标"),
    auth_title: Optional[str] = Query(default=None, description="按钮标题"),
    auth_mark: Optional[str] = Query(default=None, description="按钮标识"),
    api_path: Optional[str] = Query(default=None, description="接口路径"),
    api_method: Optional[str] = Query(default=None, description="请求方法"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    filter_args = {
        key: value
        for key, value in {
            "menu_type": menu_type,
            "parent_id": parent_id,
            "code__icontains": code,
            "name__icontains": name,
            "title__icontains": title,
            "path__icontains": path,
            "icon__icontains": icon,
            "title__icontains": auth_title,
            "code__icontains": auth_mark,
            "api_path__icontains": api_path,
            "api_method__icontains": api_method,
        }.items()
        if value is not None
    }

    query = SystemPermission.filter(**filter_args, is_del=False)
    total = await query.count()
    result = (
        await query.offset((page - 1) * pageSize)
        .limit(pageSize)
        .order_by("order", "created_at")
        .values(*PERMISSION_VALUE_FIELDS)
    )
    return ResponseUtil.success(
        data={"total": total, "result": result, "page": page, "pageSize": pageSize}
    )


@permissionAPI.get(
    "/tree",
    response_model=GetPermissionListResponse,
    response_class=JSONResponse,
    summary="获取权限树",
)
@Log(title="获取权限树", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list"])
async def get_permission_tree(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    tree_data, permissions = await PermissionService.get_permission_tree(user_type)
    return ResponseUtil.success(
        data={
            "result": tree_data,
            "total": len(permissions),
            "page": 1,
            "pageSize": 9999,
        }
    )


@permissionAPI.get(
    "/buttons/{parent_id}",
    response_model=GetPermissionListResponse,
    response_class=JSONResponse,
    summary="获取指定菜单的按钮权限列表",
)
@Log(title="获取菜单按钮权限", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list"])
async def get_menu_buttons(
    request: Request,
    parent_id: str = Path(description="菜单ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_type = current_user.get("user_type", 3)
    buttons = await PermissionService.get_menu_buttons(parent_id, user_type)
    return ResponseUtil.success(
        data={"result": buttons, "total": len(buttons), "page": 1, "pageSize": 9999}
    )


@permissionAPI.post(
    "/button/add",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="添加按钮权限",
)
@Log(title="添加按钮权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["permission:btn:add"])
async def add_button_permission(
    request: Request,
    params: AddPermissionParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    payload = params.model_dump(exclude_none=True)
    payload["menu_type"] = PermissionType.BUTTON
    permission = await PermissionService.create_permission(payload)
    if permission:
        await clear_user_cache(request)
        return ResponseUtil.success(msg="添加按钮权限成功")
    return ResponseUtil.error(msg="添加按钮权限失败")


@permissionAPI.delete(
    "/button/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除按钮权限",
)
@permissionAPI.post(
    "/button/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除按钮权限",
)
@Log(title="删除按钮权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["permission:btn:delete"])
async def delete_button_permission(
    request: Request,
    id: str = Path(description="按钮权限ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    permission = await SystemPermission.get_or_none(
        id=id, menu_type=PermissionType.BUTTON, is_del=False
    )
    if not permission:
        return ResponseUtil.error(msg="删除按钮权限失败，权限不存在")
    await PermissionService.delete_permission_recursive(str(permission.id))
    await clear_user_cache(request)
    return ResponseUtil.success(msg="删除按钮权限成功")


@permissionAPI.put(
    "/button/update/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="更新按钮权限",
)
@permissionAPI.post(
    "/button/update/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="更新按钮权限",
)
@Log(title="更新按钮权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["permission:btn:update"])
async def update_button_permission(
    request: Request,
    params: AddPermissionParams,
    id: str = Path(description="按钮权限ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    permission = await SystemPermission.get_or_none(
        id=id, menu_type=PermissionType.BUTTON, is_del=False
    )
    if not permission:
        return ResponseUtil.error(msg="更新按钮权限失败，权限不存在")

    payload = params.model_dump(exclude_unset=True, exclude_none=True)
    payload["menu_type"] = PermissionType.BUTTON
    await PermissionService.update_permission(permission, payload)
    await clear_user_cache(request)
    return ResponseUtil.success(msg="更新按钮权限成功")
