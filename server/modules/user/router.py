# _*_ coding : UTF-8 _*_
# @Comment : 用户管理 API
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Path, Query, File, UploadFile, Form
from starlette.responses import JSONResponse
from modules import SystemUser, SystemDepartment, SystemTenantUser
from core.common import BaseResponse, DeleteListParams
from modules.user.schema import AddUserParams, UpdateUserParams, GetUserInfoResponse, GetUserListResponse, \
    AddUserRoleParams, UpdateUserRoleParams, GetUserRoleInfoResponse, GetUserPermissionListResponse, \
    ResetPasswordParams, UpdateBaseUserInfoParams, UploadFileResponse, GetUserRoleListResponse, \
    ChangeTenantParams
from modules.user.service import UserService, UserRoleService, TenantUserService
from utils.permission import PermissionService, DataScope
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil
from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from utils.password import PasswordUtil
from utils.log import logger

userAPI = APIRouter(prefix="/user")


@userAPI.post("/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增用户")
@Log(title="新增用户", operation_type=OperationType.INSERT)
@Auth(permission_list=['user:btn:addUser'])
async def add_user(
        request: Request,
        params: AddUserParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    tenant_id = current_user.get("tenant_id")
    department_id = current_user.get("department_id")
    user_type = current_user.get("user_type", 3)

    # 超管可创建任意用户，普通管理员只能在当前租户下创建
    if user_type >= 2 and current_user.get("user_type", 3) != 0:
        return ResponseUtil.error(msg="添加失败，无权限操作！")

    if params.department_id:
        can_access = await PermissionService.can_access_department_data(str(current_user.get("id")), params.department_id)
        if not can_access:
            return ResponseUtil.error(msg="添加失败，无权限操作该部门！")

    params.password = await PasswordUtil.get_password_hash(input_password=params.password)
    success, msg = await UserService.create_user(
        params.dict(exclude_unset=True),
        tenant_id=tenant_id,
        department_id=params.department_id,
    )
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@userAPI.delete("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除用户")
@userAPI.post("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除用户")
@Log(title="删除用户", operation_type=OperationType.DELETE)
@Auth(permission_list=['user:btn:deleteUser'])
async def delete_user(
        request: Request,
        id: str = Path(..., description="用户ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="删除失败，用户不存在！")

    operator_id = current_user.get("id")
    can_access = await PermissionService.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="删除失败，无权限操作该用户！")

    if await UserService.delete_user(id, request.app.state.redis):
        return ResponseUtil.success(msg="删除成功！")
    return ResponseUtil.error(msg="删除失败！")


@userAPI.delete("/deleteUserList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除用户")
@userAPI.post("/deleteUserList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除用户")
@Log(title="批量删除用户", operation_type=OperationType.DELETE)
@Auth(permission_list=['user:btn:deleteUser'])
async def delete_user_list(
        request: Request,
        params: DeleteListParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    operator_id = current_user.get("id")
    deleted_count = 0

    for user_id in set(params.ids):
        can_access = await PermissionService.can_access_user_data(str(operator_id), user_id)
        if can_access:
            user = await SystemUser.get_or_none(id=user_id, is_del=False)
            if user:
                if await UserService.delete_user(user_id, request.app.state.redis):
                    deleted_count += 1

    return ResponseUtil.success(msg=f"删除成功，共删除 {deleted_count} 个用户！")


@userAPI.put("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新用户")
@userAPI.post("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新用户")
@Log(title="更新用户", operation_type=OperationType.UPDATE)
@Auth(permission_list=['user:btn:updateUser'])
async def update_user(
        request: Request,
        params: UpdateUserParams,
        id: str = Path(..., description="用户ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="更新失败，用户不存在！")

    operator_id = current_user.get("id")
    can_access = await PermissionService.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="更新失败，无权限操作该用户！")

    update_payload = {
        "username": params.username,
        "nickname": params.nickname,
        "phone": params.phone,
        "email": params.email,
        "gender": params.gender,
        "status": params.status,
    }
    if await UserService.update_user(id, update_payload, request.app.state.redis):
        return ResponseUtil.success(msg="更新成功！")
    return ResponseUtil.error(msg="更新失败！")


@userAPI.get("/info/{id}", response_class=JSONResponse, response_model=GetUserInfoResponse, summary="获取用户信息")
@Log(title="获取用户信息", operation_type=OperationType.SELECT)
@Auth(permission_list=['user:btn:Userinfo'])
async def get_user_info(request: Request, id: str = Path(..., description="用户ID"),
                        current_user: dict = Depends(AuthController.get_current_user)):
    data = await UserService.get_user_info(id)
    if data:
        # 补充租户-用户关联信息
        tenant_user = await SystemTenantUser.filter(user_id=id, is_del=False).first()
        if tenant_user:
            data["tenant_id"] = str(tenant_user.tenant_id) if tenant_user.tenant_id else None
            data["department_id"] = str(tenant_user.department_id) if tenant_user.department_id else None
            data["user_type"] = tenant_user.user_type
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="用户不存在！")


@userAPI.get("/list", response_class=JSONResponse, response_model=GetUserListResponse, summary="获取用户列表")
@Log(title="获取用户列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['user:btn:userList'])
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
    tenant_id = current_user.get("tenant_id")

    data_scope = await PermissionService.get_data_scope(str(operator_id))

    filterArgs = {
        f'{k}__contains': v for k, v in {
            'username': username, 'nickname': nickname,
            'phone': phone, 'email': email,
            'gender': gender, 'status': status,
        }.items() if v is not None
    }

    # 通过 TenantUser 过滤当前租户的用户
    if tenant_id:
        tenant_user_ids = await SystemTenantUser.filter(
            tenant_id=tenant_id, is_del=False,
        ).values_list("user_id", flat=True)
        filterArgs["id__in"] = list(tenant_user_ids)

    if department_ids:
        dept_id_list = [dept_id.strip() for dept_id in department_ids.split(',') if dept_id.strip()]
        if not data_scope.get("all"):
            dept_id_list = [d for d in dept_id_list if d in data_scope["department_ids"]]
        if dept_id_list:
            filterArgs["id__in"] = await SystemTenantUser.filter(
                tenant_id=tenant_id, department_id__in=dept_id_list, is_del=False,
            ).values_list("user_id", flat=True)
        else:
            return ResponseUtil.success(data={"result": [], "total": 0, "page": page, "pageSize": pageSize})
    elif department_id:
        if not data_scope.get("all") and department_id not in data_scope["department_ids"]:
            return ResponseUtil.error(msg="无权限查看该部门的用户！")
        filterArgs["id__in"] = await SystemTenantUser.filter(
            tenant_id=tenant_id, department_id=department_id, is_del=False,
        ).values_list("user_id", flat=True)

    total = await SystemUser.filter(**filterArgs, is_del=False).count()
    result = await SystemUser.filter(**filterArgs, is_del=False).offset(
        (page - 1) * pageSize
    ).limit(pageSize).values(
        id="id", created_at="created_at", updated_at="updated_at",
        username="username", email="email", phone="phone",
        nickname="nickname", avatar="avatar", gender="gender",
        status="status",
    )
    tenant_user_map = {
        str(item["user_id"]): item["user_type"]
        for item in await SystemTenantUser.filter(
            user_id__in=[str(item["id"]) for item in result], is_del=False
        ).values("user_id", "user_type")
    }
    for item in result:
        item["is_superadmin"] = tenant_user_map.get(str(item["id"])) == 0
    return ResponseUtil.success(data={"result": result, "total": total, "page": page, "pageSize": pageSize})


@userAPI.post("/addRole", response_model=BaseResponse, response_class=JSONResponse, summary="分配用户角色")
@Log(title="分配用户角色", operation_type=OperationType.INSERT)
@Auth(permission_list=['user:btn:addRole'])
async def add_user_role(request: Request, params: AddUserRoleParams,
                        current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    tenant_id = current_user.get("tenant_id")

    can_access = await PermissionService.can_access_user_data(str(operator_id), params.user_id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")

    await UserRoleService.sync_user_roles(params.user_id, params.role_ids, tenant_id)
    await UserService.delete_user_info_cache(request.app.state.redis, params.user_id)
    return ResponseUtil.success(msg="修改成功！")


@userAPI.delete("/deleteRole/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除用户角色")
@userAPI.post("/deleteRole/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="删除用户角色")
@Log(title="删除用户角色", operation_type=OperationType.DELETE)
@Auth(permission_list=['user:btn:deleteRole'])
async def delete_user_role(request: Request, id: str = Path(description="用户角色ID"),
                           current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")

    userRole = await SystemUserRole.get_or_none(id=id, is_del=False)
    if not userRole:
        return ResponseUtil.error(msg="删除失败,用户角色不存在！")

    can_access = await PermissionService.can_access_user_data(str(operator_id), str(userRole.user_id))
    if not can_access:
        return ResponseUtil.error(msg="无权限操作！")

    userRole.is_del = True
    await userRole.save()

    await UserService.delete_user_info_cache(request.app.state.redis, str(userRole.user_id))
    return ResponseUtil.success(msg="删除成功！")


@userAPI.put("/updateRole", response_model=BaseResponse, response_class=JSONResponse, summary="修改用户角色")
@userAPI.post("/updateRole", response_model=BaseResponse, response_class=JSONResponse, summary="修改用户角色")
@Log(title="修改用户角色", operation_type=OperationType.UPDATE)
@Auth(permission_list=['user:btn:updateRole'])
async def update_user_role(request: Request, params: UpdateUserRoleParams,
                           current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")
    tenant_id = current_user.get("tenant_id")

    can_access = await PermissionService.can_access_user_data(str(operator_id), params.user_id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")

    await UserRoleService.sync_user_roles(params.user_id, params.role_ids, tenant_id)
    await UserService.delete_user_info_cache(request.app.state.redis, params.user_id)
    return ResponseUtil.success(msg="修改成功！")


@userAPI.get("/roleInfo/{id}", response_model=GetUserRoleInfoResponse, response_class=JSONResponse, summary="获取用户角色信息")
@Log(title="获取用户角色信息", operation_type=OperationType.SELECT)
@Auth(permission_list=['user:btn:roleInfo'])
async def get_user_role_info(request: Request, id: str = Path(description="用户角色ID"),
                             current_user: dict = Depends(AuthController.get_current_user)):
    data = await UserRoleService.get_user_role_info(id)
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="获取失败,用户角色不存在！")


@userAPI.get("/roleList/{id}", response_model=GetUserRoleListResponse, response_class=JSONResponse, summary="获取用户角色列表")
@Log(title="获取用户角色列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['user:btn:roleList'])
async def get_user_role_list(
        request: Request,
        id: str = Path(description="用户ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    tenant_id = current_user.get("tenant_id")
    result = await UserRoleService.get_user_role_list(id, tenant_id)
    return ResponseUtil.success(data=result)


@userAPI.get("/permissionList/{id}", response_class=JSONResponse, response_model=GetUserPermissionListResponse, summary="获取用户权限列表")
@Log(title="获取用户权限列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['user:btn:permissionList'])
async def get_user_permission_list(request: Request, id: str = Path(description="用户ID"),
                                   current_user: dict = Depends(AuthController.get_current_user)):
    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="用户不存在！")

    tenant_id = current_user.get("tenant_id")
    operator_user_type = current_user.get("user_type", 3)
    result = await UserRoleService.get_user_permission_list(id, operator_user_type, tenant_id)
    return ResponseUtil.success(data=result)


@userAPI.post("/avatar/{id}", response_model=UploadFileResponse, response_class=JSONResponse, summary="上传用户头像")
@Log(title="上传用户头像", operation_type=OperationType.UPDATE)
@Auth(permission_list=['user:btn:uploadAvatar'])
async def upload_user_avatar(
        request: Request,
        id: str = Path(description="用户ID"),
        file: UploadFile = File(...),
        current_user: dict = Depends(AuthController.get_current_user)
):
    from utils.storage import StorageFactory
    from modules.file.model import SystemFile, get_file_type
    from exceptions.exception import ServiceException

    operator_id = current_user.get("id")

    user = await SystemUser.get_or_none(id=id, is_del=False)
    if not user:
        return ResponseUtil.error(msg="用户不存在！")

    can_access = await PermissionService.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")

    image_mimetypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/svg+xml', 'image/bmp', 'image/webp', 'image/tiff']
    if file.content_type not in image_mimetypes:
        raise ServiceException(message="文件类型不支持，仅支持图片文件")

    max_size = 5 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise ServiceException(message="文件大小不能超过5MB")

    await file.seek(0)

    try:
        dynamic_config = request.app.state.dynamic_config
        storage = await StorageFactory.create(dynamic_config)
        storage_type = await dynamic_config.get("upload_storage_type", "local")
        result = await storage.upload(file, "avatars")
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"

        file_record = await SystemFile.create(
            name=file.filename, key=result["key"], url=result["url"], size=result["size"],
            file_type=get_file_type(file.filename), mime_type=file.content_type,
            extension=ext, hash=result.get("hash"), storage_type=storage_type,
            folder="avatars", uploader_id=operator_id, uploader_name=current_user.get("username"),
        )

        user.avatar = result["url"]
        await user.save()

        await UserService.delete_user_info_cache(request.app.state.redis, str(user.id))

        return ResponseUtil.success(data={
            "id": str(user.id), "file_id": file_record.id, "filename": file.filename,
            "size": result["size"], "file_type": file.content_type,
            "avatar_url": result["url"], "upload_time": datetime.now().isoformat(),
        }, msg="头像上传成功！")
    except Exception as e:
        logger.error(f"头像上传失败: {e}")
        return ResponseUtil.error(msg=f"头像上传失败: {str(e)}")


@userAPI.put("/resetPassword/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="重置用户密码")
@userAPI.post("/resetPassword/{id}", response_model=BaseResponse, response_class=JSONResponse, summary="重置用户密码")
@Log(title="重置用户密码", operation_type=OperationType.UPDATE)
@Auth(permission_list=['user:btn:reset_password'])
async def reset_user_password(request: Request, params: ResetPasswordParams, id: str = Path(description="用户ID"),
                              current_user: dict = Depends(AuthController.get_current_user)):
    operator_id = current_user.get("id")

    can_access = await PermissionService.can_access_user_data(str(operator_id), id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")

    success, msg = await UserService.reset_password(id, params.password, request.app.state.redis)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@userAPI.post("/changeTenant", response_model=BaseResponse, response_class=JSONResponse, summary="分配用户到租户")
@Log(title="分配用户到租户", operation_type=OperationType.UPDATE)
@Auth(permission_list=['user:btn:changeTenant'])
async def change_user_tenant(
    request: Request,
    params: ChangeTenantParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    operator_id = current_user.get("id")
    can_access = await PermissionService.can_access_user_data(str(operator_id), params.user_id)
    if not can_access:
        return ResponseUtil.error(msg="无权限操作该用户！")

    success, msg = await UserService.change_tenant(params.user_id, params.tenant_id, request.app.state.redis)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@userAPI.put("/updateBaseUserInfo", response_model=BaseResponse, response_class=JSONResponse, summary="更新基础个人信息")
@userAPI.post("/updateBaseUserInfo", response_model=BaseResponse, response_class=JSONResponse, summary="更新基础个人信息")
@Log(title="更新基础个人信息", operation_type=OperationType.UPDATE)
async def update_base_userinfo(params: UpdateBaseUserInfoParams, request: Request,
                               current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    success, msg = await UserService.update_base_info(user_id, params.name, params.gender, request.app.state.redis)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@userAPI.put("/updatePassword", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新密码")
@userAPI.post("/updatePassword", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新密码")
@Log(title="用户更新密码", operation_type=OperationType.UPDATE)
async def update_user_password(request: Request, oldPassword: str = Form(description="用户旧密码"),
                               newPassword: str = Form(description="用户新密码"),
                               current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    success, msg = await UserService.change_password(user_id, oldPassword, newPassword, request.app.state.redis)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@userAPI.put("/updatePhone", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新手机号")
@userAPI.post("/updatePhone", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新手机号")
@Log(title="用户更新手机号", operation_type=OperationType.UPDATE)
async def update_user_phone(request: Request, password: str = Form(description="用户密码"),
                            phone: str = Form(description="用户手机号"),
                            current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    success, msg = await UserService.change_phone(user_id, password, phone, request.app.state.redis)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@userAPI.put("/updateEmail", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新邮箱")
@userAPI.post("/updateEmail", response_class=JSONResponse, response_model=BaseResponse, summary="用户更新邮箱")
@Log(title="用户更新邮箱", operation_type=OperationType.UPDATE)
async def update_user_email(request: Request, password: str = Form(description="用户密码"),
                            email: str = Form(description="用户邮箱"),
                            current_user: dict = Depends(AuthController.get_current_user)):
    user_id = current_user.get("id")
    success, msg = await UserService.change_email(user_id, password, email, request.app.state.redis)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


# ==================== 租户成员管理 ====================


@userAPI.get("/tenantMembers", response_class=JSONResponse, summary="获取当前租户成员列表")
@Log(title="获取当前租户成员列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['user:btn:list'])
async def get_tenant_members(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    username: Optional[str] = Query(default=None, description="用户名"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        return ResponseUtil.error(msg="未选择租户！")

    filter_args = {"tenant_id": tenant_id, "is_del": False}
    if username:
        filter_args["user__username__contains"] = username

    total = await SystemTenantUser.filter(**filter_args).count()
    members = await SystemTenantUser.filter(**filter_args).offset(
        (page - 1) * pageSize
    ).limit(pageSize).prefetch_related("user", "department").values(
        id="id", user_id="user__id", username="user__username",
        nickname="user__nickname", email="user__email",
        department_id="department__id", department_name="department__name",
        user_type="user_type", status="status", created_at="created_at",
    )

    return ResponseUtil.success(data={"result": members, "total": total, "page": page, "pageSize": pageSize})


# ==================== 导入导出 API ====================


@userAPI.get("/export", response_class=JSONResponse, summary="导出用户数据")
@Log(title="导出用户数据", operation_type=OperationType.EXPORT)
@Auth(permission_list=['user:btn:export'])
async def export_user(
    request: Request,
    username: Optional[str] = Query(default=None, description="用户名"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from fastapi.responses import StreamingResponse
    filter_args = {}
    if username:
        filter_args["username__contains"] = username

    excel_file = await UserService.export_to_excel(filters=filter_args)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user.xlsx"},
    )


@userAPI.get("/export/template", response_class=JSONResponse, summary="下载用户导入模板")
@Log(title="下载用户导入模板", operation_type=OperationType.EXPORT)
@Auth(permission_list=['user:btn:import'])
async def download_user_template(request: Request):
    from fastapi.responses import StreamingResponse
    template_file = UserService.get_import_template()
    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user_template.xlsx"},
    )


@userAPI.post("/import", response_class=JSONResponse, response_model=BaseResponse, summary="导入用户数据")
@Log(title="导入用户数据", operation_type=OperationType.IMPORT)
@Auth(permission_list=['user:btn:import'])
async def import_user(
    request: Request,
    file: UploadFile = File(..., description="Excel文件"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from utils.password import PasswordUtil
    content = await file.read()

    async def process_row(row):
        if row.get("password"):
            row["password"] = await PasswordUtil.get_password_hash(row["password"])
        return row

    success_count, fail_count, errors = await UserService.import_from_excel(
        content, row_processor=process_row, current_user_id=current_user.get("id")
    )
    msg = f"导入完成，成功 {success_count} 条，失败 {fail_count} 条"
    if errors:
        msg += f"。错误信息：{'; '.join(errors[:5])}"
    return ResponseUtil.success(msg=msg, data={"success": success_count, "fail": fail_count, "errors": errors})
