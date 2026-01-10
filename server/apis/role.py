# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 01:10
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : role.py
# @Software : PyCharm
# @Comment : 角色管理 API - 完全使用 Casbin 管理权限（方案C）
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from models import SystemRole, SystemPermission, SystemDepartment
from models.permission import PermissionType
from schemas.common import BaseResponse, DeleteListParams
from schemas.role import AddRoleParams, UpdateRoleParams, UpdateRoleResponse, AddRolePermissionParams, \
    GetRolePermissionInfoResponse, GetRolePermissionListResponse, GetRoleInfoResponse, GetRoleListResponse
from utils.casbin import CasbinEnforcer, DataScope
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil


def normalize_api_method(api_method) -> str:
    """
    统一API方法格式处理
    确保所有地方都使用相同的排序和格式化规则
    """
    if isinstance(api_method, str) and api_method.startswith('['):
        import json
        try:
            api_method = json.loads(api_method)
        except Exception:
            api_method = [api_method]
    
    if isinstance(api_method, list):
        # 统一使用字母排序，确保一致性
        return ",".join(sorted(api_method))
    else:
        return api_method or "GET"

roleAPI = APIRouter(
    prefix="/role"
)


async def clear_role_cache(request: Request):
    """清除角色相关缓存"""
    try:
        # 清除用户信息缓存
        userInfos = await request.app.state.redis.keys(f'{RedisKeyConfig.USER_INFO.key}*')
        if userInfos:
            await request.app.state.redis.delete(*userInfos)
        
        # 清除用户路由缓存
        userRoutes = await request.app.state.redis.keys(f'{RedisKeyConfig.USER_ROUTES.key}*')
        if userRoutes:
            await request.app.state.redis.delete(*userRoutes)
        
        # 清除角色相关缓存
        roleKeys = await request.app.state.redis.keys('role_*')
        if roleKeys:
            await request.app.state.redis.delete(*roleKeys)
            
        print(f"清除缓存完成: 用户信息({len(userInfos)}), 用户路由({len(userRoutes)}), 角色({len(roleKeys)})")
        
    except Exception as e:
        print(f"清除缓存失败: {e}")
        # 不抛出异常，避免影响主要业务流程


async def sync_role_permissions_to_casbin(role_code: str, permission_ids: list):
    """
    同步角色的所有权限到 Casbin（菜单/按钮/接口）
    
    Args:
        role_code: 角色编码
        permission_ids: 权限ID列表
    """
    # 获取所有权限
    permissions = await SystemPermission.filter(
        id__in=permission_ids,
        is_del=False
    ).all()
    
    # 分类处理
    menu_ids = []
    button_ids = []
    
    for perm in permissions:
        perm_id = str(perm.id)
        if perm.menu_type == PermissionType.MENU:
            menu_ids.append(perm_id)
        elif perm.menu_type == PermissionType.BUTTON:
            button_ids.append(perm_id)
        elif perm.menu_type == PermissionType.API:
            # API 权限直接添加到 Casbin
            if perm.api_path and perm.api_method:
                method_str = normalize_api_method(perm.api_method)
                await CasbinEnforcer.add_api_permission_for_role(
                    role_code, perm.api_path, method_str
                )
    
    # 设置菜单权限
    await CasbinEnforcer.set_role_permissions(role_code, menu_ids, "menu")
    # 设置按钮权限
    await CasbinEnforcer.set_role_permissions(role_code, button_ids, "button")


