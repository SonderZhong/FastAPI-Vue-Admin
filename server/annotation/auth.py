# _*_ coding : UTF-8 _*_
# @Comment : auth and permission helpers

import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Union

from fastapi import Depends, Form, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, jwt
from jose.exceptions import JWEError, JWEInvalidAuth

from exceptions.exception import AuthException, PermissionException
from modules import SystemPermission, SystemTenantUser, SystemUser, SystemUserRole
from utils.config import config
from utils.get_redis import RedisKeyConfig
from utils.permission import PermissionService, UserType
from utils.response import HttpStatusConstant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class CustomOAuth2PasswordRequestForm:
    """Custom OAuth2 password form."""

    def __init__(
        self,
        grant_type: str = Form(
            default="password",
            pattern="password",
            description="Grant type",
        ),
        username: str = Form(
            ...,
            min_length=3,
            max_length=50,
            description="Username",
        ),
        password: str = Form(
            ...,
            min_length=6,
            description="Password",
        ),
        scope: str = Form(default="", description="OAuth scope"),
        client_id: Optional[str] = Form(default=None, description="Client id"),
        client_secret: Optional[str] = Form(
            default=None,
            description="Client secret",
        ),
        login_days: Optional[int] = Form(
            default=1,
            ge=1,
            le=30,
            description="Login valid days",
        ),
        code: Optional[str] = Form(
            default=None,
            min_length=1,
            max_length=10,
            description="Captcha code",
        ),
        uuid: Optional[str] = Form(
            default=None,
            min_length=16,
            max_length=36,
            description="Captcha uuid",
        ),
    ):
        if grant_type != "password":
            raise HTTPException(
                status_code=HttpStatusConstant.BAD_REQUEST,
                detail="Only password grant type is supported",
            )

        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.login_days = login_days
        self.code = code
        self.uuid = uuid


