# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 19:57
# @UpdateTime : 2025/08/03 19:57
# @Author : sonder
# @File : response.py
# @Software : PyCharm
# @Comment : 本程序
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel


class HttpStatusConstant:
    """
    定义 HTTP 状态码的常量，描述不同操作的响应结果。

    属性:
        SUCCESS: 表示操作成功，HTTP 状态码 200。
        CREATED: 表示资源已成功创建，HTTP 状态码 201。
        ACCEPTED: 表示请求已被接受，HTTP 状态码 202。
        NO_CONTENT: 表示操作成功但无内容返回，HTTP 状态码 204。
        MOVED_PERM: 表示资源已被永久移除，HTTP 状态码 301。
        SEE_OTHER: 表示重定向到其他资源，HTTP 状态码 303。
        NOT_MODIFIED: 表示资源未被修改，HTTP 状态码 304。
        BAD_REQUEST: 参数错误，HTTP 状态码 400。
        UNAUTHORIZED: 表示未授权，HTTP 状态码 401。
        FORBIDDEN: 表示禁止访问，HTTP 状态码 403。
        NOT_FOUND: 表示资源或服务未找到，HTTP 状态码 404。
        BAD_METHOD: 不允许的 HTTP 方法，HTTP 状态码 405。
        CONFLICT: 表示资源冲突，HTTP 状态码 409。
        UNSUPPORTED_TYPE: 不支持的数据或媒体类型，HTTP 状态码 415。
        ERROR: 表示系统内部错误，HTTP 状态码 500。
        NOT_IMPLEMENTED: 接口未实现，HTTP 状态码 501。
        WARN: 系统警告消息，自定义状态码 601。
    """

    SUCCESS = 200
    """表示操作成功，HTTP 状态码 200。"""

    CREATED = 201
    """表示资源已成功创建，HTTP 状态码 201。"""

    ACCEPTED = 202
    """表示请求已被接受，HTTP 状态码 202。"""

    NO_CONTENT = 204
    """表示操作成功但无内容返回，HTTP 状态码 204。"""

    MOVED_PERM = 301
    """表示资源已被永久移除，HTTP 状态码 301。"""

    SEE_OTHER = 303
    """表示重定向到其他资源，HTTP 状态码 303。"""

    NOT_MODIFIED = 304
    """表示资源未被修改，HTTP 状态码 304。"""

    BAD_REQUEST = 400
    """参数错误，HTTP 状态码 400。"""

    UNAUTHORIZED = 401
    """表示未授权，HTTP 状态码 401。"""

    FORBIDDEN = 403
    """表示禁止访问，HTTP 状态码 403。"""

    NOT_FOUND = 404
    """表示资源或服务未找到，HTTP 状态码 404。"""

    BAD_METHOD = 405
    """不允许的 HTTP 方法，HTTP 状态码 405。"""

    CONFLICT = 409
    """表示资源冲突，HTTP 状态码 409。"""

    UNSUPPORTED_TYPE = 415
    """不支持的数据或媒体类型，HTTP 状态码 415。"""

    ERROR = 500
    """表示系统内部错误，HTTP 状态码 500。"""

    NOT_IMPLEMENTED = 501
    """接口未实现，HTTP 状态码 501。"""

    WARN = 601
    """系统警告消息，自定义状态码 601。"""


