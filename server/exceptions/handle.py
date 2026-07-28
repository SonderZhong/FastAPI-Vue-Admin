# _*_ coding : UTF-8 _*_
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from pydantic_validation_decorator import FieldValidationError
from starlette.responses import JSONResponse

from exceptions.exception import (
    AuthException,
    LoginException,
    ModelValidatorException,
    PermissionException,
    ServiceException,
    ServiceWarning,
)
from utils.log import logger
from utils.response import ResponseUtil
from utils.sentry import capture_exception


def handle_exception(app: FastAPI):
    """全局异常处理拦截器"""

    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        logger.warning(f"身份验证异常: {exc.message}")
        return ResponseUtil.unauthorized(data=exc.data, msg=exc.message)

    @app.exception_handler(LoginException)
    async def login_exception_handler(request: Request, exc: LoginException):
        logger.warning(f"登录异常: {exc.message}")
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    @app.exception_handler(ModelValidatorException)
    async def model_validator_exception_handler(request: Request, exc: ModelValidatorException):
        logger.warning(f"模型校验异常: {exc.message}")
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    @app.exception_handler(FieldValidationError)
    async def field_validation_error_handler(request: Request, exc: FieldValidationError):
        logger.warning(f"字段校验异常: {exc.message}")
        return ResponseUtil.failure(msg=exc.message)

    @app.exception_handler(PermissionException)
    async def permission_exception_handler(request: Request, exc: PermissionException):
        logger.warning(f"权限异常: {exc.message}")
        return ResponseUtil.forbidden(data=exc.data, msg=exc.message)

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        logger.error(f"服务异常: {exc.message}")
        capture_exception(exc, extra={"path": str(request.url), "method": request.method})
        return ResponseUtil.error(data=exc.data, msg=exc.message)

    @app.exception_handler(ServiceWarning)
    async def service_warning_handler(request: Request, exc: ServiceWarning):
        logger.warning(f"服务警告: {exc.message}")
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP 异常: {exc.detail}")
        return ResponseUtil.failure(msg=exc.detail)

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.exception(f"未捕获的异常: {str(exc)}")
        capture_exception(exc, extra={
            "path": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "unknown",
        })
        return ResponseUtil.error(msg="服务器内部错误")

    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"404 异常: {request.url} 未找到")
        return JSONResponse(
            content={"code": 404, "msg": "无效路径！", "data": None},
            status_code=404,
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc: HTTPException):
        logger.warning(f"405 异常: {request.method} 方法不允许")
        return JSONResponse(
            status_code=405,
            content={"code": 405, "msg": "请求方法错误", "data": None},
        )
