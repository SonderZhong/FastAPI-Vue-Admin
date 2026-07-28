# _*_ coding : UTF-8 _*_
# @Comment : 认证管理 API

import uuid
from datetime import timedelta, datetime

from fastapi import APIRouter, Request, Depends
from starlette.responses import JSONResponse

from annotation.auth import CustomOAuth2PasswordRequestForm, AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse
from modules.auth.schema import (
    GetCaptchaResponse, LoginResponse, GetEmailCodeParams,
    ForgotPasswordParams, ForgotPasswordResetParams, SelectTenantParams,
)
from modules.user.schema import RegisterUserParams
from modules.auth.service import AuthService
from utils.mail import Email
from utils.response import ResponseUtil

authAPI = APIRouter(prefix="/auth")


@authAPI.get(
    "/captcha",
    response_class=JSONResponse,
    response_model=GetCaptchaResponse,
    summary="获取验证码",
)
async def get_captcha(request: Request):
    redis = request.app.state.redis
    config = await AuthService.get_captcha_config(redis)

    if config["captcha_enabled"]:
        captcha_type = await redis.get("system_config:account_captcha_type") or "0"
        captcha_data = await AuthService.generate_captcha(redis, captcha_type)
        return ResponseUtil.success(
            data={
                **captcha_data,
                "captcha_enabled": True,
                "register_enabled": config["register_enabled"],
                "captcha_type": captcha_type,
            }
        )
    else:
        return ResponseUtil.success(
            data={
                "uuid": None,
                "captcha": None,
                "captcha_enabled": False,
                "register_enabled": config["register_enabled"],
                "captcha_type": "0",
            }
        )


@authAPI.post("/login", response_class=JSONResponse, summary="登录")
@Log(operation_type=OperationType.GRANT, title="登录", log_type="login")
async def login(request: Request, params: CustomOAuth2PasswordRequestForm = Depends()):
    result = await AuthService.login(
        request,
        username=params.username,
        password=params.password,
        login_days=params.login_days,
        code=params.code,
        captcha_uuid=params.uuid,
    )

    if not result["success"]:
        return ResponseUtil.error(msg=result["msg"])

    if result.get("request_from_swagger") or result.get("request_from_redoc"):
        return {
            "access_token": result["accessToken"],
            "token_type": "Bearer",
            "expires_in": result["expiresTime"],
        }
    return ResponseUtil.success(
        data={
            "accessToken": result["accessToken"],
            "refreshToken": result["refreshToken"],
            "tenant_id": result.get("tenant_id"),
            "available_tenants": result.get("available_tenants", []),
        }
    )


@authAPI.post(
    "/register",
    response_class=JSONResponse,
    response_model=LoginResponse,
    summary="用户注册",
)
async def register(request: Request, params: RegisterUserParams):
    result = await AuthService.register(
        request.app.state.redis, params.dict(exclude_unset=True)
    )
    if result["success"]:
        return ResponseUtil.success(msg=result["msg"])
    return ResponseUtil.error(msg=result["msg"])


@authAPI.post("/forgot-password/send-code", response_class=JSONResponse, summary="忘记密码 - 发送验证码")
async def forgot_password_send_code(request: Request, params: ForgotPasswordParams):
    result = await AuthService.forgot_password_send_code(request, params.email)
    if result["success"]:
        return ResponseUtil.success(msg=result["msg"])
    return ResponseUtil.error(msg=result["msg"])


@authAPI.post("/forgot-password/reset", response_class=JSONResponse, summary="忘记密码 - 重置密码")
async def forgot_password_reset(request: Request, params: ForgotPasswordResetParams):
    result = await AuthService.forgot_password_reset(
        request, params.email, params.code, params.new_password
    )
    if result["success"]:
        return ResponseUtil.success(msg=result["msg"])
    return ResponseUtil.error(msg=result["msg"])


@authAPI.post(
    "/code",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取邮件验证码",
)
async def get_code(request: Request, params: GetEmailCodeParams):
    result = await Email.send_email(
        request, username=params.username, title=params.title, mail=params.mail
    )
    if result:
        return ResponseUtil.success(msg="验证码发送成功！")
    return ResponseUtil.error(msg="验证码发送失败！")


@authAPI.get("/public-key", response_class=JSONResponse, summary="获取RSA公钥")
async def get_public_key(request: Request):
    """获取RSA公钥（用于前端加密请求数据）"""
    dynamic_config = getattr(request.app.state, "dynamic_config", None)
    if not dynamic_config:
        return ResponseUtil.error(msg="系统未就绪")

    encryption_enabled = await dynamic_config.get("encryption_enabled", "false")
    if encryption_enabled != "true":
        return ResponseUtil.error(msg="数据加密未启用")

    redis = request.app.state.redis
    key_size = int(await dynamic_config.get("encryption_key_size", "2048"))
    from utils.encryption import RSAEncryption
    public_pem, _ = await RSAEncryption.get_or_generate_keypair(redis, key_size)

    return ResponseUtil.success(data={"public_key": public_pem})


@authAPI.post("/select-tenant", response_class=JSONResponse, summary="选择租户")
@Log(title="选择租户", operation_type=OperationType.GRANT)
async def select_tenant(
    request: Request,
    params: SelectTenantParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    result = await AuthService.select_tenant(
        request, current_user.get("id"), params.tenant_id
    )
    if result["success"]:
        return ResponseUtil.success(
            msg=result["msg"],
            data={"tenant_id": result.get("tenant_id"), "tenant_name": result.get("tenant_name")},
        )
    return ResponseUtil.error(msg=result["msg"])


@authAPI.get(
    "/info",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取用户信息",
)
@Log(title="获取用户信息", operation_type=OperationType.SELECT)
async def info(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    data = {
        **current_user,
        "available_tenants": await AuthService._get_available_tenants(str(current_user.get("id"))),
    }
    return ResponseUtil.success(data=data)


@authAPI.get(
    "/routes",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取用户路由",
)
@Log(title="获取用户路由", operation_type=OperationType.SELECT)
async def get_user_routes(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    routes = await AuthService.get_user_routes(request.app.state.redis, current_user)
    return ResponseUtil.success(code=200, data=routes)


@authAPI.post(
    "/logout",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="用户登出",
)
@Log(title="退出登录", operation_type=OperationType.GRANT)
async def logout(request: Request, status: bool = Depends(AuthController.logout)):
    if status:
        return ResponseUtil.success(data="退出成功！")
    return ResponseUtil.error(data="登出失败！")


@authAPI.post(
    "/refreshToken",
    response_class=JSONResponse,
    response_model=LoginResponse,
    summary="刷新token",
)
@Log(title="刷新token", operation_type=OperationType.GRANT)
async def refresh_token(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    session_id = uuid.uuid4().__str__()
    accessToken = await AuthController.create_token(
        data={
            "user": current_user,
            "id": current_user.get("id"),
            "session_id": session_id,
        },
        expires_delta=timedelta(minutes=2 * 24 * 60),
    )
    expiresTime = (datetime.now() + timedelta(minutes=2 * 24 * 60)).timestamp()
    refreshToken = await AuthController.create_token(
        data={
            "user": current_user,
            "id": current_user.get("id"),
            "session_id": session_id,
        },
        expires_delta=timedelta(minutes=(4 * 24 + 2) * 60),
    )
    return ResponseUtil.success(
        data={
            "accessToken": accessToken,
            "refreshToken": refreshToken,
            "expiresTime": expiresTime,
        }
    )