class Auth:
    """Permission decorator."""

    def __init__(self, permission_list: list):
        self.permission_list = permission_list

    def __call__(self, func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not config.app().permission_verify_enabled:
                return await func(request, *args, **kwargs)

            token = request.headers.get("Authorization")
            current_user = await AuthController.get_current_user(request, token)

            user_type = current_user.get("user_type", UserType.NORMAL_USER)
            if user_type == UserType.SUPER_ADMIN:
                return await func(request, *args, **kwargs)

            permission_marks = set(current_user.get("permission_marks", []))
            permission_codes = set(current_user.get("permission_codes", []))
            for required_perm in self.permission_list:
                if required_perm in permission_marks or required_perm in permission_codes:
                    return await func(request, *args, **kwargs)

            if await PermissionService.can_access_api(
                str(current_user.get("id")),
                request.url.path,
                request.method,
            ):
                return await func(request, *args, **kwargs)

            raise PermissionException(message="Permission denied")

        return wrapper


class AuthController:
    """User auth controller."""

    @classmethod
    async def create_token(
        cls, data: dict, expires_delta: Union[timedelta, None] = None
    ) -> str:
        to_copy = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=config.jwt().expire_minutes)
        to_copy.update({"exp": expire})
        return jwt.encode(
            claims=to_copy,
            key=config.jwt().secret_key,
            algorithm=config.jwt().algorithm,
        )

    @classmethod
    async def get_current_user(
        cls,
        request: Request,
        token: str = Depends(oauth2_scheme),
    ):
        try:
            if not token:
                raise AuthException(data="", message="Missing token")
            if token.startswith("Bearer"):
                token = token.split(" ")[1]
            payload = jwt.decode(
                token=token,
                key=config.jwt().secret_key,
                algorithms=[config.jwt().algorithm],
            )
            user_id: str = payload.get("id", "")
            session_id: str = payload.get("session_id", "")
            if not user_id:
                raise AuthException(data="", message="Invalid token")
            if not await SystemUser.get_or_none(id=user_id):
                raise AuthException(data="", message="User does not exist")
        except (JWEInvalidAuth, ExpiredSignatureError, JWEError):
            raise AuthException(data="", message="Token expired, please login again")

        user_info = await request.app.state.redis.get(
            f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
        )
        if user_info:
            try:
                user_info = json.loads(user_info)
            except (json.JSONDecodeError, ValueError):
                await request.app.state.redis.delete(
                    f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
                )
                user_info = None

        if not user_info:
            user_info = await cls.get_user_info(user_id=user_id)
            await request.app.state.redis.set(
                f"{RedisKeyConfig.USER_INFO.key}:{user_id}",
                json.dumps(jsonable_encoder(user_info), ensure_ascii=False, default=str),
                ex=timedelta(minutes=30),
            )

        if not user_info:
            raise AuthException(data="", message="Invalid token")

        redis_token = await request.app.state.redis.get(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
        )
        if not redis_token:
            raise AuthException(data="", message="Token expired, please login again")
        return user_info

    @classmethod
    async def get_user_info(cls, user_id: str, tenant_id: str = None) -> dict:
        """Get user info from user + tenant-user relationships."""
        user = await SystemUser.get_or_none(id=user_id, is_del=False)
        if not user:
            return None

        user_info = {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "gender": user.gender,
            "phone": user.phone,
            "email": user.email,
            "status": user.status,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        tenant_user_query = SystemTenantUser.filter(user_id=user_id, is_del=False)
        if tenant_id:
            tenant_user_query = tenant_user_query.filter(tenant_id=tenant_id)
        tenant_user = await tenant_user_query.first()
        superadmin_relation = await SystemTenantUser.filter(
            user_id=user_id,
            user_type=UserType.SUPER_ADMIN,
            status=1,
            is_del=False,
        ).first()

        selected_tenant_without_relation = bool(tenant_id and not tenant_user and superadmin_relation)
        if not tenant_user:
            tenant_user = await SystemTenantUser.filter(user_id=user_id, is_del=False).first()

        tenant_id_res = str(tenant_user.tenant_id) if tenant_user and tenant_user.tenant_id else None
        if selected_tenant_without_relation:
            tenant_id_res = str(tenant_id)

        department_id = (
            str(tenant_user.department_id) if tenant_user and tenant_user.department_id else None
        )
        if selected_tenant_without_relation:
            department_id = None

        department_name = None
        user_type = tenant_user.user_type if tenant_user else UserType.NORMAL_USER
        if selected_tenant_without_relation:
            user_type = UserType.SUPER_ADMIN

        if department_id:
            from modules import SystemDepartment

            department = await SystemDepartment.get_or_none(
                id=tenant_user.department_id,
                is_del=False,
            )
            if department:
                department_name = department.name

        is_superadmin = user_type == UserType.SUPER_ADMIN

        role_filter = {
            "user_id": user_id,
            "is_del": False,
            "role__is_del": False,
            "role__status": 1,
        }
        if tenant_id_res:
            role_filter["tenant_id"] = tenant_id_res
        roles = await SystemUserRole.filter(**role_filter).values_list("role__code", flat=True)
        roles = [str(role) for role in roles if role]
        if not roles and user_type == UserType.SUPER_ADMIN:
            fallback_role_filter = {
                "user_id": user_id,
                "is_del": False,
                "role__is_del": False,
                "role__status": 1,
            }
            roles = await SystemUserRole.filter(**fallback_role_filter).values_list(
                "role__code", flat=True
            )
        roles = list(dict.fromkeys(str(role) for role in roles if role))

        permissions = (
            await SystemPermission.filter(
                role_permissions__role__code__in=roles,
                role_permissions__role__is_del=False,
                role_permissions__role__status=1,
                role_permissions__is_del=False,
                is_del=False,
            )
            .distinct()
            .all()
        )
        menu_ids = [str(permission.id) for permission in permissions if permission.menu_type == 0]
        button_ids = [str(permission.id) for permission in permissions if permission.menu_type == 1]
        api_ids = [str(permission.id) for permission in permissions if permission.menu_type == 2]

        data_scope = await PermissionService.get_data_scope(str(user_id))
        sub_departments = list(data_scope["department_ids"])

        permission_marks: list[str] = []
        permission_codes: list[str] = []
        if button_ids:
            button_permissions = await SystemPermission.filter(
                id__in=button_ids,
                is_del=False,
            ).values(
                id="id",
                authMark="code",
                code="code",
            )
            permission_marks = [
                item["authMark"] for item in button_permissions if item["authMark"]
            ]
            permission_codes = [item["code"] for item in button_permissions if item["code"]]

        permission_codes.extend(
            [
                code
                for code in await SystemPermission.filter(
                    id__in=menu_ids + api_ids,
                    is_del=False,
                ).values_list("code", flat=True)
                if code
            ]
        )

        if is_superadmin:
            tenant_marks = [
                "tenant:btn:list",
                "tenant:btn:add",
                "tenant:btn:update",
                "tenant:btn:delete",
                "tenant:btn:info",
                "tenant:btn:export",
                "tenant:btn:import",
            ]
            permission_marks.extend(tenant_marks)
            permission_codes.extend(tenant_marks)

        return {
            **user_info,
            "is_superadmin": is_superadmin,
            "sub_departments": sub_departments,
            "permission_ids": button_ids,
            "permission_marks": permission_marks,
            "permission_codes": list(dict.fromkeys(permission_codes)),
            "data_scope": data_scope["scope"],
            "tenant_id": tenant_id_res,
            "department_id": department_id,
            "department_name": department_name,
            "user_type": user_type,
            "roles": roles,
            "menus": menu_ids,
            "buttons": button_ids,
            "apis": api_ids,
        }

    @classmethod
    async def logout(cls, request: Request = Request, token: str = None) -> bool:
        try:
            if not token:
                raise AuthException(data="", message="Missing token")
            if token.startswith("Bearer"):
                token = token.split(" ")[1]
            payload = jwt.decode(
                token=token,
                key=config.jwt().secret_key,
                algorithms=[config.jwt().algorithm],
            )
            session_id: str = payload.get("session_id", "")
        except (JWEInvalidAuth, ExpiredSignatureError, JWEError):
            raise AuthException(data="", message="Token expired, please login again")

        redis_token = await request.app.state.redis.get(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
        )
        if redis_token == token:
            await request.app.state.redis.delete(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
            )
            return True
        return False