class ResponseUtil:
    """
    响应工具类，用于统一封装接口返回格式。
    """

    @classmethod
    def _build_response(
            cls,
            code: int,
            msg: str,
            data: Optional[Any] = None,
            rows: Optional[Any] = None,
            dict_content: Optional[Dict] = None,
            model_content: Optional[BaseModel] = None,
            success: bool = True,
    ) -> Dict:
        """
        构建统一的响应结果字典。

        :param code: 状态码
        :param msg: 响应消息
        :param data: 响应数据
        :param rows: 响应行数据（通常用于分页）
        :param dict_content: 自定义字典内容
        :param model_content: 自定义 Pydantic 模型内容
        :param success: 是否成功
        :return: 统一的响应结果字典
        """
        result = {
            "code": code,
            "msg": msg,
            "success": success,
            "time": datetime.now().isoformat(),  # 添加时间戳
        }

        # 添加可选字段
        if data is not None:
            result["data"] = data
        if rows is not None:
            result["rows"] = rows
        if dict_content is not None:
            result.update(dict_content)
        if model_content is not None:
            result.update(model_content.model_dump(by_alias=True))

        return result

    @classmethod
    def success(
            cls,
            code: int = HttpStatusConstant.SUCCESS,
            msg: str = "操作成功",
            data: Optional[Any] = None,
            rows: Optional[Any] = None,
            dict_content: Optional[Dict] = None,
            model_content: Optional[BaseModel] = None,
    ) -> JSONResponse:
        """
        成功响应方法。
        :param code: 响应状态码
        :param msg: 响应消息，默认为 "操作成功"
        :param data: 响应数据
        :param rows: 响应行数据（通常用于分页）
        :param dict_content: 自定义字典内容
        :param model_content: 自定义 Pydantic 模型内容
        :return: JSONResponse 对象
        """
        result = cls._build_response(
            code=code,
            msg=msg,
            data=data,
            rows=rows,
            dict_content=dict_content,
            model_content=model_content,
            success=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

    @classmethod
    def failure(
            cls,
            code: int = HttpStatusConstant.BAD_REQUEST,
            msg: str = "操作失败",
            data: Optional[Any] = None,
            rows: Optional[Any] = None,
            dict_content: Optional[Dict] = None,
            model_content: Optional[BaseModel] = None,
    ) -> JSONResponse:
        """
        失败响应方法。
        :param code: 响应状态码
        :param msg: 响应消息，默认为 "操作失败"
        :param data: 响应数据
        :param rows: 响应行数据（通常用于分页）
        :param dict_content: 自定义字典内容
        :param model_content: 自定义 Pydantic 模型内容
        :return: JSONResponse 对象
        """
        result = cls._build_response(
            code=code,
            msg=msg,
            data=data,
            rows=rows,
            dict_content=dict_content,
            model_content=model_content,
            success=False,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

    @classmethod
    def unauthorized(
            cls,
            code: int = HttpStatusConstant.UNAUTHORIZED,
            msg: str = "登录信息已过期，访问系统资源失败",
            data: Optional[Any] = None,
            rows: Optional[Any] = None,
            dict_content: Optional[Dict] = None,
            model_content: Optional[BaseModel] = None,
    ) -> JSONResponse:
        """
        未认证响应方法。
        :param code: 响应状态码
        :param msg: 响应消息，默认为 "登录信息已过期，访问系统资源失败"
        :param data: 响应数据
        :param rows: 响应行数据（通常用于分页）
        :param dict_content: 自定义字典内容
        :param model_content: 自定义 Pydantic 模型内容
        :return: JSONResponse 对象
        """
        result = cls._build_response(
            code=code,
            msg=msg,
            data=data,
            rows=rows,
            dict_content=dict_content,
            model_content=model_content,
            success=False,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

    @classmethod
    def forbidden(
            cls,
            code: int = HttpStatusConstant.FORBIDDEN,
            msg: str = "该用户无此接口权限",
            data: Optional[Any] = None,
            rows: Optional[Any] = None,
            dict_content: Optional[Dict] = None,
            model_content: Optional[BaseModel] = None,
    ) -> JSONResponse:
        """
        未授权响应方法。
        :param code: 响应状态码
        :param msg: 响应消息，默认为 "该用户无此接口权限"
        :param data: 响应数据
        :param rows: 响应行数据（通常用于分页）
        :param dict_content: 自定义字典内容
        :param model_content: 自定义 Pydantic 模型内容
        :return: JSONResponse 对象
        """
        result = cls._build_response(
            code=code,
            msg=msg,
            data=data,
            rows=rows,
            dict_content=dict_content,
            model_content=model_content,
            success=False,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

    @classmethod
    def error(
            cls,
            code: int = HttpStatusConstant.ERROR,
            msg: str = "接口异常",
            data: Optional[Any] = None,
            rows: Optional[Any] = None,
            dict_content: Optional[Dict] = None,
            model_content: Optional[BaseModel] = None,
    ) -> JSONResponse:
        """
        错误响应方法。
        :param code: 响应状态码
        :param msg: 响应消息，默认为 "接口异常"
        :param data: 响应数据
        :param rows: 响应行数据（通常用于分页）
        :param dict_content: 自定义字典内容
        :param model_content: 自定义 Pydantic 模型内容
        :return: JSONResponse 对象
        """
        result = cls._build_response(
            code=code,
            msg=msg,
            data=data,
            rows=rows,
            dict_content=dict_content,
            model_content=model_content,
            success=False,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

    @classmethod
    def streaming(cls, data: Any) -> StreamingResponse:
        """
        流式响应方法。

        :param data: 流式传输的内容
        :return: StreamingResponse 对象
        """
        return StreamingResponse(content=data, status_code=status.HTTP_200_OK)
