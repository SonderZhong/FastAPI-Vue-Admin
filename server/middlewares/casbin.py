# _*_ coding : UTF-8 _*_
# @Time : 2025/12/26
# @Author : sonder
# @File : casbin.py
# @Comment : Casbin 权限验证中间件 - RBAC + 部门层级数据权限

from typing import List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, ExpiredSignatureError
from jose.exceptions import JWEInvalidAuth, JWEError

from utils.casbin import CasbinEnforcer, UserType
from utils.config import config
from utils.log import logger
from utils.get_redis import RedisKeyConfig


# 白名单路径 - 不需要权限验证
WHITE_LIST: List[str] = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/captcha",
    "/api/auth/code",
    "/api/auth/logout",
    "/api/auth/refreshToken",
    "/api/casbin/data-scope-info",
    "/api/notification/ws",  # WebSocket 连接（内部验证 token）
    "/openapi.json",
    "/docs",
    "/redoc",
    "/scalar",
    "/assets",
    "/api/assets",
]

# 仅需登录即可访问的路径（不检查 Casbin 策略）
LOGIN_ONLY_LIST: List[str] = [
    "/api/auth/info",
    "/api/auth/routes",
    "/api/casbin/data-scope",
]


def is_white_listed(path: str) -> bool:
    """检查路径是否在白名单中"""
    for white_path in WHITE_LIST:
        if path.startswith(white_path):
            return True
    return False


def is_login_only(path: str) -> bool:
    """检查路径是否仅需登录"""
    for login_path in LOGIN_ONLY_LIST:
        if path.startswith(login_path):
            return True
    return False


class CasbinMiddleware(BaseHTTPMiddleware):
    """
    Casbin 权限验证中间件
    
    验证流程:
    1. 检查是否在白名单中 -> 直接放行
    2. 解析 Token 获取用户信息
    3. 检查是否仅需登录 -> 登录即放行
    4. 获取用户类型，超级管理员/管理员直接放行
    5. 使用 Casbin 检查 API 权限
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # 1. 白名单路径直接放行
        if is_white_listed(path):
            return await call_next(request)
        
        # 2. 解析 Token 获取用户信息
        user_info = await self._get_user_from_token(request)
        
        if not user_info:
            # 未登录，由后续的认证依赖处理
            return await call_next(request)
        
        # 将用户信息存入 request.state 供后续使用
        request.state.user_id = user_info.get("user_id")
        request.state.user_type = user_info.get("user_type")
        request.state.session_id = user_info.get("session_id")
        
        # 3. 仅需登录的路径
        if is_login_only(path):
            return await call_next(request)
        
        # 4. 超级管理员和管理员直接放行
        user_type = user_info.get("user_type", UserType.NORMAL_USER)
        if user_type in (UserType.SUPER_ADMIN, UserType.ADMIN):
            return await call_next(request)
        
        # 5. 使用 Casbin 检查 API 权限
        try:
            user_id = str(user_info.get("user_id"))
            
            # 先检查用户直接权限
            has_permission = await CasbinEnforcer.check_permission(
                sub=user_id,
                obj=path,
                act=method
            )
            
            if not has_permission:
                # 检查用户角色权限
                roles = await CasbinEnforcer.get_roles_for_user(user_id)
                for role in roles:
                    if await CasbinEnforcer.check_permission(role, path, method):
                        has_permission = True
                        break
            
            if not has_permission:
                logger.warning(f"权限拒绝: user={user_id}, path={path}, method={method}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": 403,
                        "msg": "没有访问权限",
                        "data": None
                    }
                )
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Casbin 权限验证异常: {e}")
            # 出错时放行，避免阻塞正常请求
            return await call_next(request)
    
    async def _get_user_from_token(self, request: Request) -> dict:
        """从 Token 解析用户信息"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return None
            
            token = auth_header
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            
            payload = jwt.decode(
                token=token,
                key=config.jwt().secret_key,
                algorithms=[config.jwt().algorithm],
            )
            
            user_id = payload.get("id")
            session_id = payload.get("session_id")
            
            if not user_id:
                return None
            
            # 验证 session 是否有效
            redis = request.app.state.redis
            redis_token = await redis.get(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
            )
            if not redis_token:
                return None
            
            # 获取用户类型
            from models import SystemUser
            user = await SystemUser.filter(id=user_id, is_del=False).first()
            if not user:
                return None
            
            return {
                "user_id": user_id,
                "user_type": user.user_type,
                "session_id": session_id,
                "department_id": str(user.department_id) if user.department_id else None
            }
            
        except (JWEInvalidAuth, ExpiredSignatureError, JWEError):
            return None
        except Exception as e:
            logger.error(f"解析 Token 异常: {e}")
            return None


def add_casbin_middleware(app):
    """添加 Casbin 中间件到 FastAPI 应用"""
    app.add_middleware(CasbinMiddleware)
    logger.info("Casbin 权限中间件已加载")
