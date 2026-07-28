# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 01:10
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : role.py
# @Software : PyCharm
# @Comment : 角色管理 API - 数据库 RBAC + 数据权限
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request, File, UploadFile
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from modules import SystemRole, SystemPermission
from core.common import BaseResponse, DeleteListParams
from modules.role.schema import (
    AddRoleParams,
    UpdateRoleParams,
    UpdateRoleResponse,
    AddRolePermissionParams,
    GetRolePermissionInfoResponse,
    GetRolePermissionListResponse,
    GetRoleInfoResponse,
    GetRoleListResponse,
)
from modules.role.service import RoleService
from utils.permission import PermissionService, DataScope
from utils.response import ResponseUtil


roleAPI = APIRouter(prefix="/role")


@roleAPI.post(
    "/add", response_model=BaseResponse, response_class=JSONResponse, summary="新增角色"
)
@Log(title="新增角色", operation_type=OperationType.INSERT)
@Auth(permission_list=["role:btn:add"])
async def add_role(
    request: Request,
    params: AddRoleParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    can_access = await PermissionService.can_access_department_data(
        str(user_id), params.department_id
    )
    if not can_access:
        return ResponseUtil.error(msg="新增失败,无权限操作该部门！")

    success, msg = await RoleService.create_role(
        params.dict(exclude_unset=True),
        tenant_id=current_user.get("tenant_id"),
    )
    if success:
        await RoleService.clear_role_cache(request.app.state.redis)
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@roleAPI.delete(
    "/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除角色",
)
@roleAPI.post(
    "/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除角色",
)
@Log(title="删除角色", operation_type=OperationType.DELETE)
@Auth(permission_list=["role:btn:delete"])
async def delete_role(
    request: Request,
    id: str = Path(..., description="角色ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    user_id = current_user.get("id")
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), dept_id
        )
        if not can_access:
            return ResponseUtil.error(msg="删除失败,无权限操作该部门的角色！")

    await RoleService.delete(id)
    await RoleService.clear_role_cache(request.app.state.redis)
    return ResponseUtil.success(msg="删除角色成功！")


@roleAPI.delete(
    "/deleteList",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="批量删除角色",
)
@roleAPI.post(
    "/deleteList",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="批量删除角色",
)
@Log(title="批量删除角色", operation_type=OperationType.DELETE)
@Auth(permission_list=["role:btn:delete"])
async def delete_role_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    deleted_count = 0

    for id in set(params.ids):
        role = await SystemRole.get_or_none(id=id, is_del=False)
        if not role:
            continue

        dept_id = str(role.department_id) if role.department_id else None
        if dept_id:
            can_access = await PermissionService.can_access_department_data(
                str(user_id), dept_id
            )
            if not can_access:
                continue

        if await RoleService.delete(id):
            deleted_count += 1

    await RoleService.clear_role_cache(request.app.state.redis)
    return ResponseUtil.success(
        msg=f"批量删除角色成功，共删除 {deleted_count} 个角色！"
    )


@roleAPI.put(
    "/update/{id}",
    response_model=UpdateRoleResponse,
    response_class=JSONResponse,
    summary="修改角色",
)
@roleAPI.post(
    "/update/{id}",
    response_model=UpdateRoleResponse,
    response_class=JSONResponse,
    summary="修改角色",
)
@Log(title="修改角色", operation_type=OperationType.UPDATE)
@Auth(permission_list=["role:btn:update"])
async def update_role(
    request: Request,
    params: UpdateRoleParams,
    id: str = Path(..., description="角色ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    user_id = current_user.get("id")

    if role.department_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), str(role.department_id)
        )
        if not can_access:
            return ResponseUtil.error(msg="修改失败,无权限操作该角色！")

    if params.department_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), params.department_id
        )
        if not can_access:
            return ResponseUtil.error(msg="修改失败,无权限操作目标部门！")

    update_payload = {}
    if params.code:
        update_payload["code"] = params.code
    if params.name:
        update_payload["name"] = params.name
    if params.description is not None:
        update_payload["description"] = params.description
    if params.status is not None:
        update_payload["status"] = params.status
    if params.department_id:
        update_payload["department_id"] = params.department_id
    success, msg = await RoleService.update_role(id, update_payload)
    if success:
        await RoleService.clear_role_cache(request.app.state.redis)
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@roleAPI.get(
    "/info/{id}",
    response_model=GetRoleInfoResponse,
    response_class=JSONResponse,
    summary="查询角色详情",
)
@Log(title="查询角色详情", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:info"])
async def get_role_info(
    request: Request,
    id: str = Path(..., description="角色ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    user_id = current_user.get("id")
    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), dept_id
        )
        if not can_access:
            return ResponseUtil.error(msg="无权限查看该角色！")

    role_info = await RoleService.get_role_info_data(id)
    if role_info:
        return ResponseUtil.success(data=role_info)
    return ResponseUtil.error(msg="查询角色详情失败！")


@roleAPI.get(
    "/list",
    response_model=GetRoleListResponse,
    response_class=JSONResponse,
    summary="查询角色列表",
)
@Log(title="查询角色列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:list"])
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
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")

    filterArgs = {
        f"{k}__contains": v
        for k, v in {
            "name": name,
            "code": code,
            "description": description,
        }.items()
        if v
    }

    if status is not None:
        filterArgs["status"] = status
    PermissionService.apply_tenant_filter(filterArgs, current_user, "tenant_id")

    data_scope = await PermissionService.get_data_scope(str(user_id))

    if department_ids:
        dept_id_list = [
            dept_id.strip() for dept_id in department_ids.split(",") if dept_id.strip()
        ]
        if not data_scope.get("all"):
            dept_id_list = [
                d for d in dept_id_list if d in data_scope["department_ids"]
            ]
        if dept_id_list:
            filterArgs["department__id__in"] = dept_id_list
        else:
            return ResponseUtil.success(
                data={"result": [], "total": 0, "page": page, "pageSize": pageSize}
            )
    elif department_id:
        if (
            not data_scope.get("all")
            and department_id not in data_scope["department_ids"]
        ):
            return ResponseUtil.error(msg="无权限查看该部门的角色！")
        filterArgs["department__id"] = department_id
    else:
        if data_scope.get("all"):
            pass
        elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
            filterArgs["department__id__in"] = list(data_scope["department_ids"])
        else:
            if data_scope["department_id"]:
                filterArgs["department__id"] = data_scope["department_id"]
            else:
                return ResponseUtil.success(
                    data={"result": [], "total": 0, "page": page, "pageSize": pageSize}
                )

    data = await RoleService.get_role_list_data(filterArgs, page, pageSize)
    return ResponseUtil.success(data=data)


