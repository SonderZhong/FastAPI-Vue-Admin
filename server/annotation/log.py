# _*_ coding : UTF-8 _*_
# @Time : 2025/08/19 01:34
# @UpdateTime : 2025/08/19 01:34
# @Author : sonder
# @File : log.py
# @Software : PyCharm
# @Comment : 本程序
from __future__ import annotations  # 兼容 Python 3.9 以下泛型

import json
import time
from enum import Enum
from functools import lru_cache, wraps
from typing import Any, Dict, Literal

from fastapi import Request
from fastapi.responses import JSONResponse, ORJSONResponse, UJSONResponse
from user_agents import parse

# ---------------- 项目内部导入 ----------------
from annotation.auth import AuthController
from exceptions.exception import (
    LoginException,
    PermissionException,
    ServiceException,
    ServiceWarning,
)
from models import SystemLoginLog, SystemOperationLog
from utils.config import config
from utils.ip2region_util import get_ip_location
from utils.log import logger
from utils.response import ResponseUtil


class OperationType(Enum):
    """
    业务操作类型枚举

    枚举值说明：
    - OTHER：其他操作
    - INSERT：增加数据操作
    - DELETE：删除数据操作
    - UPDATE：更新数据操作
    - SELECT: 查询数据操作
    - IMPORT: 导入数据操作
    - EXPORT：导出数据操作
    - GRANT： 授权操作
    """
    OTHER = 0
    """
    其他操作
    """
    INSERT = 1
    """
    增加数据操作
    """
    DELETE = 2
    """
    删除数据操作
    """
    UPDATE = 3
    """
    更新数据操作
    """
    SELECT = 4
    """
    查询数据操作
    """
    IMPORT = 5
    """
    导入数据操作
    """
    EXPORT = 6
    """
    导出数据操作
    """
    GRANT = 7
    """
    授权操作
    """


# ---------------- 工具函数 ----------------
@lru_cache(maxsize=1024)
def _parse_ua(user_agent: str) -> Any:
    """
    解析 User-Agent 字符串并缓存结果
    :param user_agent: 原始 UA 字符串
    :return: user_agents.parsed 对象
    """
    return parse(user_agent)


def _request_meta(request: Request) -> Dict[str, Any]:
    """
    提取请求公共元数据
    :param request: FastAPI Request 实例
    :return: 包含 ip、ua、browser、os、method、path 的字典
    """
    ua_str: str = request.headers.get("User-Agent", "")
    ua = _parse_ua(ua_str)
    # 优先取 X-Forwarded-For，再取 request.client.host
    host: str = request.headers.get("X-Forwarded-For") or request.client.host
    return {
        "ip": host,
        "ua": ua_str,
        "browser": f"{ua.browser.family} {ua.browser.version_string}".strip(),
        "os": f"{ua.os.family} {ua.os.version_string}".strip(),
        "method": request.method,
        "path": str(request.url.path),
    }


# ---------------- 日志装饰器 ----------------
class Log:
    """
    通用日志装饰器
    1) 记录接口耗时、异常
    2) 登录日志 / 操作日志 双表分流
    """

    def __init__(
            self,
            title: str,
            operation_type: OperationType,
            log_type: Literal["login", "operation"] = "operation",
    ) -> None:
        """
        :param title: 接口中文描述
        :param operation_type: 业务操作类型枚举
        :param log_type: login 登录日志 / operation 操作日志
        """
        self.title: str = title
        self.operation_type: OperationType = operation_type
        self.log_type: Literal["login", "operation"] = log_type

    def __call__(self, func):
        """装饰器入口"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> JSONResponse:
            # ---------- 提取 request 对象 ----------
            # 支持 request 作为第一个位置参数或关键字参数
            request: Request = None
            if args and isinstance(args[0], Request):
                request = args[0]
            elif "request" in kwargs:
                request = kwargs["request"]
            
            if request is None:
                # 如果找不到 request，直接执行原函数
                return await func(*args, **kwargs)
            
            # ---------- 前置采集 ----------
            start_ns: int = time.perf_counter_ns()
            meta: Dict[str, Any] = _request_meta(request)

            # 读取 JSON 请求体（限制 1 MB）
            body: bytes = b""
            content_type: str = request.headers.get("Content-Type", "")
            if "application/json" in content_type:
                body = await request.body()
                if len(body) > 1_048_576:  # 1 MB
                    body = b""
            params_str: str = body.decode() or "{}"

            # IP 地理位置
            meta["location"] = (
                get_ip_location(meta["ip"])
                if config.app().ip_location_enabled
                else "内网IP"
            )

            # ---------- 执行原函数 ----------
            try:
                result = await func(*args, **kwargs)
                success: bool = True
                status_code: int = 200
            except (ServiceWarning, LoginException) as e:
                logger.warning(e.message)
                result = ResponseUtil.failure(msg=e.message, data=e.data)
                success, status_code = False, 400
            except (ServiceException, PermissionException) as e:
                logger.error(e.message)
                if isinstance(e, ServiceException):
                    resp = ResponseUtil.error(msg=e.message, data=e.data)
                else:
                    resp = ResponseUtil.forbidden(msg=e.message, data=e.data)
                result = resp
                success, status_code = False, 403
            except Exception as e:
                logger.exception(e)
                result = ResponseUtil.error(msg=str(e))
                success, status_code = False, 500

            # 耗时（毫秒）
            cost_ms: int = int((time.perf_counter_ns() - start_ns) // 1_000_000)

            # ---------- 序列化响应 ----------
            resp_dict: Dict[str, Any]
            if isinstance(result, (JSONResponse, ORJSONResponse, UJSONResponse)):
                resp_dict = json.loads(result.body.decode())
            else:
                resp_dict = {"code": status_code, "message": "success" if success else "failed"}

            # ---------- 写日志 ----------
            token: str | None = request.headers.get("Authorization")
            if self.log_type == "login":
                session_id: str | None = getattr(request.app.state, "session_id", None)
                user_id: int | None = getattr(request.app.state, "login_user_id", None)
                if user_id:
                    await SystemLoginLog.create(
                        user_id=user_id,
                        login_ip=meta["ip"],
                        login_location=meta["location"],
                        browser=meta["browser"],
                        os=meta["os"],
                        status=int(success),
                        session_id=session_id,
                    )
            else:
                user: Dict[str, Any] = await AuthController.get_current_user(
                    request, token
                )
                await SystemOperationLog.create(
                    operation_name=self.title,
                    operation_type=self.operation_type.value,
                    request_method=meta["method"],
                    request_path=meta["path"],
                    operator_id=user["id"],
                    department_id=user.get("department_id"),
                    host=meta["ip"],
                    location=meta["location"],
                    user_agent=meta["ua"],
                    browser=meta["browser"],
                    os=meta["os"],
                    request_params=params_str,
                    response_result=json.dumps(resp_dict, ensure_ascii=False),
                    status=int(success),
                    cost_time=cost_ms,
                )

            return result

        return wrapper
