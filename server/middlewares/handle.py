# _*_ coding : UTF-8 _*_
from fastapi import FastAPI

from middlewares.cors import add_cors_middleware
from middlewares.gzip import add_gzip_middleware
from middlewares.auth_context import add_auth_context_middleware
from middlewares.encryption import EncryptionMiddleware


def handle_middleware(app: FastAPI):
    """全局中间件处理"""
    add_cors_middleware(app)
    add_gzip_middleware(app)
    add_auth_context_middleware(app)
    # RSA 数据加密中间件（根据配置动态启用）
    app.add_middleware(EncryptionMiddleware)
