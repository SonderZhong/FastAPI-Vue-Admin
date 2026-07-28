# _*_ coding : UTF-8 _*_
"""
RSA 加密中间件

- 请求体加密 → 解密后传递给路由处理
- 响应体加密 → 加密后返回给前端
- 日志中存储原始（未加密）数据
"""

import json
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from utils.encryption import RSAEncryption
from utils.log import logger


class EncryptionMiddleware(BaseHTTPMiddleware):
    """RSA 数据加密中间件"""

    # 不需要加密的路径
    EXCLUDE_PATHS = {
        "/auth/captcha",
        "/auth/login",
        "/auth/register",
        "/auth/forgot-password/send-code",
        "/auth/forgot-password/reset",
        "/auth/select-tenant",
        "/auth/code",
        "/api/setup/",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/assets/",
        "/files/",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否启用加密
        dynamic_config = getattr(request.app.state, "dynamic_config", None)
        if not dynamic_config:
            return await call_next(request)

        encryption_enabled = await dynamic_config.get("encryption_enabled", "false")
        if encryption_enabled != "true":
            return await call_next(request)

        # 检查是否在排除路径中
        path = request.url.path
        for exclude_path in self.EXCLUDE_PATHS:
            if path.startswith(exclude_path):
                return await call_next(request)

        # 检查请求头是否标记为加密
        is_encrypted = request.headers.get("X-Encrypted") == "true"

        # 解密请求体
        body = b""
        if is_encrypted:
            try:
                body = await request.body()
                if body:
                    encrypted_text = body.decode("utf-8")
                    redis = request.app.state.redis
                    decrypted_text = await RSAEncryption.decrypt_request(
                        redis, encrypted_text
                    )
                    # 替换请求体
                    request._body = decrypted_text.encode("utf-8")
            except Exception as e:
                logger.warning(f"请求解密失败: {e}")
                return Response(
                    content=json.dumps(
                        {"code": 400, "msg": "数据解密失败", "success": False}
                    ),
                    media_type="application/json",
                    status_code=400,
                )

        # 执行请求处理
        response = await call_next(request)

        # 加密响应体（仅对 JSON 响应加密）
        if is_encrypted and response.headers.get("content-type", "").startswith(
            "application/json"
        ):
            try:
                # 读取响应体
                response_body = b""
                async for chunk in response.body_iterator:
                    if isinstance(chunk, str):
                        response_body += chunk.encode("utf-8")
                    else:
                        response_body += chunk

                # 加密
                redis = request.app.state.redis
                encrypted = await RSAEncryption.encrypt_response(
                    redis, response_body.decode("utf-8")
                )

                return Response(
                    content=encrypted,
                    media_type="text/plain",
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except Exception as e:
                logger.error(f"响应加密失败: {e}")

        return response