@roleAPI.post(
    "/addPermission/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="新增角色权限",
)
@Log(title="新增角色权限", operation_type=OperationType.INSERT)
@Auth(permission_list=["role:btn:addPermission"])
async def add_role_permission(
    request: Request,
    params: AddRolePermissionParams,
    id: str = Path(..., description="角色ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")

    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), dept_id
        )
        if not can_access:
            return ResponseUtil.error(msg="无权限操作该角色！")

    success, msg = await RoleService.add_role_permissions(id, params.permission_ids)
    if success:
        await RoleService.clear_role_cache(request.app.state.redis)
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@roleAPI.delete(
    "/deletePermission/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除角色权限",
)
@roleAPI.post(
    "/deletePermission/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除角色权限",
)
@Log(title="删除角色权限", operation_type=OperationType.DELETE)
@Auth(permission_list=["role:btn:deletePermission"])
async def delete_role_permission(
    request: Request,
    role_id: str = Query(..., description="角色ID"),
    permission_id: str = Query(..., description="权限ID"),
    id: str = Path(..., description="兼容旧接口，可忽略"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")

    role = await SystemRole.get_or_none(id=role_id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    if role.department_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), str(role.department_id)
        )
        if not can_access:
            return ResponseUtil.error(msg="无权限操作该角色！")

    success, msg = await RoleService.delete_role_permission(role_id, permission_id)
    if success:
        await RoleService.clear_role_cache(request.app.state.redis)
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@roleAPI.put(
    "/updatePermission/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="修改角色权限",
)
@roleAPI.post(
    "/updatePermission/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="修改角色权限",
)
@Log(title="修改角色权限", operation_type=OperationType.UPDATE)
@Auth(permission_list=["role:btn:updatePermission"])
async def update_role_permission(
    request: Request,
    params: AddRolePermissionParams,
    id: str = Path(..., description="角色ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")

    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), dept_id
        )
        if not can_access:
            return ResponseUtil.error(msg="无权限操作该角色！")

    success, msg = await RoleService.update_role_permissions(id, params.permission_ids)
    if success:
        await RoleService.clear_role_cache(request.app.state.redis)
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@roleAPI.get(
    "/permissionInfo/{id}",
    response_model=GetRolePermissionInfoResponse,
    response_class=JSONResponse,
    summary="获取角色权限信息",
)
@Log(title="获取角色权限信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:permissionInfo"])
async def get_role_permission_info(
    request: Request,
    role_id: str = Query(..., description="角色ID"),
    permission_id: str = Query(..., description="权限ID"),
    id: str = Path(..., description="兼容旧接口，可忽略"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")

    role = await SystemRole.get_or_none(id=role_id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    if role.department_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), str(role.department_id)
        )
        if not can_access:
            return ResponseUtil.error(msg="无权限查看该角色权限！")

    permission = await SystemPermission.get_or_none(id=permission_id, is_del=False)
    if not permission:
        return ResponseUtil.error(msg="权限不存在！")

    data = await RoleService.get_role_permission_info_data(role, permission)
    return ResponseUtil.success(data=data)


@roleAPI.get(
    "/permissionList/{id}",
    response_model=GetRolePermissionListResponse,
    response_class=JSONResponse,
    summary="获取角色权限列表",
)
@Log(title="获取角色权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["role:btn:permissionList"])
async def get_role_permission_list(
    request: Request,
    id: str = Path(..., description="角色ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")

    role = await SystemRole.get_or_none(id=id, is_del=False)
    if not role:
        return ResponseUtil.error(msg="角色不存在！")

    dept_id = str(role.department_id) if role.department_id else None
    if dept_id:
        can_access = await PermissionService.can_access_department_data(
            str(user_id), dept_id
        )
        if not can_access:
            return ResponseUtil.error(msg="无权限查看该角色权限！")

    data = await RoleService.get_role_permission_list_data(id)
    return ResponseUtil.success(data=data)


# ==================== 导入导出 API ====================


@roleAPI.get("/export", response_class=JSONResponse, summary="导出角色数据")
@Log(title="导出角色数据", operation_type=OperationType.EXPORT)
@Auth(permission_list=["role:btn:export"])
async def export_role(
    request: Request,
    name: Optional[str] = Query(default=None, description="角色名称"),
    code: Optional[str] = Query(default=None, description="角色编码"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from fastapi.responses import StreamingResponse

    filter_args = {}
    if name:
        filter_args["name__contains"] = name
    if code:
        filter_args["code__contains"] = code

    excel_file = await RoleService.export_to_excel(filters=filter_args)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=role.xlsx"},
    )


@roleAPI.get(
    "/export/template", response_class=JSONResponse, summary="下载角色导入模板"
)
@Log(title="下载角色导入模板", operation_type=OperationType.EXPORT)
@Auth(permission_list=["role:btn:import"])
async def download_role_template(request: Request):
    from fastapi.responses import StreamingResponse

    template_file = RoleService.get_import_template()
    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=role_template.xlsx"},
    )


@roleAPI.post(
    "/import",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="导入角色数据",
)
@Log(title="导入角色数据", operation_type=OperationType.IMPORT)
@Auth(permission_list=["role:btn:import"])
async def import_role(
    request: Request,
    file: UploadFile = File(..., description="Excel文件"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    content = await file.read()
    success_count, fail_count, errors = await RoleService.import_from_excel(
        content, current_user_id=current_user.get("id")
    )
    if success_count > 0:
        await RoleService.clear_role_cache(request.app.state.redis)
    msg = f"导入完成，成功 {success_count} 条，失败 {fail_count} 条"
    if errors:
        msg += f"。错误信息：{'; '.join(errors[:5])}"
    return ResponseUtil.success(
        msg=msg, data={"success": success_count, "fail": fail_count, "errors": errors}
    )
