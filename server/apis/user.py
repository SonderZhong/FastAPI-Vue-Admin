# _*_ coding : UTF-8 _*_
# @Time : 2025/08/23 23:18
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : user.py
# @Software : PyCharm
# @Comment : 用户管理 API - 完全使用 Casbin 管理权限（方案C）
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Path, Query, File, UploadFile, Form
from starlette.responses import JSONResponse
from models import SystemUser, SystemDepartment, SystemUserRole, SystemLoginLog, SystemOperationLog
from models.permission import PermissionType
from models import SystemPermission, SystemRole
from schemas.common import BaseResponse, DeleteListParams
from schemas.user import AddUserParams, UpdateUserParams, GetUserInfoResponse, GetUserListResponse, \
    AddUserRoleParams, UpdateUserRoleParams, GetUserRoleInfoResponse, GetUserPermissionListResponse, \
    ResetPasswordParams, UpdateBaseUserInfoParams, UploadFileResponse, GetUserRoleListResponse
from utils.casbin import CasbinEnforcer, DataScope
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil
from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from exceptions.exception import ServiceException
from utils.password import PasswordUtil
from utils.log import logger

userAPI = APIRouter(prefix="/user")


@userAPI.post("/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增用户")
@Log(title="新增用户", operation_type=OperationType.INSERT)
@Auth(permission_list=["user:btn:addUser", "POST:/user/add"])
async def add_user(
        request: Request,
        params: AddUserParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    if await SystemUser.get_or_none(username=params.username, is_del=False):
        return ResponseUtil.error(msg="添加失败，用户已存在！")
    
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    if params.department_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), params.department_id)
        if not can_access:
            return ResponseUtil.error(msg="添加失败，无权限操作该部门！")
    
    params.password = await PasswordUtil.get_password_hash(input_password=params.password)
    department = await SystemDepartment.get_or_none(id=params.department_id, is_del=False)
    if await SystemUser.create(
            username=params.username,
            password=params.password,
            nickname=params.nickname,
            phone=params.phone,
            email=params.email,
            gender=params.gender,
            department=department,
            status=params.status,
            user_type=params.user_type,
    ):
        return ResponseUtil.success(msg="添加成功！")
    else:
        return ResponseUtil.error(msg="添加失败！")


@userAPI.delete("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除用户")
@userAPI.post("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除用户")
@Log(title="删除用户", operation_type=OperationType.DELETE)
@Auth(permission_list=["user:btn:deleteUser", "DELETE,POST:/user/delete/*"])
async def delete_user(
        request: Request,
        id: str = Path(..., description="用户ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="删除失败，用户不存在！")
    
    # 使用 Casbin 检查数据权限
    operator_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="删除失败，无权限操作该用户！")
    
    user.is_del = True
    await user.save()
    
    # 移除用户角色
    await SystemUserRole.filter(user_id=user.id, is_del=False).update(is_del=True)
    # 移除用户登录日志
    await SystemLoginLog.filter(user_id=user.id, is_del=False).update(is_del=True)
    # 移除用户操作日志
    await SystemOperationLog.filter(operator_id=user.id, is_del=False).update(is_del=True)
    
    # 删除 Casbin 中该用户的所有角色关联
    await CasbinEnforcer.delete_user(id)
    
    # 更新用户信息缓存
    if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{id}'):
        await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{id}')
    # 更新用户路由缓存
    if await request.app.state.redis.get(f'{RedisKeyConfig.USER_ROUTES.key}:{id}'):
        await request.app.state.redis.delete(f'{RedisKeyConfig.USER_ROUTES.key}:{id}')
    
    return ResponseUtil.success(msg="删除成功！")


@userAPI.delete("/deleteUserList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除用户")
@userAPI.post("/deleteUserList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除用户")
@Log(title="批量删除用户", operation_type=OperationType.DELETE)
@Auth(permission_list=["user:btn:deleteUser", "DELETE,POST:/user/deleteUserList"])
async def delete_user_list(
        request: Request,
        params: DeleteListParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    operator_id = current_user.get("id")
    deleted_count = 0
    
    for user_id in set(params.ids):
        # 使用 Casbin 检查数据权限
        can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), user_id)
        if can_access:
            user = await SystemUser.get_or_none(id=user_id, is_del=False)
            if user:
                user.is_del = True
                await user.save()
                # 删除 Casbin 中该用户的所有角色关联
                await CasbinEnforcer.delete_user(user_id)
                deleted_count += 1
    
    return ResponseUtil.success(msg=f"删除成功，共删除 {deleted_count} 个用户！")


