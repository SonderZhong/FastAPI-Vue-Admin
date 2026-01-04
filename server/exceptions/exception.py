# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:20
# @UpdateTime : 2025/08/04 01:20
# @Author : sonder
# @File : exception.py
# @Software : PyCharm
# @Comment : 本程序
from typing import Optional, Any

from fastapi.responses import JSONResponse

from utils.response import ResponseUtil


class LoginException(Exception):
    """
    自定义登录异常。
    - 用于处理登录相关的异常情况。
    """

    def __init__(self, message: str = "登录失败", data: Optional[Any] = None):
        """
        初始化登录异常。

        :param message: 异常消息，默认为 "登录失败"
        :param data: 异常相关的数据
        """
        self.message = message
        self.data = data

    def to_response(self) -> JSONResponse:
        """
        将异常转换为统一的响应格式。

        :return: JSONResponse 对象
        """
        return ResponseUtil.failure(msg=self.message, data=self.data)


class AuthException(Exception):
    """
    自定义令牌异常。
    - 用于处理身份验证相关的异常情况。
    """

    def __init__(self, message: str = "身份验证失败", data: Optional[Any] = None):
        """
        初始化令牌异常。

        :param message: 异常消息，默认为 "身份验证失败"
        :param data: 异常相关的数据
        """
        self.message = message
        self.data = data

    def to_response(self) -> JSONResponse:
        """
        将异常转换为统一的响应格式。

        :return: JSONResponse 对象
        """
        return ResponseUtil.unauthorized(msg=self.message, data=self.data)


class PermissionException(Exception):
    """
    自定义权限异常。
    - 用于处理权限相关的异常情况。
    """

    def __init__(self, message: str = "权限不足", data: Optional[Any] = None):
        """
        初始化权限异常。

        :param message: 异常消息，默认为 "权限不足"
        :param data: 异常相关的数据
        """
        self.message = message
        self.data = data

    def to_response(self) -> JSONResponse:
        """
        将异常转换为统一的响应格式。

        :return: JSONResponse 对象
        """
        return ResponseUtil.forbidden(msg=self.message, data=self.data)


class ServiceException(Exception):
    """
    自定义服务异常。
    - 用于处理服务层逻辑相关的异常情况。
    """

    def __init__(self, message: str = "服务异常", data: Optional[Any] = None):
        """
        初始化服务异常。

        :param message: 异常消息，默认为 "服务异常"
        :param data: 异常相关的数据
        """
        self.message = message
        self.data = data

    def to_response(self) -> JSONResponse:
        """
        将异常转换为统一的响应格式。

        :return: JSONResponse 对象
        """
        return ResponseUtil.error(msg=self.message, data=self.data)


class ServiceWarning(Exception):
    """
    自定义服务警告。
    - 用于处理服务层逻辑中的警告情况（非致命错误）。
    """

    def __init__(self, message: str = "服务警告", data: Optional[Any] = None):
        """
        初始化服务警告。

        :param message: 警告消息，默认为 "服务警告"
        :param data: 警告相关的数据
        """
        self.message = message
        self.data = data

    def to_response(self) -> JSONResponse:
        """
        将警告转换为统一的响应格式。

        :return: JSONResponse 对象
        """
        return ResponseUtil.failure(msg=self.message, data=self.data)


class ModelValidatorException(Exception):
    """
    自定义模型校验异常。
    - 用于处理数据模型校验失败的异常情况。
    """

    def __init__(self, message: str = "数据校验失败", data: Optional[Any] = None):
        """
        初始化模型校验异常。

        :param message: 异常消息，默认为 "数据校验失败"
        :param data: 异常相关的数据
        """
        self.message = message
        self.data = data

    def to_response(self) -> JSONResponse:
        """
        将异常转换为统一的响应格式。

        :return: JSONResponse 对象
        """
        return ResponseUtil.failure(msg=self.message, data=self.data)
