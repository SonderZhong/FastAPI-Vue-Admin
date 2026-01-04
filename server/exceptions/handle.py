# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:22
# @UpdateTime : 2025/08/04 01:22
# @Author : sonder
# @File : handle.py
# @Software : PyCharm
# @Comment : 本程序
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


def handle_exception(app: FastAPI):
    """
    全局异常处理拦截器。
    - 捕获并处理所有异常，返回统一的接口响应格式。
    """

    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        """
        处理自定义身份验证异常（AuthException）。
        - 返回 401 未授权响应。
        """
        logger.warning(f"身份验证异常: {exc.message}")
        return ResponseUtil.unauthorized(data=exc.data, msg=exc.message)

    @app.exception_handler(LoginException)
    async def login_exception_handler(request: Request, exc: LoginException):
        """
        处理自定义登录异常（LoginException）。
        - 返回 400 失败响应。
        """
        logger.warning(f"登录异常: {exc.message}")
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    @app.exception_handler(ModelValidatorException)
    async def model_validator_exception_handler(request: Request, exc: ModelValidatorException):
        """
        处理自定义模型校验异常（ModelValidatorException）。
        - 返回 400 失败响应。
        """
        logger.warning(f"模型校验异常: {exc.message}")
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    @app.exception_handler(FieldValidationError)
    async def field_validation_error_handler(request: Request, exc: FieldValidationError):
        """
        处理字段校验异常（FieldValidationError）。
        - 返回 400 失败响应。
        """
        logger.warning(f"字段校验异常: {exc.message}")
        return ResponseUtil.failure(msg=exc.message)

    @app.exception_handler(PermissionException)
    async def permission_exception_handler(request: Request, exc: PermissionException):
        """
        处理自定义权限异常（PermissionException）。
        - 返回 403 未授权响应。
        """
        logger.warning(f"权限异常: {exc.message}")
        return ResponseUtil.forbidden(data=exc.data, msg=exc.message)

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        """
        处理自定义服务异常（ServiceException）。
        - 返回 500 错误响应。
        """
        logger.error(f"服务异常: {exc.message}")
        return ResponseUtil.error(data=exc.data, msg=exc.message)

    @app.exception_handler(ServiceWarning)
    async def service_warning_handler(request: Request, exc: ServiceWarning):
        """
        处理自定义服务警告（ServiceWarning）。
        - 返回 400 失败响应。
        """
        logger.warning(f"服务警告: {exc.message}")
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        处理 FastAPI 的 HTTP 异常。
        - 返回统一的错误响应格式。
        """
        logger.warning(f"HTTP 异常: {exc.detail}")
        return ResponseUtil.failure(msg=exc.detail)

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        """
        处理其他未捕获的异常。
        - 返回 500 错误响应。
        """
        logger.exception(f"未捕获的异常: {str(exc)}")
        return ResponseUtil.error(msg="服务器内部错误")

    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: HTTPException):
        """
        处理 404 未找到资源异常。
        - 返回 404 失败响应。
        """
        logger.warning(f"404 异常: {request.url} 未找到")
        return JSONResponse(
            content={"code": 404, "msg": "无效路径！", "data": None},
            status_code=404,
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc: HTTPException):
        """
        处理 405 方法不允许异常。
        - 返回 405 失败响应。
        """
        logger.warning(f"405 异常: {request.method} 方法不允许")
        return JSONResponse(
            status_code=405,
            content={"code": 405, "msg": "请求方法错误", "data": None},
        )
