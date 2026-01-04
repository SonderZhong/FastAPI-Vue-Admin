# _*_ coding : UTF-8 _*_
# @Time : 2025/12/26
# @Author : sonder
# @File : casbin.py
# @Comment : Casbin 权限管理 API - RBAC + 部门层级数据权限

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.responses import JSONResponse

from annotation.auth import AuthController
from annotation.log import Log, OperationType
from utils.casbin import CasbinEnforcer, DataScope, UserType
from utils.response import ResponseUtil

casbinAPI = APIRouter(prefix="/casbin")


# ==================== 请求模型 ====================

class PolicyParams(BaseModel):
    """策略参数"""
    sub: str  # 角色编码
    obj: str  # 资源路径
    act: str  # HTTP方法
    data_scope: int = DataScope.SELF_ONLY  # 数据权限范围


class RoleForUserParams(BaseModel):
    """用户角色关联参数"""
    user_id: str
    role_code: str


class CheckPermissionParams(BaseModel):
    """权限检查参数"""
    sub: str
    obj: str
    act: str


class CheckDataAccessParams(BaseModel):
    """数据访问检查参数"""
    target_user_id: Optional[str] = None
    target_dept_id: Optional[str] = None


class UpdateModelParams(BaseModel):
    """更新模型配置参数"""
    model_text: str


# ==================== 数据权限 API ====================

@casbinAPI.get(
    "/data-scope",
    response_class=JSONResponse,
    summary="获取当前用户的数据权限范围"
)
@Log(title="获取数据权限范围", operation_type=OperationType.SELECT)
async def get_data_scope(current_user: dict = Depends(AuthController.get_current_user)):
    """
    获取当前用户的数据权限范围
    
    返回:
    - scope: 数据范围 (1=全部, 2=本部门及下属, 3=仅本部门, 4=仅本人)
    - user_type: 用户类型 (0=超级管理员, 1=管理员, 2=部门管理员, 3=普通用户)
    - department_ids: 可访问的部门ID列表
    """
    user_id = current_user.get("id")
    scope = await CasbinEnforcer.get_data_scope(user_id)
    
    return ResponseUtil.success(data={
        "scope": scope["scope"],
        "scope_name": DataScope(scope["scope"]).name,
        "user_type": scope["user_type"],
        "user_type_name": UserType(scope["user_type"]).name,
        "department_id": scope["department_id"],
        "department_ids": list(scope["department_ids"])
    })


