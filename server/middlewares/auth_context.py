# _*_ coding : UTF-8 _*_
from typing import List, Optional

from fastapi import Request
from jose import jwt, ExpiredSignatureError
from jose.exceptions import JWEError, JWEInvalidAuth
from starlette.middleware.base import BaseHTTPMiddleware

from utils.permission import UserType
from utils.config import config
from utils.get_redis import RedisKeyConfig
from utils.log import logger


WHITE_LIST: List[str] = [
    "/auth/login",
    "/auth/register",
    "/auth/captcha",
    "/auth/code",
    "/auth/logout",
    "/auth/refreshToken",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/captcha",
    "/api/auth/code",
    "/api/auth/logout",
    "/api/auth/refreshToken",
    "/api/notification/ws",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/scalar",
    "/assets",
    "/api/assets",
]

LOGIN_ONLY_LIST: List[str] = [
    "/auth/info",
    "/auth/routes",
    "/api/auth/info",
    "/api/auth/routes",
]


def is_white_listed(path: str) -> bool:
    return any(path.startswith(white_path) for white_path in WHITE_LIST)


def is_login_only(path: str) -> bool:
    return any(path.startswith(login_path) for login_path in LOGIN_ONLY_LIST)


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Parse auth context and attach it to request.state."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if is_white_listed(path):
            return await call_next(request)

        user_info = await self._get_user_from_token(request)
        if user_info:
            request.state.user_id = user_info.get("user_id")
            request.state.user_type = user_info.get("user_type")
            request.state.tenant_id = user_info.get("tenant_id")
            request.state.session_id = user_info.get("session_id")
            request.state.department_id = user_info.get("department_id")

        if is_login_only(path):
            return await call_next(request)

        return await call_next(request)

    async def _get_user_from_token(self, request: Request) -> Optional[dict]:
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return None

            token = auth_header
            if token.startswith("Bearer "):
                token = token.split(" ", 1)[1]

            payload = jwt.decode(
                token=token,
                key=config.jwt().secret_key,
                algorithms=[config.jwt().algorithm],
            )

            user_id = payload.get("id")
            session_id = payload.get("session_id")
            if not user_id:
                return None

            redis = request.app.state.redis
            redis_token = await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}")
            if not redis_token:
                return None

            from modules import SystemUser, SystemTenantUser

            user = await SystemUser.filter(id=user_id, is_del=False).first()
            if not user:
                return None

            user_type = UserType.NORMAL_USER
            tenant_id = None
            department_id = None

            tenant_user = await SystemTenantUser.filter(user_id=user_id, is_del=False).first()
            if tenant_user:
                user_type = tenant_user.user_type
                tenant_id = str(tenant_user.tenant_id) if tenant_user.tenant_id else None
                department_id = str(tenant_user.department_id) if tenant_user.department_id else None

            return {
                "user_id": user_id,
                "user_type": user_type,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "department_id": department_id,
            }

        except (JWEInvalidAuth, ExpiredSignatureError, JWEError):
            return None
        except Exception as exc:
            logger.error(f"Parse token in auth context middleware failed: {exc}")
            return None


def add_auth_context_middleware(app):
    app.add_middleware(AuthContextMiddleware)
    logger.info("认证上下文中间件已加载")
