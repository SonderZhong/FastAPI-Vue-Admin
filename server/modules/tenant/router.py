# _*_ coding : UTF-8 _*_
# @Time : 2026/07/02 21:45
# @UpdateTime : 2026/07/02 21:45
# @Author : SonderZhong
# @File : router.py
# @Software : VSCode
# @Comment : 本程序用于租户相关API


from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request, File, UploadFile
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse, DeleteListParams
from modules.tenant.schema import (
    AddTenantParams,
    UpdateTenantParams,
    GetTenantInfoResponse,
    GetTenantListResponse,
    JoinTenantParams,
)
from modules.tenant.service import TenantService
from utils.response import ResponseUtil

tenantAPI = APIRouter(prefix="/tenant")


@tenantAPI.post(
    "/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增租户"
)
@Log(title="新增租户", operation_type=OperationType.INSERT)
@Auth(permission_list=["tenant:btn:add"])
async def add_tenant(
    request: Request,
    params: AddTenantParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await TenantService.create_tenant(
        params.dict(exclude_unset=True),
        creator_id=str(current_user.get("id")) if current_user.get("id") else None,
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@tenantAPI.delete(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除租户",
)
@tenantAPI.post(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除租户",
)
@Log(title="删除租户", operation_type=OperationType.DELETE)
@Auth(permission_list=["tenant:btn:delete"])
async def delete_tenant(
    request: Request,
    id: str = Path(..., description="租户ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success = await TenantService.delete(id)
    return (
        ResponseUtil.success(msg="删除成功！")
        if success
        else ResponseUtil.error(msg="删除失败！")
    )


@tenantAPI.delete(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除租户",
)
@tenantAPI.post(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除租户",
)
@Log(title="批量删除租户", operation_type=OperationType.DELETE)
@Auth(permission_list=["tenant:btn:delete"])
async def delete_tenant_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    deleted, total = await TenantService.batch_delete(params.ids)
    return ResponseUtil.success(
        msg=f"批量删除完成，成功 {deleted} 个，失败 {total - deleted} 个！"
    )


@tenantAPI.put(
    "/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="修改租户",
)
@tenantAPI.post(
    "/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="修改租户",
)
@Log(title="修改租户", operation_type=OperationType.UPDATE)
@Auth(permission_list=["tenant:btn:update"])
async def update_tenant(
    request: Request,
    params: UpdateTenantParams,
    id: str = Path(..., description="租户ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    update_data = params.dict(exclude_unset=True, exclude_none=True)
    success, msg = await TenantService.update_tenant(id, update_data)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@tenantAPI.get(
    "/info/{id}",
    response_class=JSONResponse,
    response_model=GetTenantInfoResponse,
    summary="获取租户信息",
)
@Log(title="获取租户信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["tenant:btn:info"])
async def get_tenant_info(
    request: Request,
    id: str = Path(..., description="租户ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    data = await TenantService.get_tenant_info(id)
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="租户不存在！")


@tenantAPI.get(
    "/list",
    response_class=JSONResponse,
    response_model=GetTenantListResponse,
    summary="获取租户列表",
)
@Log(title="获取租户列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["tenant:btn:list"])
async def get_tenant_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    name: Optional[str] = Query(default=None, description="租户名称"),
    code: Optional[str] = Query(default=None, description="租户编码"),
    status: Optional[int] = Query(default=None, description="状态"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    filter_args = {}
    if name:
        filter_args["name__contains"] = name
    if code:
        filter_args["code__contains"] = code
    if status is not None:
        filter_args["status"] = status

    data, total = await TenantService.get_tenant_list(page, pageSize, filter_args)
    return ResponseUtil.success(
        data={
            "result": data,
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


# ==================== 邀请码管理 API ====================


@tenantAPI.post(
    "/invite-code/generate/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="生成租户邀请码",
)
@Log(title="生成租户邀请码", operation_type=OperationType.UPDATE)
@Auth(permission_list=["tenant:btn:update"])
async def generate_invite_code(
    request: Request,
    id: str = Path(..., description="租户ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg, data = await TenantService.generate_invite_code(id)
    if success:
        return ResponseUtil.success(msg=msg, data=data)
    return ResponseUtil.error(msg=msg)


@tenantAPI.put(
    "/invite-code/toggle/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="开启/关闭租户邀请注册",
)
@tenantAPI.post(
    "/invite-code/toggle/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="开启/关闭租户邀请注册",
)
@Log(title="开启/关闭租户邀请注册", operation_type=OperationType.UPDATE)
@Auth(permission_list=["tenant:btn:update"])
async def toggle_invite_register(
    request: Request,
    id: str = Path(..., description="租户ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await TenantService.toggle_allow_register(id)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@tenantAPI.get(
    "/invite-code/info/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取租户邀请码信息",
)
@Log(title="获取租户邀请码信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["tenant:btn:info"])
async def get_invite_code_info(
    request: Request,
    id: str = Path(..., description="租户ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    data = await TenantService.get_invite_code_info(id)
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="租户不存在！")


@tenantAPI.get(
    "/validate-invite-code/{code}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="验证邀请码",
)
async def validate_invite_code(
    request: Request,
    code: str = Path(..., description="邀请码"),
):
    data = await TenantService.validate_invite_code(code)
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="邀请码无效或租户已禁用！")


# ==================== 加入租户 API ====================


@tenantAPI.post(
    "/join",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="通过邀请码加入租户",
)
@Log(title="通过邀请码加入租户", operation_type=OperationType.UPDATE)
async def join_tenant(
    request: Request,
    params: JoinTenantParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    success, msg = await TenantService.join_tenant(
        current_user.get("id"), params.invite_code, request.app.state.redis
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@tenantAPI.get(
    "/members/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取租户成员列表",
)
@Log(title="获取租户成员列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["tenant:btn:info"])
async def get_tenant_members(
    request: Request,
    id: str = Path(..., description="租户ID"),
    page: int = Query(default=1, description="页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    members, total = await TenantService.get_tenant_members(id, page, pageSize)
    return ResponseUtil.success(
        data={
            "result": members,
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


# ==================== 导入导出 API ====================


@tenantAPI.get("/export", response_class=JSONResponse, summary="导出租户数据")
@Log(title="导出租户数据", operation_type=OperationType.EXPORT)
@Auth(permission_list=["tenant:btn:export"])
async def export_tenant(
    request: Request,
    name: Optional[str] = Query(default=None, description="租户名称"),
    code: Optional[str] = Query(default=None, description="租户编码"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from fastapi.responses import StreamingResponse

    filter_args = {}
    if name:
        filter_args["name__contains"] = name
    if code:
        filter_args["code__contains"] = code

    excel_file = await TenantService.export_to_excel(filters=filter_args)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=tenant.xlsx"},
    )


@tenantAPI.get(
    "/export/template", response_class=JSONResponse, summary="下载租户导入模板"
)
@Log(title="下载租户导入模板", operation_type=OperationType.EXPORT)
@Auth(permission_list=["tenant:btn:import"])
async def download_tenant_template(request: Request):
    from fastapi.responses import StreamingResponse

    template_file = TenantService.get_import_template()
    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=tenant_template.xlsx"},
    )


@tenantAPI.post(
    "/import",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="导入租户数据",
)
@Log(title="导入租户数据", operation_type=OperationType.IMPORT)
@Auth(permission_list=["tenant:btn:import"])
async def import_tenant(
    request: Request,
    file: UploadFile = File(..., description="Excel文件"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    content = await file.read()
    success_count, fail_count, errors = await TenantService.import_from_excel(
        content, current_user_id=current_user.get("id")
    )
    msg = f"导入完成，成功 {success_count} 条，失败 {fail_count} 条"
    if errors:
        msg += f"。错误信息：{'; '.join(errors[:5])}"
    return ResponseUtil.success(
        msg=msg, data={"success": success_count, "fail": fail_count, "errors": errors}
    )
