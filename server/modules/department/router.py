from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse, DeleteListParams
from modules import SystemDepartment, SystemRole
from modules.department.schema import AddDepartmentParams, GetDepartmentInfoResponse, GetDepartmentListResponse
from modules.department.service import DepartmentService
from utils.get_redis import RedisKeyConfig
from utils.permission import DataScope, PermissionService
from utils.response import ResponseUtil

departmentAPI = APIRouter(prefix="/department")


async def clear_department_cache(request: Request):
    user_infos = await request.app.state.redis.keys(f"{RedisKeyConfig.USER_INFO.key}:*")
    if user_infos:
        await request.app.state.redis.delete(*user_infos)
    user_routes = await request.app.state.redis.keys(f"{RedisKeyConfig.USER_ROUTES.key}:*")
    if user_routes:
        await request.app.state.redis.delete(*user_routes)


@departmentAPI.post("/add", response_model=BaseResponse, response_class=JSONResponse, summary="新增部门")
@Log(title="新增部门", operation_type=OperationType.INSERT)
@Auth(permission_list=["department:btn:add"])
async def add_department(
    request: Request,
    params: AddDepartmentParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    is_superadmin = bool(current_user.get("is_superadmin"))
    target_tenant_id = (
        params.tenant_id if is_superadmin and params.tenant_id else current_user.get("tenant_id")
    )
    if not params.parent_id and not is_superadmin:
        params.parent_id = current_user.get("department_id")

    if params.parent_id:
        can_access = await PermissionService.can_access_department_data(str(user_id), str(params.parent_id))
        if not can_access:
            return ResponseUtil.error(msg="添加失败，无权限在该部门下创建子部门")

    department = await DepartmentService.create_department(
        {
            "name": params.name,
            "code": params.code,
            "tenant_id": target_tenant_id,
            "parent_id": params.parent_id,
            "principal": params.principal,
            "phone": params.phone,
            "email": params.email,
            "remark": params.remark,
            "sort": params.sort,
            "status": params.status,
        }
    )
    if department:
        await clear_department_cache(request)
        return ResponseUtil.success(msg="添加成功")
    return ResponseUtil.error(msg="添加失败")


@departmentAPI.delete("/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除部门")
@departmentAPI.post("/delete/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除部门")
@Log(title="删除部门", operation_type=OperationType.DELETE)
@Auth(permission_list=["department:btn:delete"])
async def delete_department(
    request: Request,
    id: str = Path(description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    department = await SystemDepartment.get_or_none(id=id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="删除失败，部门不存在")

    user_id = current_user.get("id")
    can_access = await PermissionService.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="删除失败，无权限")

    if await DepartmentService.delete_department_recursive(str(department.id)):
        await clear_department_cache(request)
        return ResponseUtil.success(msg="删除成功")
    return ResponseUtil.error(msg="删除失败")


@departmentAPI.delete("/deleteList", response_model=BaseResponse, response_class=JSONResponse, summary="批量删除部门")
@departmentAPI.post("/deleteList", response_model=BaseResponse, response_class=JSONResponse, summary="批量删除部门")
@Log(title="批量删除部门", operation_type=OperationType.DELETE)
@Auth(permission_list=["department:btn:delete"])
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

        can_access = await PermissionService.can_access_department_data(str(user_id), item)
        if can_access:
            await DepartmentService.delete_department_recursive(str(department.id))
            deleted_count += 1

    await clear_department_cache(request)
    return ResponseUtil.success(msg=f"删除成功，共删除 {deleted_count} 个部门")


@departmentAPI.put("/update/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="修改部门")
@departmentAPI.post("/update/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="修改部门")
@Log(title="修改部门", operation_type=OperationType.UPDATE)
@Auth(permission_list=["department:btn:update"])
async def update_department(
    request: Request,
    params: AddDepartmentParams,
    id: str = Path(description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    department = await SystemDepartment.get_or_none(id=id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="修改失败，部门不存在")

    user_id = current_user.get("id")
    can_access = await PermissionService.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="修改失败，无权限")

    new_parent_id = str(params.parent_id) if params.parent_id else None
    if new_parent_id and new_parent_id != str(department.parent_id):
        can_access_parent = await PermissionService.can_access_department_data(str(user_id), new_parent_id)
        if not can_access_parent:
            return ResponseUtil.error(msg="无权限操作目标上级部门")

    try:
        await DepartmentService.update_department_with_ancestor(
            department,
            {
                "name": params.name,
                "code": params.code,
                "parent_id": new_parent_id,
                "principal": params.principal,
                "phone": params.phone,
                "email": params.email,
                "remark": params.remark,
                "sort": params.sort,
                "status": params.status,
            },
        )
    except ValueError as exc:
        return ResponseUtil.error(msg=str(exc))

    await clear_department_cache(request)
    return ResponseUtil.success(msg="修改成功")


@departmentAPI.get(
    "/info/{id}",
    response_model=GetDepartmentInfoResponse,
    response_class=JSONResponse,
    summary="查询部门详情",
)
@Log(title="查询部门详情", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:info"])
async def get_department(
    request: Request,
    id: str = Path(description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    can_access = await PermissionService.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="查询失败，无权限")

    department = await SystemDepartment.get_or_none(id=id, is_del=False)
    if not department:
        return ResponseUtil.error(msg="部门不存在")

    dept_data = await SystemDepartment.filter(id=id, is_del=False).values(
        id="id",
        tenant_id="tenant_id",
        code="code",
        ancestor_path="ancestor_path",
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
    return ResponseUtil.error(msg="部门不存在")


@departmentAPI.get(
    "/list",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="查询部门列表",
)
@Log(title="查询部门列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list"])
async def get_department_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页条数"),
    department_id: Optional[str] = Query(default=None, description="上级部门ID"),
    tenant_id: Optional[str] = Query(default=None, description="租户ID（超管可选）"),
    name: Optional[str] = Query(default=None, description="部门名称"),
    principal: Optional[str] = Query(default=None, description="负责人"),
    phone: Optional[str] = Query(default=None, description="电话"),
    email: Optional[str] = Query(default=None, description="邮箱"),
    remark: Optional[str] = Query(default=None, description="备注"),
    sort: Optional[int] = Query(default=None, description="排序权重"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    data_scope = await PermissionService.get_data_scope(str(user_id))

    filter_args = {
        f"{k}__contains": v
        for k, v in {
            "name": name,
            "principal": principal,
            "phone": phone,
            "email": email,
            "remark": remark,
            "sort": sort,
        }.items()
        if v is not None and v != ""
    }

    # 超管可以指定 tenant_id，否则按当前用户租户过滤
    if tenant_id:
        filter_args["tenant_id"] = tenant_id
    else:
        PermissionService.apply_tenant_filter(filter_args, current_user, "tenant_id")
    queryset = SystemDepartment.filter(**filter_args, is_del=False)

    if data_scope.get("all"):
        pass
    elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        queryset = queryset.filter(id__in=list(data_scope["department_ids"]))
    else:
        if data_scope["department_id"]:
            queryset = queryset.filter(id=data_scope["department_id"])
        else:
            return ResponseUtil.success(data={"result": [], "total": 0, "page": page, "pageSize": pageSize})

    if department_id:
        queryset = queryset.filter(ancestor_path__contains=f"/{department_id}/").exclude(id=department_id)

    total = await queryset.count()
    data = (
        await queryset.order_by("sort", "created_at")
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .values(
            id="id",
            tenant_id="tenant_id",
            code="code",
            ancestor_path="ancestor_path",
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
    return ResponseUtil.success(data={"result": data, "total": total, "page": page, "pageSize": pageSize})


@departmentAPI.get(
    "/roleList/{id}",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="用户获取部门角色列表",
)
@Log(title="获取部门角色列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list"])
async def get_department_role_list(
    request: Request,
    id: str = Path(..., description="部门ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    user_id = current_user.get("id")
    can_access = await PermissionService.can_access_department_data(str(user_id), id)
    if not can_access:
        return ResponseUtil.error(msg="查询失败，无权限")

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
    return ResponseUtil.success(data={"result": data, "total": len(data), "page": 1, "pageSize": 9999})


@departmentAPI.get(
    "/all",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="获取所有部门数据",
)
@Log(title="获取所有部门数据", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list"])
async def get_all_departments(request: Request, current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    data_scope = await PermissionService.get_data_scope(str(user_id))

    filter_args = {"is_del": False}
    PermissionService.apply_tenant_filter(filter_args, current_user, "tenant_id")

    queryset = SystemDepartment.filter(**filter_args)

    if data_scope.get("all"):
        pass
    elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        queryset = queryset.filter(id__in=list(data_scope["department_ids"]))
    else:
        if data_scope["department_id"]:
            queryset = queryset.filter(id=data_scope["department_id"])
        else:
            return ResponseUtil.success(data={"result": [], "total": 0, "page": 1, "pageSize": 9999})

    data = (
        await queryset.order_by("sort", "created_at").values(
            id="id",
            tenant_id="tenant_id",
            code="code",
            ancestor_path="ancestor_path",
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
    return ResponseUtil.success(data={"result": data, "total": len(data), "page": 1, "pageSize": 9999})


@departmentAPI.get(
    "/tree",
    response_model=GetDepartmentListResponse,
    response_class=JSONResponse,
    summary="获取部门树形结构数据",
)
@Log(title="获取部门树形结构数据", operation_type=OperationType.SELECT)
@Auth(permission_list=["department:btn:list"])
async def get_department_tree(request: Request, current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    data_scope = await PermissionService.get_data_scope(str(user_id))

    filter_args = {"is_del": False}
    PermissionService.apply_tenant_filter(filter_args, current_user, "tenant_id")
    queryset = SystemDepartment.filter(**filter_args)

    if data_scope.get("all"):
        pass
    elif data_scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        queryset = queryset.filter(id__in=list(data_scope["department_ids"]))
    else:
        if data_scope["department_id"]:
            queryset = queryset.filter(id=data_scope["department_id"])
        else:
            return ResponseUtil.success(data={"result": [], "total": 0, "page": 1, "pageSize": 9999})

    departments = await queryset.order_by("sort", "created_at").values(
        id="id",
        tenant_id="tenant_id",
        code="code",
        ancestor_path="ancestor_path",
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

    dept_ids = {str(dept.get("id")) for dept in departments}

    def build_tree(parent_id=None):
        tree = []
        for dept in departments:
            dept_parent_id = dept.get("parent_id")
            dept_parent_id_str = str(dept_parent_id) if dept_parent_id else None
            should_add = False
            if parent_id is None:
                if dept_parent_id is None or dept_parent_id_str not in dept_ids:
                    should_add = True
            else:
                if dept_parent_id_str == str(parent_id):
                    should_add = True

            if should_add:
                dept_copy = dict(dept)
                children = build_tree(dept.get("id"))
                if children:
                    dept_copy["children"] = children
                tree.append(dept_copy)
        return tree

    return ResponseUtil.success(
        data={
            "result": build_tree(),
            "total": len(departments),
            "page": 1,
            "pageSize": 9999,
        }
    )
