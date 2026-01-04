# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:04
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : permission.py
# @Software : PyCharm
# @Comment : 权限管理 API - 完全使用 Casbin 管理权限（方案C）
from typing import Optional, List

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from models import SystemPermission
from models.permission import PermissionType
from schemas.common import BaseResponse
from schemas.permission import AddPermissionParams, GetPermissionInfoResponse, GetPermissionListResponse
from utils.casbin import CasbinEnforcer


def normalize_api_method(api_method) -> str:
    """
    统一API方法格式处理
    确保所有地方都使用相同的排序和格式化规则
    """
    if isinstance(api_method, str) and api_method.startswith('['):
        import json
        try:
            api_method = json.loads(api_method)
        except:
            api_method = [api_method]
    
    if isinstance(api_method, list):
        # 统一使用字母排序，确保一致性
        return ",".join(sorted(api_method))
    else:
        return api_method or "GET"
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil

permissionAPI = APIRouter(
    prefix="/permission",
    dependencies=[Depends(AuthController.get_current_user)]
)


@permissionAPI.post("/add", response_model=BaseResponse, response_class=JSONResponse, summary="新增权限")
@Log(title="新增权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["permission:btn:add", "POST:/permission/add"])
async def add_permission(request: Request, params: AddPermissionParams):
    params = params.dict()
    params = {k: v for k, v in params.items() if v is not None}
    if await SystemPermission.create(
            **params
    ):
        await clear_user_cache(request)
        return ResponseUtil.success(code=200, msg="新增成功")
    return ResponseUtil.error(code=500, msg="新增失败")


@permissionAPI.delete("/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除权限")
@permissionAPI.post("/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除权限")
@Log(title="删除权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["permission:btn:delete", "DELETE,POST:/permission/delete/*"])
async def delete_permission(request: Request, id: str = Path(description="权限ID")):
    if permission := await SystemPermission.get_or_none(id=id, is_del=False):
        # 移除角色权限
        await delete_permission_recursive(permission_id=permission.id)
        await clear_user_cache(request)
        return ResponseUtil.success(msg="删除权限成功！")
    else:
        return ResponseUtil.error(msg="删除权限失败，权限不存在！")


async def delete_permission_recursive(permission_id: str):
    """
    递归删除权限及其附属权限（同时从 Casbin 移除）
    :param permission_id: 权限ID
    :return:
    """
    # 获取权限信息
    permission = await SystemPermission.get_or_none(id=permission_id, is_del=False)
    if permission:
        # 从 Casbin 移除该权限（所有角色）
        perm_id = str(permission.id)
        if permission.menu_type == PermissionType.MENU:
            # 获取所有策略，移除包含该权限的
            all_policies = CasbinEnforcer.get_all_policies()
            for policy in all_policies:
                if len(policy) >= 3 and policy[1] == perm_id and policy[2] == "menu":
                    await CasbinEnforcer.remove_permission_for_role(policy[0], perm_id, "menu")
        elif permission.menu_type == PermissionType.BUTTON:
            all_policies = CasbinEnforcer.get_all_policies()
            for policy in all_policies:
                if len(policy) >= 3 and policy[1] == perm_id and policy[2] == "button":
                    await CasbinEnforcer.remove_permission_for_role(policy[0], perm_id, "button")
        elif permission.menu_type == PermissionType.API and permission.api_path:
            all_policies = CasbinEnforcer.get_all_policies()
            for policy in all_policies:
                if len(policy) >= 3 and policy[1] == permission.api_path:
                    await CasbinEnforcer.remove_api_permission_for_role(policy[0], permission.api_path, policy[2])
    
    await SystemPermission.filter(id=permission_id, is_del=False).update(is_del=True)
    
    sub_permissions = await SystemPermission.filter(parent_id=permission_id, is_del=False).all()
    for sub_department in sub_permissions:
        await delete_permission_recursive(sub_department.id)
    return True


@permissionAPI.put("/update/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="更新权限")
@permissionAPI.post("/update/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="更新权限")
@Log(title="更新权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["permission:btn:update", "PUT,POST:/permission/update/*"])
async def update_permission(request: Request, params: AddPermissionParams, id: str = Path(description="权限ID"), ):
    if permission := await SystemPermission.get_or_none(id=id, is_del=False):
        params = params.dict()
        params = {k: v for k, v in params.items() if v is not None}
        await permission.update_from_dict(params)
        await permission.save()
        # 更新用户信息缓存
        await clear_user_cache(request)
        return ResponseUtil.success(msg="更新权限成功！")
    else:
        return ResponseUtil.error(msg="更新权限失败，权限不存在！")


@permissionAPI.get("/info/{id}", response_model=GetPermissionInfoResponse, response_class=JSONResponse,
                   summary="查询权限详情")
@Log(title="查询权限详情", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:info", "GET:/permission/info/*"])
async def get_permission(request: Request, id: str = Path(description="权限ID")):
    if permission := await SystemPermission.get_or_none(id=id, is_del=False):
        return ResponseUtil.success(msg="查询权限详情成功！", data={
            "id": permission.id,
            "created_at": permission.created_at,
            "updated_at": permission.updated_at,
            "menu_type": permission.menu_type,
            "parent_id": permission.parent_id,
            "name": permission.name,
            "title": permission.title,
            "path": permission.path,
            "component": permission.component,
            "icon": permission.icon,
            "showBadge": permission.showBadge,
            "showTextBadge": permission.showTextBadge,
            "isHide": permission.isHide,
            "isHideTab": permission.isHideTab,
            "link": permission.link,
            "isIframe": permission.isIframe,
            "keepAlive": permission.keepAlive,
            "isFirstLevel": permission.isFirstLevel,
            "fixedTab": permission.fixedTab,
            "activePath": permission.activePath,
            "isFullPage": permission.isFullPage,
            "order": permission.order,
            "authTitle": permission.authTitle,
            "authMark": permission.authMark,
            "min_user_type": permission.min_user_type,
            # 接口权限字段
            "api_path": permission.api_path,
            "api_method": permission.api_method,
            "data_scope": permission.data_scope,
            "remark": permission.remark
        })
    else:
        return ResponseUtil.error(msg="查询权限详情失败，权限不存在！")


@permissionAPI.get("/list", response_model=GetPermissionListResponse, response_class=JSONResponse,
                   summary="查询权限列表")
@Log(title="查询权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list", "GET:/permission/list"])
async def get_permission_list(
        request: Request,
        page: int = Query(default=1, description="当前页码"),
        pageSize: int = Query(default=10, description="每页数量"),
        menu_type: Optional[str] = Query(default=None, description="权限类型 0菜单 1按钮 2接口"),
        parent_id: Optional[str] = Query(default=None, description="父权限ID"),
        name: Optional[str] = Query(default=None, description="权限名称"),
        title: Optional[str] = Query(default=None, description="菜单标题"),
        path: Optional[str] = Query(default=None, description="权限路径"),
        icon: Optional[str] = Query(default=None, description="图标"),
        auth_title: Optional[str] = Query(default=None, description="权限标题"),
        auth_mark: Optional[str] = Query(default=None, description="权限标识"),
        api_path: Optional[str] = Query(default=None, description="接口路径"),
        api_method: Optional[str] = Query(default=None, description="请求方法")
):
    filterArgs = {
        k: v for k, v in {
            "menu_type": menu_type,
            "parent_id": parent_id,
            "name__icontains": name,
            "title__icontains": title,
            "path__icontains": path,
            "icon__icontains": icon,
            "auth_title__icontains": auth_title,
            "auth_mark__icontains": auth_mark,
            "api_path__icontains": api_path,
            "api_method__icontains": api_method,
        }.items() if v is not None
    }
    total = await SystemPermission.filter(**filterArgs, is_del=False).count()
    result = await SystemPermission.filter(**filterArgs, is_del=False).offset((page - 1) * pageSize).limit(
        pageSize).order_by(
        'order').values(
        "id",
        "created_at",
        "updated_at",
        "menu_type",
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
        "authTitle",
        "authMark",
        "min_user_type",
        "api_path",
        "api_method",
        "data_scope",
        "remark",
    )
    return ResponseUtil.success(data={
        "total": total,
        "result": result,
        "page": page,
    })


@permissionAPI.get("/tree", response_model=GetPermissionListResponse, response_class=JSONResponse,
                   summary="获取权限树形结构数据")
@Log(title="获取权限树形结构数据", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list", "GET:/permission/tree"])
async def get_permission_tree(
        request: Request,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取权限树形结构，包含菜单和按钮权限"""
    
    # 获取所有权限数据
    permissions = await SystemPermission.filter(is_del=False).order_by("order", "created_at").values(
        id="id",
        menu_type="menu_type",
        parent_id="parent_id", 
        name="name",
        title="title",
        path="path",
        component="component",
        icon="icon",
        showBadge="showBadge",
        showTextBadge="showTextBadge",
        isHide="isHide",
        isHideTab="isHideTab",
        link="link",
        isIframe="isIframe",
        keepAlive="keepAlive",
        isFirstLevel="isFirstLevel",
        fixedTab="fixedTab",
        activePath="activePath",
        isFullPage="isFullPage",
        order="order",
        authTitle="authTitle",
        authMark="authMark",
        min_user_type="min_user_type",
        created_at="created_at",
        updated_at="updated_at",
        # 接口权限字段
        api_path="api_path",
        api_method="api_method",
        data_scope="data_scope",
        remark="remark"
    )
    
    # 构建树形结构
    def build_tree(parent_id=None):
        tree = []
        for perm in permissions:
            if str(perm.get("parent_id")) == str(parent_id):
                perm_copy = dict(perm)
                children = build_tree(perm.get("id"))
                if children:
                    perm_copy["children"] = children
                tree.append(perm_copy)
        return tree
    
    tree_data = build_tree()
    
    return ResponseUtil.success(data={
        "result": tree_data,
        "total": len(permissions),
        "page": 1,
        "pageSize": 9999
    })


@permissionAPI.get("/buttons/{parent_id}", response_model=GetPermissionListResponse, response_class=JSONResponse,
                   summary="获取指定菜单的按钮权限列表")
@Log(title="获取菜单按钮权限", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list", "GET:/permission/buttons/*"])
async def get_menu_buttons(
        request: Request,
        parent_id: str = Path(description="菜单ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取指定菜单下的按钮权限列表"""
    
    buttons = await SystemPermission.filter(
        parent_id=parent_id, 
        menu_type=1,  # 按钮类型
        is_del=False
    ).order_by("order", "created_at").values(
        id="id",
        menu_type="menu_type",
        parent_id="parent_id",
        name="name",
        title="title",
        path="path",
        component="component",
        icon="icon",
        order="order",
        authTitle="authTitle",
        authMark="authMark",
        created_at="created_at",
        updated_at="updated_at"
    )
    
    return ResponseUtil.success(data={
        "result": buttons,
        "total": len(buttons),
        "page": 1,
        "pageSize": 9999
    })


@permissionAPI.post("/button/add", response_model=BaseResponse, response_class=JSONResponse, summary="添加按钮权限")
@Log(title="添加按钮权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["permission:btn:add", "POST:/permission/button/add"])
async def add_button_permission(
        request: Request, 
        params: AddPermissionParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """为指定菜单添加按钮权限"""
    
    # 确保是按钮类型
    params_dict = params.dict()
    params_dict["menu_type"] = 1  # 强制设置为按钮类型
    params_dict = {k: v for k, v in params_dict.items() if v is not None}
    
    if await SystemPermission.create(**params_dict):
        # 清除用户缓存
        await clear_user_cache(request)
        return ResponseUtil.success(msg="添加按钮权限成功")
    return ResponseUtil.error(msg="添加按钮权限失败")


@permissionAPI.delete("/button/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除按钮权限")
@permissionAPI.post("/button/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除按钮权限")
@Log(title="删除按钮权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["permission:btn:delete", "DELETE,POST:/permission/button/delete/*"])
async def delete_button_permission(
        request: Request, 
        id: str = Path(description="按钮权限ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """删除按钮权限"""
    
    if permission := await SystemPermission.get_or_none(id=id, menu_type=1, is_del=False):
        await permission.update(is_del=True)
        
        # 从 Casbin 移除该按钮权限（所有角色）
        all_policies = CasbinEnforcer.get_all_policies()
        for policy in all_policies:
            if len(policy) >= 3 and policy[1] == id and policy[2] == "button":
                await CasbinEnforcer.remove_permission_for_role(policy[0], id, "button")
        
        # 清除用户缓存
        await clear_user_cache(request)
        return ResponseUtil.success(msg="删除按钮权限成功")
    return ResponseUtil.error(msg="删除按钮权限失败，权限不存在")


@permissionAPI.put("/button/update/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="更新按钮权限")
@permissionAPI.post("/button/update/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="更新按钮权限")
@Log(title="更新按钮权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["permission:btn:update", "PUT,POST:/permission/button/update/*"])
async def update_button_permission(
        request: Request,
        params: AddPermissionParams,
        id: str = Path(description="按钮权限ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """更新按钮权限"""
    
    if permission := await SystemPermission.get_or_none(id=id, menu_type=1, is_del=False):
        params_dict = params.dict()
        params_dict["menu_type"] = 1  # 确保是按钮类型
        params_dict = {k: v for k, v in params_dict.items() if v is not None}
        
        await permission.update_from_dict(params_dict)
        await permission.save()
        
        # 清除用户缓存
        await clear_user_cache(request)
        return ResponseUtil.success(msg="更新按钮权限成功")
    return ResponseUtil.error(msg="更新按钮权限失败，权限不存在")


async def clear_user_cache(request: Request):
    """清除用户相关缓存"""
    # 清除用户信息缓存
    if user_infos := await request.app.state.redis.keys(f'{RedisKeyConfig.USER_INFO.key}:*'):
        await request.app.state.redis.delete(*user_infos)
    
    # 清除用户路由缓存
    if user_routes := await request.app.state.redis.keys(f'{RedisKeyConfig.USER_ROUTES.key}:*'):
        await request.app.state.redis.delete(*user_routes)


# ==================== 接口权限 API ====================



class AddApiPermissionParams(BaseModel):
    """添加接口权限参数"""
    parent_id: Optional[str] = None
    title: str  # 权限名称
    api_path: str  # 接口路径，如 /api/user/*
    api_method: List[str]  # 请求方法列表，如 ["GET", "POST", "PUT", "DELETE"]
    data_scope: int = 4  # 数据范围，默认仅本人
    min_user_type: int = 3  # 最低用户类型
    authMark: Optional[str] = None  # 权限标识
    remark: Optional[str] = None  # 备注


class SyncRolePermissionsParams(BaseModel):
    """同步角色权限参数"""
    role_code: str
    permission_ids: List[str]


@permissionAPI.get("/api/list", response_class=JSONResponse, summary="获取接口权限列表")
@Log(title="获取接口权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["permission:btn:list", "GET:/permission/api/list"])
async def get_api_permission_list(
        request: Request,
        page: int = Query(default=1, description="当前页码"),
        pageSize: int = Query(default=50, description="每页数量"),
        api_path: Optional[str] = Query(default=None, description="接口路径"),
        api_method: Optional[str] = Query(default=None, description="请求方法"),
        title: Optional[str] = Query(default=None, description="权限名称"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取所有接口类型的权限"""
    filterArgs = {"menu_type": PermissionType.API}
    
    if api_path:
        filterArgs["api_path__icontains"] = api_path
    if api_method:
        filterArgs["api_method__icontains"] = api_method
    if title:
        filterArgs["title__icontains"] = title
    
    total = await SystemPermission.filter(**filterArgs, is_del=False).count()
    result = await SystemPermission.filter(**filterArgs, is_del=False).offset(
        (page - 1) * pageSize
    ).limit(pageSize).order_by("order", "created_at").values(
        "id", "title", "api_path", "api_method", "data_scope",
        "min_user_type", "authMark", "remark", "parent_id",
        "created_at", "updated_at"
    )
    
    return ResponseUtil.success(data={
        "result": result,
        "total": total,
        "page": page,
        "pageSize": pageSize
    })


@permissionAPI.post("/api/add", response_class=JSONResponse, summary="添加接口权限")
@Log(title="添加接口权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["permission:btn:add", "POST:/permission/api/add"])
async def add_api_permission(
        request: Request,
        params: AddApiPermissionParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """添加接口权限"""
    permission = await SystemPermission.create(
        menu_type=PermissionType.API,
        parent_id=params.parent_id,
        title=params.title,
        api_path=params.api_path,
        api_method=params.api_method,
        data_scope=params.data_scope,
        min_user_type=params.min_user_type,
        authMark=params.authMark,
        remark=params.remark
    )
    
    if permission:
        return ResponseUtil.success(msg="添加接口权限成功", data={"id": str(permission.id)})
    return ResponseUtil.error(msg="添加接口权限失败")


@permissionAPI.put("/api/update/{id}", response_class=JSONResponse, summary="更新接口权限")
@permissionAPI.post("/api/update/{id}", response_class=JSONResponse, summary="更新接口权限")
@Log(title="更新接口权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["permission:btn:update", "PUT,POST:/permission/api/update/*"])
async def update_api_permission(
        request: Request,
        params: AddApiPermissionParams,
        id: str = Path(description="权限ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """更新接口权限"""
    permission = await SystemPermission.get_or_none(
        id=id, menu_type=PermissionType.API, is_del=False
    )
    
    if not permission:
        return ResponseUtil.error(msg="接口权限不存在")
    
    permission.title = params.title
    permission.api_path = params.api_path
    permission.api_method = params.api_method
    permission.data_scope = params.data_scope
    permission.min_user_type = params.min_user_type
    permission.authMark = params.authMark
    permission.remark = params.remark
    if params.parent_id:
        permission.parent_id = params.parent_id
    
    await permission.save()
    
    # 重新加载 Casbin 策略
    await CasbinEnforcer.reload_policy()
    
    return ResponseUtil.success(msg="更新接口权限成功")


@permissionAPI.delete("/api/delete/{id}", response_class=JSONResponse, summary="删除接口权限")
@permissionAPI.post("/api/delete/{id}", response_class=JSONResponse, summary="删除接口权限")
@Log(title="删除接口权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["permission:btn:delete", "DELETE,POST:/permission/api/delete/*"])
async def delete_api_permission(
        request: Request,
        id: str = Path(description="权限ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """删除接口权限"""
    permission = await SystemPermission.get_or_none(
        id=id, menu_type=PermissionType.API, is_del=False
    )
    
    if not permission:
        return ResponseUtil.error(msg="接口权限不存在")
    
    # 从 Casbin 移除该 API 权限（所有角色）
    if permission.api_path:
        all_policies = CasbinEnforcer.get_all_policies()
        for policy in all_policies:
            if len(policy) >= 3 and policy[1] == permission.api_path:
                await CasbinEnforcer.remove_api_permission_for_role(policy[0], permission.api_path, policy[2])
    
    # 软删除
    permission.is_del = True
    await permission.save()
    
    # 重新加载 Casbin 策略
    await CasbinEnforcer.reload_policy()
    
    return ResponseUtil.success(msg="删除接口权限成功")


@permissionAPI.post("/api/sync-to-casbin", response_class=JSONResponse, summary="同步角色接口权限到Casbin")
@Log(title="同步权限到Casbin", operation_type=OperationType.OTHER)
@Auth(permission_list=["permission:btn:update", "POST:/permission/api/sync-to-casbin"])
async def sync_role_api_permissions_to_casbin(
        request: Request,
        params: SyncRolePermissionsParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """将角色的权限同步到 Casbin"""
    from models import SystemPermission
    from models.permission import PermissionType
    
    # 获取所有权限
    permissions = await SystemPermission.filter(
        id__in=params.permission_ids,
        is_del=False
    ).all()
    
    # 分类处理
    menu_ids = []
    button_ids = []
    added = 0
    
    for perm in permissions:
        perm_id = str(perm.id)
        if perm.menu_type == PermissionType.MENU:
            menu_ids.append(perm_id)
        elif perm.menu_type == PermissionType.BUTTON:
            button_ids.append(perm_id)
        elif perm.menu_type == PermissionType.API and perm.api_path and perm.api_method:
            method_str = normalize_api_method(perm.api_method)
            result = await CasbinEnforcer.add_api_permission_for_role(
                params.role_code, perm.api_path, method_str
            )
            if result:
                added += 1
    
    # 设置菜单和按钮权限
    menu_result = await CasbinEnforcer.set_role_permissions(params.role_code, menu_ids, "menu")
    button_result = await CasbinEnforcer.set_role_permissions(params.role_code, button_ids, "button")
    
    return ResponseUtil.success(
        msg=f"同步完成: 菜单 {menu_result['added']} 添加/{menu_result['removed']} 移除, 按钮 {button_result['added']} 添加/{button_result['removed']} 移除, API {added} 添加",
        data={
            "menu": menu_result,
            "button": button_result,
            "api_added": added
        }
    )


@permissionAPI.post("/api/init-casbin", response_class=JSONResponse, summary="初始化Casbin策略")
@Log(title="初始化Casbin策略", operation_type=OperationType.OTHER)
@Auth(permission_list=["permission:btn:update", "POST:/permission/api/init-casbin"])
async def init_casbin_policies(
        request: Request,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """重新加载 Casbin 策略"""
    await CasbinEnforcer.reload_policy()
    
    return ResponseUtil.success(msg="Casbin 策略已重新加载")