@casbinAPI.post(
    "/check-data-access",
    response_class=JSONResponse,
    summary="检查数据访问权限"
)
async def check_data_access(
    params: CheckDataAccessParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """
    检查当前用户是否可以访问指定用户或部门的数据
    """
    user_id = current_user.get("id")
    
    result = {"allowed": False}
    
    if params.target_user_id:
        result["can_access_user"] = await CasbinEnforcer.can_access_user_data(
            user_id, params.target_user_id
        )
        result["allowed"] = result["can_access_user"]
    
    if params.target_dept_id:
        result["can_access_dept"] = await CasbinEnforcer.can_access_department_data(
            user_id, params.target_dept_id
        )
        result["allowed"] = result.get("allowed", True) and result["can_access_dept"]
    
    return ResponseUtil.success(data=result)


# ==================== 策略管理 API ====================

@casbinAPI.get(
    "/policies",
    response_class=JSONResponse,
    summary="获取所有策略规则"
)
@Log(title="获取Casbin策略", operation_type=OperationType.SELECT)
async def get_policies(current_user: dict = Depends(AuthController.get_current_user)):
    """获取所有 p 类型的策略规则"""
    policies = CasbinEnforcer.get_all_policies()
    data = []
    for p in policies:
        item = {"sub": p[0], "obj": p[1], "act": p[2]}
        if len(p) > 3:
            item["data_scope"] = int(p[3]) if p[3].isdigit() else DataScope.SELF_ONLY
        data.append(item)
    return ResponseUtil.success(data=data)


@casbinAPI.post(
    "/policy",
    response_class=JSONResponse,
    summary="添加策略规则"
)
@Log(title="添加Casbin策略", operation_type=OperationType.INSERT)
async def add_policy(
    params: PolicyParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """
    添加策略规则
    
    - sub: 角色编码 (如 role_admin)
    - obj: 资源路径/权限ID (支持通配符，如 /api/users/*)
    - act: HTTP方法/权限类型 (menu/button 或 GET|POST|PUT|DELETE)
    - data_scope: 数据权限范围 (1=全部, 2=本部门及下属, 3=仅本部门, 4=仅本人)
    """
    # 判断是菜单/按钮权限还是 API 权限
    if params.act in ("menu", "button"):
        result = await CasbinEnforcer.add_permission_for_role(
            params.sub, params.obj, params.act
        )
    else:
        result = await CasbinEnforcer.add_api_permission_for_role(
            params.sub, params.obj, params.act
        )
    
    if result:
        return ResponseUtil.success(msg="策略添加成功")
    return ResponseUtil.error(msg="策略已存在或添加失败")


@casbinAPI.delete(
    "/policy",
    response_class=JSONResponse,
    summary="删除策略规则"
)
@Log(title="删除Casbin策略", operation_type=OperationType.DELETE)
async def remove_policy(
    params: PolicyParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """删除策略规则"""
    # 判断是菜单/按钮权限还是 API 权限
    if params.act in ("menu", "button"):
        result = await CasbinEnforcer.remove_permission_for_role(
            params.sub, params.obj, params.act
        )
    else:
        result = await CasbinEnforcer.remove_api_permission_for_role(
            params.sub, params.obj, params.act
        )
    
    if result:
        return ResponseUtil.success(msg="策略删除成功")
    return ResponseUtil.error(msg="策略不存在或删除失败")


# ==================== 用户角色关联 API ====================

@casbinAPI.get(
    "/groupings",
    response_class=JSONResponse,
    summary="获取所有用户-角色关联"
)
@Log(title="获取用户角色关联", operation_type=OperationType.SELECT)
async def get_groupings(current_user: dict = Depends(AuthController.get_current_user)):
    """获取所有 g 类型的用户-角色关联"""
    groupings = CasbinEnforcer.get_all_grouping_policies()
    data = [{"user_id": g[0], "role_code": g[1]} for g in groupings]
    return ResponseUtil.success(data=data)


@casbinAPI.post(
    "/role-for-user",
    response_class=JSONResponse,
    summary="为用户分配角色"
)
@Log(title="分配用户角色", operation_type=OperationType.INSERT)
async def add_role_for_user(
    params: RoleForUserParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """为用户分配角色"""
    result = await CasbinEnforcer.add_role_for_user(params.user_id, params.role_code)
    if result:
        return ResponseUtil.success(msg="角色分配成功")
    return ResponseUtil.error(msg="角色已分配或分配失败")


@casbinAPI.delete(
    "/role-for-user",
    response_class=JSONResponse,
    summary="移除用户角色"
)
@Log(title="移除用户角色", operation_type=OperationType.DELETE)
async def remove_role_for_user(
    params: RoleForUserParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """移除用户的角色"""
    result = await CasbinEnforcer.remove_role_for_user(params.user_id, params.role_code)
    if result:
        return ResponseUtil.success(msg="角色移除成功")
    return ResponseUtil.error(msg="角色关联不存在或移除失败")


@casbinAPI.get(
    "/roles/{user_id}",
    response_class=JSONResponse,
    summary="获取用户的所有角色"
)
@Log(title="获取用户角色", operation_type=OperationType.SELECT)
async def get_roles_for_user(
    user_id: str,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取指定用户的所有角色"""
    roles = await CasbinEnforcer.get_roles_for_user(user_id)
    return ResponseUtil.success(data=roles)


@casbinAPI.get(
    "/users/{role_code}",
    response_class=JSONResponse,
    summary="获取角色下的所有用户"
)
@Log(title="获取角色用户", operation_type=OperationType.SELECT)
async def get_users_for_role(
    role_code: str,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取指定角色下的所有用户"""
    users = await CasbinEnforcer.get_users_for_role(role_code)
    return ResponseUtil.success(data=users)


@casbinAPI.get(
    "/permissions/{role_code}",
    response_class=JSONResponse,
    summary="获取角色的所有权限"
)
@Log(title="获取角色权限", operation_type=OperationType.SELECT)
async def get_permissions_for_role(
    role_code: str,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """获取指定角色的所有权限"""
    permissions = await CasbinEnforcer.get_permissions_for_role(role_code)
    data = []
    for p in permissions:
        item = {"sub": p[0], "obj": p[1], "act": p[2]}
        if len(p) > 3:
            item["data_scope"] = int(p[3]) if p[3].isdigit() else DataScope.SELF_ONLY
        data.append(item)
    return ResponseUtil.success(data=data)


@casbinAPI.post(
    "/check",
    response_class=JSONResponse,
    summary="检查API权限"
)
async def check_permission(
    params: CheckPermissionParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """检查指定主体是否有权限访问资源"""
    result = await CasbinEnforcer.check_permission(params.sub, params.obj, params.act)
    return ResponseUtil.success(data={"allowed": result})


@casbinAPI.post(
    "/reload",
    response_class=JSONResponse,
    summary="重新加载策略"
)
@Log(title="重载Casbin策略", operation_type=OperationType.OTHER)
async def reload_policy(current_user: dict = Depends(AuthController.get_current_user)):
    """从数据库重新加载所有策略"""
    await CasbinEnforcer.reload_policy()
    return ResponseUtil.success(msg="策略重新加载成功")


@casbinAPI.delete(
    "/role/{role_code}",
    response_class=JSONResponse,
    summary="删除角色"
)
@Log(title="删除Casbin角色", operation_type=OperationType.DELETE)
async def delete_role(
    role_code: str,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """删除角色及其所有关联"""
    result = await CasbinEnforcer.delete_role(role_code)
    if result:
        return ResponseUtil.success(msg="角色删除成功")
    return ResponseUtil.error(msg="角色不存在或删除失败")


@casbinAPI.delete(
    "/user/{user_id}",
    response_class=JSONResponse,
    summary="清除用户的所有角色"
)
@Log(title="清除用户角色", operation_type=OperationType.DELETE)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """清除用户的所有角色关联"""
    result = await CasbinEnforcer.delete_user(user_id)
    if result:
        return ResponseUtil.success(msg="用户角色清除成功")
    return ResponseUtil.error(msg="用户不存在或清除失败")


# ==================== 模型配置管理 ====================

@casbinAPI.get(
    "/model",
    response_class=JSONResponse,
    summary="获取当前模型配置"
)
@Log(title="获取Casbin模型配置", operation_type=OperationType.SELECT)
async def get_model(current_user: dict = Depends(AuthController.get_current_user)):
    """获取当前 Casbin 模型配置文本"""
    model_text = await CasbinEnforcer.get_model_text()
    return ResponseUtil.success(data={"model_text": model_text})


@casbinAPI.put(
    "/model",
    response_class=JSONResponse,
    summary="更新模型配置"
)
@Log(title="更新Casbin模型配置", operation_type=OperationType.UPDATE)
async def update_model(
    params: UpdateModelParams,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """更新 Casbin 模型配置"""
    result = await CasbinEnforcer.update_model(params.model_text)
    if result:
        return ResponseUtil.success(msg="模型配置更新成功")
    return ResponseUtil.error(msg="模型配置更新失败，请检查配置格式")


@casbinAPI.post(
    "/reload-model",
    response_class=JSONResponse,
    summary="重新加载模型配置"
)
@Log(title="重载Casbin模型", operation_type=OperationType.OTHER)
async def reload_model(current_user: dict = Depends(AuthController.get_current_user)):
    """从数据库重新加载模型配置"""
    await CasbinEnforcer.reload_model()
    return ResponseUtil.success(msg="模型配置重新加载成功")


# ==================== 数据权限说明 ====================

@casbinAPI.get(
    "/data-scope-info",
    response_class=JSONResponse,
    summary="获取数据权限范围说明"
)
async def get_data_scope_info():
    """获取数据权限范围和用户类型的说明"""
    return ResponseUtil.success(data={
        "user_types": {
            UserType.SUPER_ADMIN: "超级管理员 - 可查看所有数据",
            UserType.ADMIN: "管理员 - 可管理多个部门和系统配置",
            UserType.DEPT_ADMIN: "部门管理员 - 可查看本部门及下属部门数据",
            UserType.NORMAL_USER: "普通用户 - 只能查看自己的数据"
        },
        "data_scopes": {
            DataScope.ALL: "全部数据",
            DataScope.DEPT_AND_CHILD: "本部门及下属部门",
            DataScope.DEPT_ONLY: "仅本部门",
            DataScope.SELF_ONLY: "仅本人"
        }
    })
