# _*_ coding : UTF-8 _*_
# @Time : 2025/08/24 23:25
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : department.py
# @Software : PyCharm
# @Comment : 部门管理 API - 集成 Casbin 数据权限
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from models import SystemDepartment, SystemRole
from schemas.common import BaseResponse, DeleteListParams
from schemas.department import (
    AddDepartmentParams,
    GetDepartmentInfoResponse,
    GetDepartmentListResponse
)
from utils.casbin import CasbinEnforcer, DataScope
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil

departmentAPI = APIRouter(prefix="/department")


async def clear_department_cache(request: Request):
    """清除部门相关缓存"""
    userInfos = await request.app.state.redis.keys(f"{RedisKeyConfig.USER_INFO.key}:*")
    if userInfos:
        await request.app.state.redis.delete(*userInfos)
    userRoutes = await request.app.state.redis.keys(f"{RedisKeyConfig.USER_ROUTES.key}:*")
    if userRoutes:
        await request.app.state.redis.delete(*userRoutes)


@departmentAPI.post(
    "/add", response_model=BaseResponse, response_class=JSONResponse, summary="新增部门"
)
@Log(title="新增部门", operation_type=OperationType.INSERT)
@Auth(permission_list=["department:btn:add", "POST:/department/add"])
async def add_department(
    request: Request,
    params: AddDepartmentParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    parent_id = current_user.get("department_id")
    
    # 如果没有指定父部门，默认使用当前用户的部门
    if not params.parent_id:
        params.parent_id = parent_id
    
    # 使用 Casbin 检查父部门权限
    if params.parent_id:
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), str(params.parent_id))
        if not can_access:
            return ResponseUtil.error(msg="添加失败，无权限在该部门下创建子部门！")
    
    department = await SystemDepartment.create(
        name=params.name,
        parent_id=params.parent_id,
        principal=params.principal,
        phone=params.phone,
        email=params.email,
        remark=params.remark,
        sort=params.sort,
        status=params.status,
    )
    if department:
        await clear_department_cache(request)
        return ResponseUtil.success(msg="添加成功！")
    else:
        return ResponseUtil.error(msg="添加失败！")