@roleAPI.post("/add", response_model=BaseResponse, response_class=JSONResponse, summary="新增角色")
@Log(title="新增角色", operation_type=OperationType.INSERT)
@Auth(permission_list=["role:btn:add", "POST:/role/add"])
async def add_role(request: Request, params: AddRoleParams,
                   current_user: dict = Depends(AuthController.get_current_user)):
    # 验证部门权限
    if not params.department_id:
        return ResponseUtil.error(msg="部门ID不能为空！")
    
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_department_data(str(user_id), params.department_id)
    if not can_access:
        return ResponseUtil.error(msg="新增失败,无权限操作该部门！")
    
    # 检查角色编码是否已存在（全局唯一）
    if await SystemRole.get_or_none(code=params.code, is_del=False):
        return ResponseUtil.error(msg="角色编码已存在！")
    
    # 验证部门是否存在
    department = await SystemDepartment.get_or_none(id=params.department_id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="指定的部门不存在！")
    
    # 创建角色
    role = await SystemRole.create(
        code=params.code,
        name=params.name,
        description=params.description,
        status=params.status,
        department_id=department.id,
    )
    if role:
        await clear_role_cache(request)
        return ResponseUtil.success(msg="新增角色成功！")
    return ResponseUtil.error(msg="新增角色失败！")


@roleAPI.delete("/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除角色")
@roleAPI.post("/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除角色")
@Log(title="删除角色", operation_type=OperationType.DELETE)
@Auth(permission_list=["role:btn:delete", "DELETE,POST:/role/delete/*"])
async def delete_role(request: Request, id: str = Path(..., description="角色ID"),
                      current_user: dict = Depends(AuthController.get_current_user)):
    role = await SystemRole.get_or_none(id=id, is_del=False).prefetch_related("department")
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), dept_id)
        if not can_access:
            return ResponseUtil.error(msg="删除失败,无权限操作该部门的角色！")
    
    # 删除 Casbin 中该角色的所有策略（包括权限和用户关联）
    await CasbinEnforcer.delete_role(role.code)
    
    role.is_del = True
    await role.save()
    
    await clear_role_cache(request)
    return ResponseUtil.success(msg="删除角色成功！")


@roleAPI.delete("/deleteList", response_model=BaseResponse, response_class=JSONResponse, summary="批量删除角色")
@roleAPI.post("/deleteList", response_model=BaseResponse, response_class=JSONResponse, summary="批量删除角色")
@Log(title="批量删除角色", operation_type=OperationType.DELETE)
@Auth(permission_list=["role:btn:delete", "DELETE,POST:/role/deleteList"])
async def delete_role_list(request: Request, params: DeleteListParams,
                           current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    deleted_count = 0
    
    for id in set(params.ids):
        role = await SystemRole.get_or_none(id=id, is_del=False)
        if not role:
            continue
        
        # 使用 Casbin 检查部门数据权限
        dept_id = str(role.department_id) if role.department_id else None
        if dept_id:
            can_access = await CasbinEnforcer.can_access_department_data(str(user_id), dept_id)
            if not can_access:
                continue
        
        # 删除 Casbin 中该角色的所有策略
        await CasbinEnforcer.delete_role(role.code)
        
        role.is_del = True
        await role.save()
        deleted_count += 1
    
    await clear_role_cache(request)
    return ResponseUtil.success(msg=f"批量删除角色成功，共删除 {deleted_count} 个角色！")


@roleAPI.put("/update/{id}", response_model=UpdateRoleResponse, response_class=JSONResponse, summary="修改角色")
@roleAPI.post("/update/{id}", response_model=UpdateRoleResponse, response_class=JSONResponse, summary="修改角色")
@Log(title="修改角色", operation_type=OperationType.UPDATE)
@Auth(permission_list=["role:btn:update", "PUT,POST:/role/update/*"])
async def update_role(request: Request, params: UpdateRoleParams, id: str = Path(..., description="角色ID"),
                      current_user: dict = Depends(AuthController.get_current_user)):
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    user_id = current_user.get("id")
    
    # 检查原部门权限
    if role.department_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), str(role.department_id))
        if not can_access:
            return ResponseUtil.error(msg="修改失败,无权限操作该角色！")
    
    # 检查目标部门权限
    if params.department_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), params.department_id)
        if not can_access:
            return ResponseUtil.error(msg="修改失败,无权限操作目标部门！")
    
    old_code = role.code
    
    # 更新角色信息
    if params.code:
        # 检查新编码是否已存在
        existing = await SystemRole.get_or_none(code=params.code, is_del=False)
        if existing and str(existing.id) != id:
            return ResponseUtil.error(msg="角色编码已存在！")
        role.code = params.code
    if params.name:
        role.name = params.name
    if params.description is not None:
        role.description = params.description
    if params.status is not None:
        role.status = params.status
    if params.department_id:
        department = await SystemDepartment.get_or_none(id=params.department_id, is_del=False)
        if department:
            role.department_id = department.id
        else:
            role.department_id = None
    
    await role.save()
    
    # 如果角色编码变更，需要迁移 Casbin 中的策略
    if params.code and params.code != old_code:
        # 获取旧角色的所有权限
        old_permissions = await CasbinEnforcer.get_permissions_for_role(old_code)
        old_users = await CasbinEnforcer.get_users_for_role(old_code)
        
        # 删除旧角色
        await CasbinEnforcer.delete_role(old_code)
        
        # 为新角色添加权限
        for perm in old_permissions:
            obj = perm.get("obj", "")
            act = perm.get("act", "")
            if act in ("menu", "button"):
                await CasbinEnforcer.add_permission_for_role(params.code, obj, act)
            else:
                await CasbinEnforcer.add_api_permission_for_role(params.code, obj, act)
        
        # 迁移用户关联
        for user in old_users:
            await CasbinEnforcer.add_role_for_user(user, params.code)
    
    await clear_role_cache(request)
    return ResponseUtil.success(msg="修改角色成功！")