@userAPI.put("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新用户")
@userAPI.post("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新用户")
@Log(title="更新用户", operation_type=OperationType.UPDATE)
@Auth(permission_list=["user:btn:updateUser", "PUT,POST:/user/update/*"])
async def update_user(
        request: Request,
        params: UpdateUserParams,
        id: str = Path(..., description="用户ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="更新失败，用户不存在！")
    
    # 使用 Casbin 检查数据权限
    operator_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="更新失败，无权限操作该用户！")
    
    # 如果要更换部门，检查目标部门权限
    if params.department_id:
        can_access_dept = await CasbinEnforcer.can_access_department_data(str(operator_id), params.department_id)
        if not can_access_dept:
            return ResponseUtil.error(msg="更新失败，无权限操作目标部门！")
    
    user.username = params.username
    user.nickname = params.nickname
    user.phone = params.phone
    user.email = params.email
    user.gender = params.gender
    user.status = params.status
    user.user_type = params.user_type
    if department := await SystemDepartment.get_or_none(id=params.department_id, is_del=False):
        user.department = department
    else:
        user.department = None
    await user.save()
    if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{id}'):
        await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{id}')
    return ResponseUtil.success(msg="更新成功！")


@userAPI.get("/info/{id}", response_class=JSONResponse, response_model=GetUserInfoResponse, summary="获取用户信息")
@Log(title="获取用户信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["user:btn:Userinfo", "GET:/user/info/*"])
async def get_user_info(request: Request, id: str = Path(..., description="用户ID"),
                        current_user: dict = Depends(AuthController.get_current_user)):
    if user := await SystemUser.get_or_none(id=id, is_del=False):
        user = await user.first().values(
            id="id",
            created_at="created_at",
            updated_at="updated_at",
            username="username",
            email="email",
            phone="phone",
            nickname="nickname",
            gender="gender",
            status="status",
            user_type="user_type",
            avatar="avatar",
            department_id="department__id",
            department_name="department__name",
        )
        return ResponseUtil.success(data=user)
    else:
        return ResponseUtil.error(msg="用户不存在！")


@userAPI.get("/list", response_class=JSONResponse, response_model=GetUserListResponse, summary="获取用户列表")
@Log(title="获取用户列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["user:btn:userList", "GET:/user/list"])
async def get_user_list(
        request: Request,
        page: int = Query(default=1, description="当前页码"),
        pageSize: int = Query(default=10, description="每页数量"),
        username: Optional[str] = Query(default=None, description="用户名"),
        nickname: Optional[str] = Query(default=None, description="昵称"),
        phone: Optional[str] = Query(default=None, description="手机号"),
        email: Optional[str] = Query(default=None, description="邮箱"),
        gender: Optional[str] = Query(default=None, description="性别"),
        status: Optional[str] = Query(default=None, description="状态"),
        department_id: Optional[str] = Query(default=None, description="部门ID"),
        department_ids: Optional[str] = Query(default=None, description="多个部门ID，逗号分隔"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    operator_id = current_user.get("id")
    
    # 获取用户的数据权限范围
    data_scope = await CasbinEnforcer.get_data_scope(str(operator_id))
    
    filterArgs = {
        f'{k}__contains': v for k, v in {
            'username': username,
            'nickname': nickname,
            'phone': phone,
            'email': email,
            'gender': gender,
            'status': status
        }.items() if v is not None
    }
    
    # 部门过滤逻辑
    if department_ids:
        # 如果指定了多个部门ID，查询这些部门的用户（需要在权限范围内）
        dept_id_list = [dept_id.strip() for dept_id in department_ids.split(',') if dept_id.strip()]
        if data_scope["scope"] != DataScope.ALL:
            # 过滤出有权限的部门
            dept_id_list = [d for d in dept_id_list if d in data_scope["department_ids"]]
        if dept_id_list:
            filterArgs["department_id__in"] = dept_id_list
        else:
            return ResponseUtil.success(data={
                "result": [],
                "total": 0,
                "page": page,
                "pageSize": pageSize
            })
    elif department_id:
        # 如果指定了单个部门ID，检查权限
        if data_scope["scope"] != DataScope.ALL and department_id not in data_scope["department_ids"]:
            return ResponseUtil.error(msg="无权限查看该部门的用户！")
        filterArgs["department_id"] = department_id
    else:
        # 如果没有指定部门ID，根据数据权限范围查询
        if data_scope["scope"] == DataScope.ALL:
            # 全部数据权限，不限制部门
            pass
        elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
            # 部门及下属部门数据权限
            filterArgs["department_id__in"] = list(data_scope["department_ids"])
        else:
            # 仅本人数据权限，只能看自己
            filterArgs["id"] = operator_id
    
    total = await SystemUser.filter(**filterArgs, is_del=False).count()
    result = await SystemUser.filter(**filterArgs, is_del=False).offset((page - 1) * pageSize).limit(pageSize).values(
        id="id",
        created_at="created_at",
        updated_at="updated_at",
        username="username",
        email="email",
        phone="phone",
        nickname="nickname",
        avatar="avatar",
        gender="gender",
        status="status",
        user_type="user_type",
        department_id="department__id",
        department_name="department__name",
    )
    return ResponseUtil.success(data={
        "result": result,
        "total": total,
        "page": page,
        "pageSize": pageSize
    })


@userAPI.post("/addRole", response_model=BaseResponse, response_class=JSONResponse, summary="分配用户角色")
@Log(title="分配用户角色", operation_type=OperationType.INSERT)
@Auth(permission_list=["user:btn:addRole", "POST:/user/addRole"])
async def add_user_role(request: Request, params: AddUserRoleParams,
                        current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), params.user_id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")
    
    # 获取用户已有角色
    userRoles = await SystemUserRole.filter(
        user_id=params.user_id, is_del=False
    ).prefetch_related("role").all()
    
    existing_role_ids = [str(ur.role_id) for ur in userRoles]
    
    # 利用集合找到需要添加的角色
    addRoles = set(params.role_ids).difference(set(existing_role_ids))
    # 利用集合找到需要删除的角色
    deleteRoles = set(existing_role_ids).difference(set(params.role_ids))

    # 添加角色
    from models import SystemRole
    for role_id in addRoles:
        # 先检查是否存在已软删除的记录
        existing_role = await SystemUserRole.filter(
            user_id=params.user_id, 
            role_id=role_id,
            is_del=True
        ).first()
        
        if existing_role:
            # 如果存在软删除的记录，则恢复它
            existing_role.is_del = False
            await existing_role.save()
        else:
            # 如果不存在软删除记录，则创建新记录
            await SystemUserRole.create(
                user_id=params.user_id,
                role_id=role_id
            )
        
        # 同步到 Casbin
        role = await SystemRole.get_or_none(id=role_id, is_del=False)
        if role:
            await CasbinEnforcer.add_role_for_user(params.user_id, role.code)
    
    # 删除角色
    for role_id in deleteRoles:
        await SystemUserRole.filter(
            user_id=params.user_id,
            role_id=role_id,
            is_del=False
        ).update(is_del=True)
        
        # 从 Casbin 移除
        role = await SystemRole.get_or_none(id=role_id, is_del=False)
        if role:
            await CasbinEnforcer.remove_role_for_user(params.user_id, role.code)
    
    if await request.app.state.redis.get(
        f"{RedisKeyConfig.USER_INFO.key}:{params.user_id}"
    ):
        await request.app.state.redis.delete(
            f"{RedisKeyConfig.USER_INFO.key}:{params.user_id}"
        )
    return ResponseUtil.success(msg="修改成功！")

@userAPI.delete("/deleteRole/{id}", response_model=BaseResponse, response_class=JSONResponse,
                summary="删除用户角色")
@userAPI.post("/deleteRole/{id}", response_model=BaseResponse, response_class=JSONResponse,
              summary="删除用户角色")
@Log(title="删除用户角色", operation_type=OperationType.DELETE)
@Auth(permission_list=["user:btn:deleteRole", "DELETE,POST:/user/deleteRole/*"])
async def delete_user_role(request: Request, id: str = Path(description="用户角色ID"),
                           current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    
    # 先查询用户角色关联记录
    userRole = await SystemUserRole.get_or_none(id=id, is_del=False).prefetch_related("user", "role")
    if not userRole:
        return ResponseUtil.error(msg="删除失败,用户角色不存在！")
    
    user = await userRole.user
    role = await userRole.role
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), str(user.id))
    if not can_access:
        return ResponseUtil.error(msg="无权限操作！")
    
    userRole.is_del = True
    await userRole.save()
    
    # 从 Casbin 移除用户角色关联
    if role:
        await CasbinEnforcer.remove_role_for_user(str(user.id), role.code)
    
    if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
        await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
    
    return ResponseUtil.success(msg="删除成功！")


@userAPI.put("/updateRole", response_model=BaseResponse, response_class=JSONResponse, summary="修改用户角色")
@userAPI.post("/updateRole", response_model=BaseResponse, response_class=JSONResponse,
              summary="修改用户角色")
@Log(title="修改用户角色", operation_type=OperationType.UPDATE)
@Auth(permission_list=["user:btn:updateRole", "PUT,POST:/user/updateRole"])
async def update_user_role(request: Request, params: UpdateUserRoleParams,
                           current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), params.user_id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")
    
    # 获取用户已有角色
    userRoles = await SystemUserRole.filter(user_id=params.user_id, is_del=False).prefetch_related("role").all()
    existing_role_ids = [str(ur.role_id) for ur in userRoles]
    
    # 利用集合找到需要添加的角色
    addRoles = set(params.role_ids).difference(set(existing_role_ids))
    # 利用集合找到需要删除的角色
    deleteRoles = set(existing_role_ids).difference(set(params.role_ids))

    from models import SystemRole
    
    # 添加角色
    for role_id in addRoles:
        # 先检查是否存在已软删除的记录
        existing_role = await SystemUserRole.filter(
            user_id=params.user_id, 
            role_id=role_id,
            is_del=True
        ).first()
        
        if existing_role:
            # 如果存在软删除的记录，则恢复它
            existing_role.is_del = False
            await existing_role.save()
        else:
            # 如果不存在软删除记录，则创建新记录
            await SystemUserRole.create(
                user_id=params.user_id,
                role_id=role_id
            )
        
        # 同步到 Casbin
        role = await SystemRole.get_or_none(id=role_id, is_del=False)
        if role:
            await CasbinEnforcer.add_role_for_user(params.user_id, role.code)
    
    # 删除角色
    for role_id in deleteRoles:
        await SystemUserRole.filter(
            user_id=params.user_id,
            role_id=role_id,
            is_del=False
        ).update(is_del=True)
        
        # 从 Casbin 移除
        role = await SystemRole.get_or_none(id=role_id, is_del=False)
        if role:
            await CasbinEnforcer.remove_role_for_user(params.user_id, role.code)
    
    if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{params.user_id}'):
        await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{params.user_id}')
    return ResponseUtil.success(msg="修改成功！")


@userAPI.get("/roleInfo/{id}", response_model=GetUserRoleInfoResponse, response_class=JSONResponse,
             summary="获取用户角色信息")
@Log(title="获取用户角色信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["user:btn:roleInfo", "GET:/user/roleInfo/*"])
async def get_user_role_info(request: Request, id: str = Path(description="用户角色ID"),
                             current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    
    userRole = await SystemUserRole.get_or_none(id=id, is_del=False).prefetch_related("user")
    if not userRole:
        return ResponseUtil.error(msg="获取失败,用户角色不存在！")
    
    user = await userRole.user
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), str(user.id))
    if not can_access:
        return ResponseUtil.error(msg="无权限查看！")
    
    data = await SystemUserRole.filter(id=id, is_del=False).values(
        id="id",
        user_id="user__id",
        user_name="user__username",
        role_name="role__name",
        role_code="role__code",
        role_id="role__id",
        created_at="created_at",
        updated_at="updated_at"
    )
    
    if data:
        return ResponseUtil.success(data=data[0])
    return ResponseUtil.error(msg="获取失败,用户角色不存在！")


@userAPI.get("/roleList/{id}", response_model=GetUserRoleListResponse, response_class=JSONResponse,
             summary="获取用户角色列表")
@Log(title="获取用户角色列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["user:btn:roleList", "GET:/user/roleList/*"])
async def get_user_role_list(
        request: Request,
        id: str = Path(description="用户ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    operator_id = current_user.get("id")
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="无权限查看！")
    
    result = await SystemUserRole.filter(user_id=id, is_del=False).values(
        id="id",
        department_id="user__department__id",
        department_name="user__department__name",
        department_phone="user__department__phone",
        department_principal="user__department__principal",
        department_email="user__department__email",
        role_name="role__name",
        role_code="role__code",
        role_id="role__id",
        created_at="created_at",
        updated_at="updated_at"
    )
    
    # 获取 Casbin 中该用户的角色
    casbin_roles = await CasbinEnforcer.get_roles_for_user(id)
    
    return ResponseUtil.success(data={
        "result": result,
        "total": len(result),
        "page": 1,
        "pageSize": 10,
        "casbin_roles": casbin_roles
    })


@userAPI.get("/permissionList/{id}", response_class=JSONResponse, response_model=GetUserPermissionListResponse,
             summary="获取用户权限列表")
@Log(title="获取用户权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["user:btn:permissionList", "GET:/user/permissionList/*"])
async def get_user_permission_list(request: Request, id: str = Path(description="用户ID"),
                                   current_user: dict = Depends(AuthController.get_current_user)):
    # 获取当前操作者的用户类型，用于过滤权限
    # user_type: 0=超级管理员, 1=管理员, 2=部门管理员, 3=普通用户
    operator_user_type = current_user.get("user_type", 3)
    
    # 使用 Casbin 获取用户的所有权限
    user_permissions = await CasbinEnforcer.get_user_permissions(id)
    
    result = []
    
    # 获取菜单和按钮权限详情
    all_permission_ids = user_permissions["menus"] + user_permissions["buttons"]
    if all_permission_ids:
        # 根据操作者用户类型过滤: 只能看到 min_user_type >= 当前用户类型的权限
        permissions = await SystemPermission.filter(
            id__in=all_permission_ids,
            is_del=False,
            min_user_type__gte=operator_user_type
        ).all()
        
        # 获取角色信息
        role_codes = user_permissions["roles"]
        roles = await SystemRole.filter(code__in=role_codes, is_del=False).all()
        role_map = {r.code: {"id": str(r.id), "name": r.name} for r in roles}
        
        for perm in permissions:
            perm_id = str(perm.id)
            perm_type = "menu" if perm_id in user_permissions["menus"] else "button"
            
            # 找到授予该权限的角色
            for role_code in role_codes:
                if perm_type == "menu":
                    role_menus = await CasbinEnforcer.get_menu_permissions_for_role(role_code)
                    if perm_id in role_menus:
                        role_info = role_map.get(role_code, {})
                        result.append({
                            "permission_id": perm.id,
                            "permission_name": perm.title,
                            "permission_auth": perm.authMark,
                            "permission_type": perm.menu_type,
                            "parent_id": str(perm.parent_id) if perm.parent_id else None,
                            "role_id": role_info.get("id"),
                            "role_name": role_info.get("name"),
                            "perm_type": perm_type,
                        })
                        break
                else:
                    role_buttons = await CasbinEnforcer.get_button_permissions_for_role(role_code)
                    if perm_id in role_buttons:
                        role_info = role_map.get(role_code, {})
                        result.append({
                            "permission_id": perm.id,
                            "permission_name": perm.title,
                            "permission_auth": perm.authMark,
                            "permission_type": perm.menu_type,
                            "parent_id": str(perm.parent_id) if perm.parent_id else None,
                            "role_id": role_info.get("id"),
                            "role_name": role_info.get("name"),
                            "perm_type": perm_type,
                        })
                        break
    
    # 处理API权限
    api_permissions = user_permissions.get("apis", [])
    if api_permissions and role_codes:
        roles = await SystemRole.filter(code__in=role_codes, is_del=False).all()
        role_map = {r.code: {"id": str(r.id), "name": r.name} for r in roles}
        
        # 导入normalize_api_method函数
        from apis.role import normalize_api_method
        
        # 为每个角色获取API权限
        for role_code in role_codes:
            role_api_permissions = await CasbinEnforcer.get_api_permissions_for_role(role_code)
            
            # 将API权限转换为权限ID
            for api_perm in role_api_permissions:
                api_path = api_perm["path"]
                api_method = api_perm["method"]
                
                # 标准化Casbin中的方法格式
                if isinstance(api_method, list):
                    casbin_method_str = ",".join(sorted(api_method))
                else:
                    casbin_method_str = ",".join(sorted(api_method.split(",") if "," in api_method else [api_method]))
                
                # 查找匹配的权限记录（根据操作者用户类型过滤）
                matching_perms = await SystemPermission.filter(
                    api_path=api_path,
                    menu_type=PermissionType.API,
                    is_del=False,
                    min_user_type__gte=operator_user_type
                ).all()
                
                for perm in matching_perms:
                    # 使用统一的方法格式化进行比较
                    perm_method_str = normalize_api_method(perm.api_method)
                    
                    # 检查方法字符串是否匹配（考虑不同的排序方式）
                    casbin_method_set = set(casbin_method_str.split(","))
                    perm_method_set = set(perm_method_str.split(","))
                    
                    if casbin_method_set == perm_method_set:
                        role_info = role_map.get(role_code, {})
                        result.append({
                            "permission_id": perm.id,
                            "permission_name": perm.title,
                            "permission_auth": perm.authMark,
                            "permission_type": perm.menu_type,
                            "parent_id": str(perm.parent_id) if perm.parent_id else None,
                            "role_id": role_info.get("id"),
                            "role_name": role_info.get("name"),
                            "api_path": perm.api_path,
                            "api_method": perm_method_str,
                            "perm_type": "api",
                        })
                        break
    
    return ResponseUtil.success(data={
        "result": result,
        "roles": user_permissions["roles"],
        "menus": user_permissions["menus"],
        "buttons": user_permissions["buttons"],
        "apis": user_permissions["apis"]
    })


@userAPI.post("/avatar/{id}", response_model=UploadFileResponse, response_class=JSONResponse, summary="上传用户头像")
@Log(title="上传用户头像", operation_type=OperationType.UPDATE)
@Auth(permission_list=["user:btn:uploadAvatar", "POST:/user/avatar/*"])
async def upload_user_avatar(
        request: Request,
        id: str = Path(description="用户ID"),
        file: UploadFile = File(...), 
        current_user: dict = Depends(AuthController.get_current_user)
):
    from utils.storage import StorageFactory
    from models.file import SystemFile, get_file_type
    
    operator_id = current_user.get("id")
    
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="用户不存在！")
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")
    
    # 文件类型验证
    image_mimetypes = [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/svg+xml',
        'image/bmp',
        'image/webp',
        'image/tiff'
    ]
    if file.content_type not in image_mimetypes:
        raise ServiceException(message="文件类型不支持，仅支持图片文件")
    
    # 文件大小验证 (5MB限制)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise ServiceException(message="文件大小不能超过5MB")
    
    # 重置文件指针
    await file.seek(0)
    
    try:
        # 使用统一存储服务上传
        dynamic_config = request.app.state.dynamic_config
        storage = await StorageFactory.create(dynamic_config)
        storage_type = await dynamic_config.get("upload_storage_type", "local")
        
        # 上传到 avatars 文件夹
        result = await storage.upload(file, "avatars")
        
        # 获取文件扩展名
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
        
        # 保存文件记录到 system_file 表
        file_record = await SystemFile.create(
            name=file.filename,
            key=result["key"],
            url=result["url"],
            size=result["size"],
            file_type=get_file_type(file.filename),
            mime_type=file.content_type,
            extension=ext,
            hash=result.get("hash"),
            storage_type=storage_type,
            folder="avatars",
            uploader_id=operator_id,
            uploader_name=current_user.get("username")
        )
        
        # 更新用户头像字段
        user.avatar = result["url"]
        await user.save()
        
        # 清除用户信息缓存
        if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
            await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
        
        return ResponseUtil.success(data={
            "id": str(user.id),
            "file_id": file_record.id,
            "filename": file.filename,
            "size": result["size"],
            "file_type": file.content_type,
            "avatar_url": result["url"],
            "upload_time": datetime.now().isoformat()
        }, msg="头像上传成功！")
        
    except Exception as e:
        logger.error(f"头像上传失败: {e}")
        return ResponseUtil.error(msg=f"头像上传失败: {str(e)}")


@userAPI.put("/resetPassword/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="重置用户密码")
@userAPI.post("/resetPassword/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="重置用户密码")
@Log(title="重置用户密码", operation_type=OperationType.UPDATE)
@Auth(permission_list=["user:btn:reset_password", "PUT,POST:/user/resetPassword/*"])
async def reset_user_password(request: Request, params: ResetPasswordParams, id: str = Path(description="用户ID"),
                              current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="用户不存在！")
    
    # 使用 Casbin 检查数据权限
    can_access = await CasbinEnforcer.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")
    
    # 加密新密码
    user.password = await PasswordUtil.get_password_hash(input_password=params.password)
    await user.save()
    
    # 清除用户信息缓存
    if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
        await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
        
    return ResponseUtil.success(msg="重置密码成功！")


@userAPI.put("/updateBaseUserInfo", response_model=BaseResponse, response_class=JSONResponse,
             summary="更新基础个人信息")
@userAPI.post("/updateBaseUserInfo", response_model=BaseResponse, response_class=JSONResponse,
              summary="更新基础个人信息")
@Log(title="更新基础个人信息", operation_type=OperationType.UPDATE)
async def update_base_userinfo(params: UpdateBaseUserInfoParams, request: Request,
                               current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    if user := await SystemUser.get_or_none(id=user_id, is_del=False):
        # 更新昵称和性别
        if params.name is not None:
            user.nickname = params.name
        user.gender = params.gender
        await user.save()
        
        # 清除用户信息缓存
        if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
            await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
            
        return ResponseUtil.success(msg="更新成功！")
    
    return ResponseUtil.error(msg="更新失败！")


@userAPI.put("/updatePassword", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新密码")
@userAPI.post("/updatePassword", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新密码")
@Log(title="用户更新密码", operation_type=OperationType.UPDATE)
async def update_user_password(request: Request, oldPassword: str = Form(description="用户旧密码"),
                               newPassword: str = Form(description="用户新密码"),
                               current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    if user := await SystemUser.get_or_none(id=user_id, is_del=False):
        # 验证旧密码
        if not await PasswordUtil.verify_password(plain_password=oldPassword, hashed_password=user.password):
            return ResponseUtil.error(msg="旧密码错误！")
        
        # 设置新密码
        user.password = await PasswordUtil.get_password_hash(input_password=newPassword)
        await user.save()
        
        # 清除用户信息缓存
        if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
            await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
            
        return ResponseUtil.success(msg="更新成功！")
    
    return ResponseUtil.error(msg="更新失败！")


@userAPI.put("/updatePhone", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新手机号")
@userAPI.post("/updatePhone", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新手机号")
@Log(title="用户更新手机号", operation_type=OperationType.UPDATE)
async def update_user_phone(request: Request, password: str = Form(description="用户密码"),
                            phone: str = Form(description="用户手机号"),
                            current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    if user := await SystemUser.get_or_none(id=user_id, is_del=False):
        # 验证密码
        if not await PasswordUtil.verify_password(plain_password=password, hashed_password=user.password):
            return ResponseUtil.error(msg="更改失败，请正确输入密码")
        
        # 检查手机号是否已被使用
        phone_exists = await SystemUser.filter(phone=phone, is_del=False).exclude(id=user_id).count()
        if phone_exists > 0:
            return ResponseUtil.error(msg=f"更改失败，手机号:{phone}已绑定其他账号！")
        
        # 更新手机号
        user.phone = phone
        await user.save()
        
        # 清除用户信息缓存
        if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
            await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
            
        return ResponseUtil.success(msg="更新成功！")
    
    return ResponseUtil.error(msg="更新失败！")


@userAPI.put("/updateEmail", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新邮箱")
@userAPI.post("/updateEmail", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新邮箱")
@Log(title="用户更新邮箱", operation_type=OperationType.UPDATE)
async def update_user_email(request: Request, password: str = Form(description="用户密码"),
                            email: str = Form(description="用户邮箱"),
                            current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    if user := await SystemUser.get_or_none(id=user_id, is_del=False):
        # 验证密码
        if not await PasswordUtil.verify_password(plain_password=password, hashed_password=user.password):
            return ResponseUtil.error(msg="更改失败，请正确输入密码")
        
        # 检查邮箱是否已被使用
        email_exists = await SystemUser.filter(email=email, is_del=False).exclude(id=user_id).count()
        if email_exists > 0:
            return ResponseUtil.error(msg=f"更改失败，邮箱:{email}已绑定其他账号！")
        
        # 更新邮箱
        user.email = email
        await user.save()
        
        # 清除用户信息缓存
        if await request.app.state.redis.get(f'{RedisKeyConfig.USER_INFO.key}:{user.id}'):
            await request.app.state.redis.delete(f'{RedisKeyConfig.USER_INFO.key}:{user.id}')
            
        return ResponseUtil.success(msg="更新成功！")
    
    return ResponseUtil.error(msg="更新失败！")