@departmentAPI.delete(
    "/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除部门",
)
@departmentAPI.post(
    "/delete/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="删除部门",
)
@Log(title="删除部门", operation_type=OperationType.DELETE)
@Auth(permission_list=["department:btn:delete", "DELETE,POST:/department/delete/*"])
async def delete_department(
    request: Request,
    id: str = Path(description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    department = await SystemDepartment.get_or_none(id=id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="删除失败,部门不存在！")
    
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="删除失败,无权限！")
    
    if await delete_department_recursive(department_id=department.id):
        await clear_department_cache(request)
        return ResponseUtil.success(msg="删除成功！")
    return ResponseUtil.error(msg="删除失败!")


@departmentAPI.delete(
    "/deleteList",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="批量删除部门",
)
@departmentAPI.post(
    "/deleteList",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="批量删除部门",
)
@Log(title="批量删除部门", operation_type=OperationType.DELETE)
@Auth(permission_list=["department:btn:delete", "DELETE,POST:/department/deleteList"])
async def delete_department_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    deleted_count = 0
    
    for item in set(params.ids):
        department = await SystemDepartment.get_or_none(id=item, is_del=False)
        if not department:
            continue
        
        # 使用 Casbin 检查部门数据权限
        can_access = await CasbinEnforcer.can_access_department_data(str(user_id), item)
        if can_access:
            await delete_department_recursive(department_id=department.id)
            deleted_count += 1
    
    await clear_department_cache(request)
    return ResponseUtil.success(msg=f"删除成功，共删除 {deleted_count} 个部门！")


async def delete_department_recursive(department_id: str):
    """
    递归删除部门及其附属部门
    :param department_id: 部门ID
    :return:
    """
    await SystemDepartment.filter(id=department_id, is_del=False).update(is_del=True)
    sub_departments = await SystemDepartment.filter(
        parent_id=department_id, is_del=False
    ).all()
    for sub_department in sub_departments:
        await delete_department_recursive(sub_department.id)
    return True


@departmentAPI.put(
    "/update/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="修改部门",
)
@departmentAPI.post(
    "/update/{id}",
    response_model=BaseResponse,
    response_class=JSONResponse,
    summary="修改部门",
)
@Log(title="修改部门", operation_type=OperationType.UPDATE)
@Auth(permission_list=["department:btn:update", "PUT,POST:/department/update/*"])
async def update_department(
    request: Request,
    params: AddDepartmentParams,
    id: str = Path(description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    department = await SystemDepartment.get_or_none(id=id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="修改失败,部门不存在！")
    
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="修改失败,无权限！")
    
    # 如果要更换父部门，检查目标父部门权限
    if params.parent_id and str(params.parent_id) != str(department.parent_id):
        can_access_parent = await CasbinEnforcer.can_access_department_data(str(user_id), str(params.parent_id))
        if not can_access_parent:
            return ResponseUtil.error(msg="修改失败,无权限操作目标父部门！")
    
    department.name = params.name
    department.parent_id = params.parent_id
    department.principal = params.principal
    department.phone = params.phone
    department.email = params.email
    department.remark = params.remark
    department.sort = params.sort
    department.status = params.status
    await department.save()
    
    await clear_department_cache(request)
    return ResponseUtil.success(msg="修改成功！")


@departmentAPI.get(
    "/info/{id}",
    response_model=GetDepartmentInfoResponse,
    response_class=JSONResponse,
    summary="查询部门详情",
)
@Log(title="查询部门详情", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:info", "GET:/department/info/*"])
async def get_department(
    request: Request,
    id: str = Path(description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="查询失败,无权限！")
    
    department = await SystemDepartment.get_or_none(id=id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="部门不存在！")
    
    dept_data = await SystemDepartment.filter(id=id, is_del=False).values(
        id="id",
        name="name",
        parent_id="parent_id",
        principal="principal",
        phone="phone",
        email="email",
        remark="remark",
        sort="sort",
        status="status",
        created_at="created_at",
        updated_at="updated_at",
        create_by="create_by",
        update_by="update_by",
    )
    
    if dept_data:
        return ResponseUtil.success(data=dept_data[0])
    return ResponseUtil.error(msg="部门不存在！")


@departmentAPI.get(
    "/list",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="查询部门列表",
)
@Log(title="查询部门列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list", "GET:/department/list"])
async def get_department_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页条数"),
    name: Optional[str] = Query(default=None, description="部门名称"),
    principal: Optional[str] = Query(default=None, description="负责人"),
    phone: Optional[str] = Query(default=None, description="电话"),
    email: Optional[str] = Query(default=None, description="邮箱"),
    remark: Optional[str] = Query(default=None, description="备注"),
    sort: Optional[int] = Query(default=None, description="排序权重"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    
    # 获取用户的数据权限范围
    data_scope = await CasbinEnforcer.get_data_scope(str(user_id))
    
    filterArgs = {
        f"{k}__contains": v
        for k, v in {
            "name": name,
            "principal": principal,
            "phone": phone,
            "email": email,
            "remark": remark,
            "sort": sort,
        }.items()
        if v
    }
    
    # 根据数据权限范围过滤
    if data_scope["scope"] == DataScope.ALL:
        # 全部数据权限，不限制部门
        pass
    elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        # 部门及下属部门数据权限
        filterArgs["id__in"] = list(data_scope["department_ids"])
    else:
        # 仅本人数据权限，只能看自己的部门
        if data_scope["department_id"]:
            filterArgs["id"] = data_scope["department_id"]
        else:
            return ResponseUtil.success(
                data={"result": [], "total": 0, "page": page, "pageSize": pageSize}
            )

    total = await SystemDepartment.filter(**filterArgs, is_del=False).count()
    data = (
        await SystemDepartment.filter(**filterArgs, is_del=False)
        .order_by("sort", "created_at")
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .values(
            id="id",
            name="name",
            parent_id="parent_id",
            principal="principal",
            phone="phone",
            email="email",
            remark="remark",
            sort="sort",
            status="status",
            created_at="created_at",
            updated_at="updated_at",
        )
    )
    return ResponseUtil.success(
        data={"result": data, "total": total, "page": page, "pageSize": pageSize}
    )


@departmentAPI.get(
    "/roleList/{id}",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="用户获取部门角色列表",
)
@Log(title="获取部门角色列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list", "GET:/department/roleList/*"])
async def get_department_role_list(
    request: Request,
    id: str = Path(..., description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    # 使用 Casbin 检查部门数据权限
    user_id = current_user.get("id")
    can_access = await CasbinEnforcer.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="查询失败,无权限！")
    
    data = await SystemRole.filter(department__id=id, is_del=False).values(
        id="id",
        department_id="department__id",
        department_name="department__name",
        department_phone="department__phone",
        department_principal="department__principal",
        department_email="department__email",
        role_name="name",
        role_code="code",
        role_id="id",
        created_at="created_at",
        updated_at="updated_at",
    )
    return ResponseUtil.success(
        data={"result": data, "total": len(data), "page": 1, "pageSize": 9999}
    )


@departmentAPI.get(
    "/all",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="获取所有部门数据",
)
@Log(title="获取所有部门数据", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list", "GET:/department/all"])
async def get_all_departments(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    user_id = current_user.get("id")
    
    # 获取用户的数据权限范围
    data_scope = await CasbinEnforcer.get_data_scope(str(user_id))
    
    filterArgs = {"is_del": False}
    
    # 根据数据权限范围过滤
    if data_scope["scope"] == DataScope.ALL:
        # 全部数据权限，不限制部门
        pass
    elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        # 部门及下属部门数据权限
        filterArgs["id__in"] = list(data_scope["department_ids"])
    else:
        # 仅本人数据权限，只能看自己的部门
        if data_scope["department_id"]:
            filterArgs["id"] = data_scope["department_id"]
        else:
            return ResponseUtil.success(
                data={"result": [], "total": 0, "page": 1, "pageSize": 9999}
            )

    data = (
        await SystemDepartment.filter(**filterArgs)
        .order_by("sort", "created_at")
        .values(
            id="id",
            name="name",
            parent_id="parent_id",
            principal="principal",
            phone="phone",
            email="email",
            remark="remark",
            sort="sort",
            status="status",
            created_at="created_at",
            updated_at="updated_at",
        )
    )
    return ResponseUtil.success(
        data={"result": data, "total": len(data), "page": 1, "pageSize": 9999}
    )


@departmentAPI.get(
    "/tree",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="获取部门树形结构数据",
)
@Log(title="获取部门树形结构数据", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list", "GET:/department/tree"])
async def get_department_tree(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    user_id = current_user.get("id")
    
    # 获取用户的数据权限范围
    data_scope = await CasbinEnforcer.get_data_scope(str(user_id))
    
    filterArgs = {"is_del": False}
    
    # 根据数据权限范围过滤
    if data_scope["scope"] == DataScope.ALL:
        # 全部数据权限，不限制部门
        pass
    elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        # 部门及下属部门数据权限
        filterArgs["id__in"] = list(data_scope["department_ids"])
    else:
        # 仅本人数据权限，只能看自己的部门
        if data_scope["department_id"]:
            filterArgs["id"] = data_scope["department_id"]
        else:
            return ResponseUtil.success(
                data={"result": [], "total": 0, "page": 1, "pageSize": 9999}
            )

    # 获取所有有权限的部门数据
    departments = (
        await SystemDepartment.filter(**filterArgs)
        .order_by("sort", "created_at")
        .values(
            id="id",
            name="name",
            parent_id="parent_id",
            principal="principal",
            phone="phone",
            email="email",
            remark="remark",
            sort="sort",
            status="status",
            created_at="created_at",
            updated_at="updated_at",
        )
    )

    # 构建树形结构
    def build_tree(parent_id=None):
        tree = []
        for dept in departments:
            if str(dept.get("parent_id")) == str(parent_id):
                dept_copy = dict(dept)
                children = build_tree(dept.get("id"))
                if children:
                    dept_copy["children"] = children
                tree.append(dept_copy)
        return tree

    tree_data = build_tree()

    return ResponseUtil.success(
        data={
            "result": tree_data,
            "total": len(departments),
            "page": 1,
            "pageSize": 9999,
        }
    )