@roleAPI.get("/info/{id}", response_model=GetRoleInfoResponse, response_class=JSONResponse, summary="查询角色详情")
@Log(title="查询角色详情", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:info", "GET:/role/info/*"])
async def get_role_info(request: Request, id: str = Path(..., description="角色ID"),
                        current_user: dict = Depends(AuthController.get_current_user)):
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), dept_id)
        if not can_access:
            return ResponseUtil.error(msg="无权限查看该角色！")
    
    role_data = await SystemRole.filter(id=id, is_del=False).values(
        id="id",
        created_at="created_at",
        updated_at="updated_at",
        code="code",
        name="name",
        status="status",
        description="description",
        department_id="department_id",
        department_name="department__name",
        department_principal="department__principal",
        department_phone="department__phone",
        department_email="department__email",
    )
    
    if role_data:
        # 从 Casbin 获取角色权限
        role_info = role_data[0]
        permissions = await CasbinEnforcer.get_permissions_for_role(role.code)
        menu_ids = await CasbinEnforcer.get_menu_permissions_for_role(role.code)
        button_ids = await CasbinEnforcer.get_button_permissions_for_role(role.code)
        api_permissions = await CasbinEnforcer.get_api_permissions_for_role(role.code)
        
        role_info["permissions"] = permissions
        role_info["menu_ids"] = menu_ids
        role_info["button_ids"] = button_ids
        role_info["api_permissions"] = api_permissions
        return ResponseUtil.success(data=role_info)
    
    return ResponseUtil.error(msg="查询角色详情失败！")


@roleAPI.get("/list", response_model=GetRoleListResponse, response_class=JSONResponse, summary="查询角色列表")
@Log(title="查询角色列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:list", "GET:/role/list"])
async def get_role_list(
        request: Request,
        page: int = Query(1, description="页码"),
        pageSize: int = Query(10, description="每页数量"),
        name: Optional[str] = Query(None, description="角色名称"),
        code: Optional[str] = Query(None, description="角色编码"),
        description: Optional[str] = Query(None, description="角色描述"),
        department_id: Optional[str] = Query(None, description="所属部门ID"),
        department_ids: Optional[str] = Query(None, description="多个部门ID，逗号分隔"),
        status: Optional[int] = Query(None, description="状态"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    user_id = current_user.get("id")
    
    filterArgs = {
        f'{k}__contains': v for k, v in {
            "name": name,
            "code": code,
            "description": description,
        }.items() if v
    }
    
    if status is not None:
        filterArgs["status"] = status
    
    # 获取用户的数据权限范围
    data_scope = await CasbinEnforcer.get_data_scope(str(user_id))
    
    # 根据数据权限范围过滤
    if department_ids:
        # 如果指定了多个部门ID，查询这些部门的角色（需要在权限范围内）
        dept_id_list = [dept_id.strip() for dept_id in department_ids.split(',') if dept_id.strip()]
        if data_scope["scope"] != DataScope.ALL:
            # 过滤出有权限的部门
            dept_id_list = [d for d in dept_id_list if d in data_scope["department_ids"]]
        if dept_id_list:
            filterArgs["department__id__in"] = dept_id_list
        else:
            # 没有权限的部门，返回空
            return ResponseUtil.success(data={
                "result": [],
                "total": 0,
                "page": page,
                "pageSize": pageSize
            })
    elif department_id:
        # 如果指定了单个部门ID，检查权限
        if data_scope["scope"] != DataScope.ALL and department_id not in data_scope["department_ids"]:
            return ResponseUtil.error(msg="无权限查看该部门的角色！")
        filterArgs["department__id"] = department_id
    else:
        # 如果没有指定部门ID，根据数据权限范围查询
        if data_scope["scope"] == DataScope.ALL:
            # 全部数据权限，不限制部门
            pass
        elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
            # 部门及下属部门数据权限
            filterArgs["department__id__in"] = list(data_scope["department_ids"])
        else:
            # 仅本人数据权限，只能看自己部门的角色
            if data_scope["department_id"]:
                filterArgs["department__id"] = data_scope["department_id"]
            else:
                return ResponseUtil.success(data={
                    "result": [],
                    "total": 0,
                    "page": page,
                    "pageSize": pageSize
                })
    
    total = await SystemRole.filter(**filterArgs, is_del=False).count()
    data = await SystemRole.filter(**filterArgs, is_del=False).offset(
        (page - 1) * pageSize).limit(
        pageSize).values(
        id="id",
        created_at="created_at",
        updated_at="updated_at",
        code="code",
        name="name",
        status="status",
        description="description",
        department_id="department__id",
        department_name="department__name",
        department_principal="department__principal",
        department_phone="department__phone",
        department_email="department__email",
    )

    return ResponseUtil.success(data={
        "result": data,
        "total": total,
        "page": page,
        "pageSize": pageSize
    })


@roleAPI.post("/addPermission/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="新增角色权限")
@Log(title="新增角色权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["role:btn:addPermission", "POST:/role/addPermission/*"])
async def add_role_permission(request: Request, params: AddRolePermissionParams,
                              id: str = Path(..., description="角色ID"),
                              current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), dept_id)
        if not can_access:
            return ResponseUtil.error(msg="无权限操作该角色！")
    
    # 获取所有有效权限ID
    valid_permissions = await SystemPermission.filter(
        id__in=params.permission_ids,
        is_del=False
    ).all()
    
    # 同步权限到 Casbin
    await sync_role_permissions_to_casbin(role.code, [str(p.id) for p in valid_permissions])
    
    await clear_role_cache(request)
    return ResponseUtil.success(msg="新增角色权限成功！")


@roleAPI.delete("/deletePermission/{id}", response_model=BaseResponse, response_class=JSONResponse,
                summary="删除角色权限")
@roleAPI.post("/deletePermission/{id}", response_model=BaseResponse, response_class=JSONResponse,
              summary="删除角色权限")
@Log(title="删除角色权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["role:btn:deletePermission", "DELETE,POST:/role/deletePermission/*"])
async def delete_role_permission(request: Request, 
                                 role_id: str = Query(..., description="角色ID"),
                                 permission_id: str = Query(..., description="权限ID"),
                                 id: str = Path(..., description="兼容旧接口，可忽略"),
                                 current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    
    role = await SystemRole.get_or_none(id=role_id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    if role.department_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), str(role.department_id))
        if not can_access:
            return ResponseUtil.error(msg="无权限操作该角色！")
    
    permission = await SystemPermission.get_or_none(id=permission_id, is_del=False)
    if not permission:
        return ResponseUtil.error(msg="权限不存在！")
    
    # 从 Casbin 移除权限
    if permission.menu_type == PermissionType.MENU:
        await CasbinEnforcer.remove_permission_for_role(role.code, permission_id, "menu")
    elif permission.menu_type == PermissionType.BUTTON:
        await CasbinEnforcer.remove_permission_for_role(role.code, permission_id, "button")
    elif permission.menu_type == PermissionType.API and permission.api_path and permission.api_method:
        # 处理API权限删除 - 需要找到Casbin中实际存储的格式
        api_path = permission.api_path
        
        # 获取当前角色的所有API权限，找到匹配的记录
        current_api_perms = await CasbinEnforcer.get_api_permissions_for_role(role.code)
        
        # 查找匹配的API权限记录
        target_method = None
        for api_perm in current_api_perms:
            if api_perm["path"] == api_path:
                # 找到匹配的路径，使用Casbin中实际存储的方法格式
                if isinstance(api_perm["method"], list):
                    target_method = ",".join(api_perm["method"])
                else:
                    target_method = api_perm["method"]
                break
        
        if target_method:
            await CasbinEnforcer.remove_api_permission_for_role(role.code, api_path, target_method)
        else:
            # 如果没找到，尝试使用normalize后的格式
            method_str = normalize_api_method(permission.api_method)
            await CasbinEnforcer.remove_api_permission_for_role(role.code, api_path, method_str)
    
    await clear_role_cache(request)
    return ResponseUtil.success(msg="删除角色权限成功！")


@roleAPI.put("/updatePermission/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="修改角色权限")
@roleAPI.post("/updatePermission/{id}", response_model=BaseResponse, response_class=JSONResponse,
              summary="修改角色权限")
@Log(title="修改角色权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["role:btn:updatePermission", "PUT,POST:/role/updatePermission/*"])
async def update_role_permission(request: Request, params: AddRolePermissionParams,
                                 id: str = Path(..., description="角色ID"),
                                 current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), dept_id)
        if not can_access:
            return ResponseUtil.error(msg="无权限操作该角色！")
    
    # 获取当前角色在Casbin中实际存储的权限（不做任何推导）
    current_menu_ids = set(await CasbinEnforcer.get_menu_permissions_for_role(role.code))
    current_button_ids = set(await CasbinEnforcer.get_button_permissions_for_role(role.code))
    current_api_permissions = await CasbinEnforcer.get_api_permissions_for_role(role.code)
    
    # 将当前API权限转换为权限ID集合（严格匹配，不推导）
    current_api_ids = set()
    for api_perm in current_api_permissions:
        api_path = api_perm["path"]
        api_method = api_perm["method"]
        
        # 标准化Casbin中的方法格式，确保排序一致
        if isinstance(api_method, list):
            casbin_method_str = ",".join(sorted(api_method))
        else:
            casbin_method_str = ",".join(sorted(api_method.split(",") if "," in api_method else [api_method]))
        
        # 查找匹配的权限记录（严格匹配，不包含父子关系推导）
        matching_perms = await SystemPermission.filter(
            api_path=api_path,
            menu_type=PermissionType.API,
            is_del=False
        ).all()
        
        for perm in matching_perms:
            # 使用统一的方法格式化进行比较
            perm_method_str = normalize_api_method(perm.api_method)
            
            # 检查方法字符串是否匹配（考虑不同的排序方式）
            # 将两个字符串都转换为集合进行比较，避免排序问题
            casbin_method_set = set(casbin_method_str.split(","))
            perm_method_set = set(perm_method_str.split(","))
            
            if casbin_method_set == perm_method_set:
                current_api_ids.add(str(perm.id))
                break
    
    # 当前所有实际存储的权限ID（不包含推导的权限）
    current_all_ids = current_menu_ids | current_button_ids | current_api_ids
    
    # 新的权限ID集合（前端传来的所有权限，包括半选的）
    new_permission_ids = set(params.permission_ids)
    
    # 如果传入空数组，直接清除角色的所有权限
    if not params.permission_ids:
        # 删除角色的所有权限
        await CasbinEnforcer.delete_role(role.code)
        # 重新加载 Casbin 策略
        await CasbinEnforcer.reload_policy()
        await clear_role_cache(request)
        return ResponseUtil.success(msg="修改角色权限成功！")
    
    # 使用集合计算需要添加和删除的权限（严格按照ID操作，不做父子关系推导）
    to_add = new_permission_ids - current_all_ids
    to_remove = current_all_ids - new_permission_ids
    
    # 获取需要操作的权限详情
    if to_add or to_remove:
        all_operation_ids = list(to_add | to_remove)
        operation_permissions = await SystemPermission.filter(
            id__in=all_operation_ids,
            is_del=False
        ).all()
        
        # 严格按照权限ID进行添加和删除操作，不做父子关系推导
        for perm in operation_permissions:
            perm_id = str(perm.id)
            
            if perm_id in to_add:
                # 添加权限（严格按照权限类型添加，不推导父子关系）
                if perm.menu_type == PermissionType.MENU:
                    await CasbinEnforcer.add_permission_for_role(role.code, perm_id, "menu")
                elif perm.menu_type == PermissionType.BUTTON:
                    await CasbinEnforcer.add_permission_for_role(role.code, perm_id, "button")
                elif perm.menu_type == PermissionType.API and perm.api_path and perm.api_method:
                    # 处理API权限（使用统一的方法格式化）
                    method_str = normalize_api_method(perm.api_method)
                    await CasbinEnforcer.add_api_permission_for_role(role.code, perm.api_path, method_str)
            
            elif perm_id in to_remove:
                # 删除权限（严格按照权限类型删除，不推导父子关系）
                if perm.menu_type == PermissionType.MENU:
                    await CasbinEnforcer.remove_permission_for_role(role.code, perm_id, "menu")
                elif perm.menu_type == PermissionType.BUTTON:
                    await CasbinEnforcer.remove_permission_for_role(role.code, perm_id, "button")
                elif perm.menu_type == PermissionType.API and perm.api_path and perm.api_method:
                    # 处理API权限删除 - 需要找到Casbin中实际存储的格式
                    api_path = perm.api_path
                    
                    # 获取当前角色的所有API权限，找到匹配的记录
                    current_api_perms = await CasbinEnforcer.get_api_permissions_for_role(role.code)
                    
                    # 查找匹配的API权限记录
                    target_method = None
                    for api_perm in current_api_perms:
                        if api_perm["path"] == api_path:
                            # 找到匹配的路径，使用Casbin中实际存储的方法格式
                            if isinstance(api_perm["method"], list):
                                target_method = ",".join(api_perm["method"])
                            else:
                                target_method = api_perm["method"]
                            break
                    
                    if target_method:
                        await CasbinEnforcer.remove_api_permission_for_role(role.code, api_path, target_method)
                    else:
                        # 如果没找到，尝试使用normalize后的格式
                        method_str = normalize_api_method(perm.api_method)
                        await CasbinEnforcer.remove_api_permission_for_role(role.code, api_path, method_str)
    
    # 重新加载 Casbin 策略以确保缓存更新
    await CasbinEnforcer.reload_policy()
    
    await clear_role_cache(request)
    return ResponseUtil.success(msg="修改角色权限成功！")


@roleAPI.get("/permissionInfo/{id}", response_model=GetRolePermissionInfoResponse, response_class=JSONResponse,
             summary="获取角色权限信息")
@Log(title="获取角色权限信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:permissionInfo", "GET:/role/permissionInfo/*"])
async def get_role_permission_info(request: Request, 
                                   role_id: str = Query(..., description="角色ID"),
                                   permission_id: str = Query(..., description="权限ID"),
                                   id: str = Path(..., description="兼容旧接口，可忽略"),
                                   current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    
    role = await SystemRole.get_or_none(id=role_id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    if role.department_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), str(role.department_id))
        if not can_access:
            return ResponseUtil.error(msg="无权限查看该角色权限！")
    
    permission = await SystemPermission.get_or_none(id=permission_id, is_del=False)
    if not permission:
        return ResponseUtil.error(msg="权限不存在！")
    
    # 检查角色是否拥有该权限
    has_permission = False
    perm_type = None
    
    if permission.menu_type == PermissionType.MENU:
        perm_type = "menu"
        has_permission = await CasbinEnforcer.check_permission(role.code, permission_id, "menu")
    elif permission.menu_type == PermissionType.BUTTON:
        perm_type = "button"
        has_permission = await CasbinEnforcer.check_permission(role.code, permission_id, "button")
    elif permission.menu_type == PermissionType.API and permission.api_path:
        perm_type = "api"
        # 处理api_method字段，使用统一的方法格式化
        method_str = normalize_api_method(permission.api_method)
        has_permission = await CasbinEnforcer.check_permission(role.code, permission.api_path, method_str)
    
    data = {
        "role_id": str(role.id),
        "role_name": role.name,
        "role_code": role.code,
        "permission_id": str(permission.id),
        "permission_name": permission.title,
        "permission_auth": permission.authMark,
        "permission_type": permission.menu_type,
        "perm_type": perm_type,
        "has_permission": has_permission,
        "api_path": permission.api_path,
        "api_method": permission.api_method,
        "data_scope": permission.data_scope,
    }
    
    return ResponseUtil.success(data=data)


@roleAPI.get("/permissionList/{id}", response_model=GetRolePermissionListResponse, response_class=JSONResponse,
             summary="获取角色权限列表")
@Log(title="获取角色权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:permissionList", "GET:/role/permissionList/*"])
async def get_role_permission_list(request: Request, id: str = Path(..., description="角色ID"),
                                   current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")
    
    # 使用 Casbin 检查部门数据权限
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), dept_id)
        if not can_access:
            return ResponseUtil.error(msg="无权限查看该角色权限！")
    
    # 从 Casbin 获取角色的实际权限（不做父子关系计算）
    menu_ids = await CasbinEnforcer.get_menu_permissions_for_role(role.code)
    button_ids = await CasbinEnforcer.get_button_permissions_for_role(role.code)
    api_permissions = await CasbinEnforcer.get_api_permissions_for_role(role.code)
    
    # 获取API权限对应的权限ID
    api_permission_ids = []
    if api_permissions:
        # 根据API路径和方法查找对应的权限ID
        for api_perm in api_permissions:
            api_path = api_perm["path"]
            api_method = api_perm["method"]
            
            # 标准化Casbin中的方法格式，确保排序一致
            if isinstance(api_method, list):
                casbin_method_str = ",".join(sorted(api_method))
            else:
                casbin_method_str = ",".join(sorted(api_method.split(",") if "," in api_method else [api_method]))
            
            # 查找匹配的权限记录
            matching_perms = await SystemPermission.filter(
                api_path=api_path,
                menu_type=PermissionType.API,
                is_del=False
            ).all()
            
            for perm in matching_perms:
                # 使用统一的方法格式化进行比较
                perm_method_str = normalize_api_method(perm.api_method)
                
                # 检查方法字符串是否匹配（考虑不同的排序方式）
                # 将两个字符串都转换为集合进行比较，避免排序问题
                casbin_method_set = set(casbin_method_str.split(","))
                perm_method_set = set(perm_method_str.split(","))
                
                if casbin_method_set == perm_method_set:
                    api_permission_ids.append(str(perm.id))
                    break
    
    # 返回实际拥有的权限ID，让前端计算显示状态
    actual_permission_ids = menu_ids + button_ids + api_permission_ids
    
    return ResponseUtil.success(data={
        "actual_permission_ids": actual_permission_ids,  # 实际拥有的权限ID
        "menu_ids": menu_ids,
        "button_ids": button_ids,
        "api_permission_ids": api_permission_ids,
        "api_permissions": api_permissions
    })
