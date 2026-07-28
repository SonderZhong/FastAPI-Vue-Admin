# _*_ coding : UTF-8 _*_

import json
import uuid
from datetime import datetime, timedelta

from tortoise.expressions import Q

from annotation.auth import AuthController
from annotation.log import _request_meta
from modules import (
    SystemDepartment,
    SystemLoginLog,
    SystemPermission,
    SystemRole,
    SystemRolePermission,
    SystemTenantUser,
    SystemUser,
    SystemUserRole,
)
from utils.captcha import CaptchaUtil
from utils.config import config
from utils.get_redis import RedisKeyConfig
from utils.ip2region_util import get_ip_location
from utils.notification import NotificationService
from utils.password import PasswordUtil


def get_login_meta(request) -> dict:
    meta = _request_meta(request)
    meta["location"] = (
        get_ip_location(meta["ip"]) if config.app().ip_location_enabled else "Internal IP"
    )
    return meta


class AuthService:
    @staticmethod
    async def get_captcha_config(redis) -> dict:
        captcha_enabled = (
            await redis.get(f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_captcha_enabled")
            == "true"
        )
        register_enabled = (
            await redis.get(f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_register_enabled")
            == "true"
        )
        return {
            "captcha_enabled": captcha_enabled,
            "register_enabled": register_enabled,
        }

    @staticmethod
    async def generate_captcha(redis, captcha_type: str = "0") -> dict:
        captcha_result = await CaptchaUtil.create_captcha(captcha_type)
        session_id = str(uuid.uuid4())
        captcha = captcha_result[0]
        result = captcha_result[-1]
        await redis.set(
            f"{RedisKeyConfig.CAPTCHA_CODES.key}:{session_id}",
            result,
            ex=timedelta(minutes=2),
        )
        return {"uuid": session_id, "captcha": captcha}

    @staticmethod
    async def login(
        request,
        username: str,
        password: str,
        login_days: int = 1,
        code: str = "",
        captcha_uuid: str = "",
    ) -> dict:
        redis = request.app.state.redis

        captcha_enabled = (
            await redis.get(f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_captcha_enabled")
            == "true"
        )
        request_from_swagger = request.headers.get("referer", "").endswith("docs")
        request_from_redoc = request.headers.get("referer", "").endswith("redoc")

        if captcha_enabled and not request_from_redoc and not request_from_swagger:
            result = await CaptchaUtil.verify_code(
                request,
                code=code,
                session_id=captcha_uuid,
            )
            if not result["status"]:
                return {"success": False, "msg": result["msg"]}

        user = await SystemUser.get_or_none(
            Q(username=username) | Q(email=username) | Q(phone=username),
            is_del=False,
        )

        if not user:
            request_meta = get_login_meta(request)
            await SystemLoginLog.create(
                user_id=None,
                login_ip=request_meta["ip"],
                login_location=request_meta["location"],
                browser=request_meta["browser"],
                os=request_meta["os"],
                status=0,
                session_id=None,
            )
            return {"success": False, "msg": "Username or password is incorrect"}

        if not await PasswordUtil.verify_password(
            plain_password=password,
            hashed_password=user.password,
        ):
            request_meta = get_login_meta(request)
            await SystemLoginLog.create(
                user_id=user.id,
                login_ip=request_meta["ip"],
                login_location=request_meta["location"],
                browser=request_meta["browser"],
                os=request_meta["os"],
                status=0,
                session_id=None,
            )
            return {"success": False, "msg": "Username or password is incorrect"}

        user_info = await AuthController.get_user_info(user.id)
        session_id = str(uuid.uuid4())
        request_meta = get_login_meta(request)

        tenant_user = await SystemTenantUser.filter(user_id=user.id, is_del=False).first()
        log_tenant_id = tenant_user.tenant_id if tenant_user else None
        log_dept_id = tenant_user.department_id if tenant_user else None

        await SystemLoginLog.create(
            user_id=user.id,
            login_ip=request_meta["ip"],
            login_location=request_meta["location"],
            browser=request_meta["browser"],
            os=request_meta["os"],
            status=1,
            session_id=session_id,
            tenant_id=log_tenant_id,
            department_id=log_dept_id,
        )

        token_data = {
            "id": str(user.id),
            "username": user.username,
            "session_id": session_id,
        }
        access_token = await AuthController.create_token(
            data=token_data,
            expires_delta=timedelta(minutes=login_days * 24 * 60),
        )
        expires_time = (
            datetime.now() + timedelta(minutes=login_days * 24 * 60)
        ).timestamp()
        refresh_token = await AuthController.create_token(
            data=token_data,
            expires_delta=timedelta(minutes=(login_days * 24 + 2) * 60),
        )

        await redis.set(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}",
            access_token,
            ex=timedelta(minutes=login_days * 24 * 60),
        )
        await redis.set(
            f"{RedisKeyConfig.USER_INFO.key}:{user.id}",
            json.dumps(user_info, ensure_ascii=False, default=str),
            ex=timedelta(minutes=login_days * 24 * 60),
        )

        notification_service = NotificationService(redis)
        await notification_service.send_login_notification(
            user_id=str(user.id),
            username=user.username,
            login_ip=request_meta["ip"],
            login_location=request_meta["location"],
            browser=request_meta["browser"],
            os=request_meta["os"],
        )

        available_tenants = await AuthService._get_available_tenants(str(user.id))

        return {
            "success": True,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresTime": expires_time,
            "request_from_swagger": request_from_swagger,
            "request_from_redoc": request_from_redoc,
            "tenant_id": user_info.get("tenant_id"),
            "available_tenants": available_tenants,
        }

    @staticmethod
    async def _get_available_tenants(user_id: str) -> list:
        from modules.tenant.model import SystemTenant

        user = await SystemUser.get_or_none(id=user_id, is_del=False)
        if not user:
            return []

        super_admin_relation = await SystemTenantUser.filter(
            user_id=user_id,
            user_type=0,
            status=1,
            is_del=False,
        ).first()
        if super_admin_relation:
            tenants = await SystemTenant.filter(status=1, is_del=False).values(
                "id",
                "name",
                "code",
            )
            return [
                {"id": str(item["id"]), "name": item["name"], "code": item["code"]}
                for item in tenants
            ]

        tenant_users = (
            await SystemTenantUser.filter(
                user_id=user_id,
                status=1,
                is_del=False,
            )
            .prefetch_related("tenant")
            .all()
        )

        result = []
        for tenant_user in tenant_users:
            tenant = await tenant_user.tenant
            if tenant and not tenant.is_del and tenant.status == 1:
                result.append(
                    {
                        "id": str(tenant.id),
                        "name": tenant.name,
                        "code": tenant.code,
                    }
                )
        return result

    @staticmethod
    async def select_tenant(request, user_id: str, tenant_id: str) -> dict:
        from modules.tenant.model import SystemTenant

        user = await SystemUser.get_or_none(id=user_id, is_del=False)
        if not user:
            return {"success": False, "msg": "User does not exist"}

        tenant = await SystemTenant.get_or_none(id=tenant_id, status=1, is_del=False)
        if not tenant:
            return {"success": False, "msg": "Tenant does not exist or is disabled"}

        tenant_user = await SystemTenantUser.filter(
            user_id=user_id,
            tenant_id=tenant_id,
            status=1,
            is_del=False,
        ).first()
        super_admin_relation = await SystemTenantUser.filter(
            user_id=user_id,
            user_type=0,
            status=1,
            is_del=False,
        ).first()
        if not tenant_user and not super_admin_relation:
            return {"success": False, "msg": "No permission to switch to this tenant"}

        redis = request.app.state.redis
        user_info = await AuthController.get_user_info(user.id, tenant_id=tenant_id)
        await redis.set(
            f"{RedisKeyConfig.USER_INFO.key}:{user.id}",
            json.dumps(user_info, ensure_ascii=False, default=str),
            ex=timedelta(hours=24),
        )

        route_keys = await redis.keys(f"{RedisKeyConfig.USER_ROUTES.key}:{user.id}:*")
        if route_keys:
            await redis.delete(*route_keys)

        return {
            "success": True,
            "msg": f"Switched to tenant {tenant.name}",
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
        }

    @staticmethod
    async def register(redis, params: dict) -> dict:
        from modules.tenant.model import SystemTenant

        key = RedisKeyConfig.SYSTEM_CONFIG.key
        (
            captcha_enabled,
            register_enabled,
            default_dept_id,
            default_role_id,
            default_tenant_id,
        ) = await redis.mget(
            f"{key}:account_captcha_enabled",
            f"{key}:account_register_enabled",
            f"{key}:default_department_id",
            f"{key}:default_role_id",
            f"{key}:default_tenant_id",
        )
        captcha_enabled = captcha_enabled == "true"
        register_enabled = register_enabled == "true"

        invite_code = params.get("invite_code")
        tenant = None
        if invite_code:
            tenant = await SystemTenant.get_or_none(
                invite_code=invite_code,
                status=1,
                is_del=False,
            )
            if not tenant:
                return {"success": False, "msg": "Invite code is invalid or tenant is disabled"}
            if not tenant.allow_register:
                return {"success": False, "msg": "This tenant does not allow invite registration"}
        elif not register_enabled:
            return {"success": False, "msg": "Registration is disabled"}

        username = params.get("username", "")
        if await SystemUser.get_or_none(username=username, is_del=False):
            return {"success": False, "msg": "Username already exists"}

        email = params.get("email")
        if email and await SystemUser.filter(email=email, is_del=False).exists():
            return {"success": False, "msg": "Email is already bound"}

        phone = params.get("phone")
        if phone and await SystemUser.filter(phone=phone, is_del=False).exists():
            return {"success": False, "msg": "Phone is already bound"}

        user = await SystemUser.create(
            username=username,
            password=await PasswordUtil.get_password_hash(params["password"]),
            nickname=params.get("nickname"),
            phone=phone,
            email=email,
            gender=params.get("gender", 0),
            status=1,
        )

        tenant_id = str(tenant.id) if tenant else (default_tenant_id or None)
        dept_id = params.get("department_id") or default_dept_id
        role_id = default_role_id
        if tenant:
            tenant_default_department = await SystemDepartment.filter(
                tenant_id=tenant.id,
                is_del=False,
                status=1,
            ).order_by("sort", "created_at").first()
            if tenant_default_department:
                dept_id = str(tenant_default_department.id)

            tenant_default_role = await SystemRole.filter(
                tenant_id=tenant.id,
                code="user",
                is_del=False,
                status=1,
            ).first()
            if not tenant_default_role:
                tenant_default_role = await SystemRole.filter(
                    tenant_id=tenant.id,
                    is_del=False,
                    status=1,
                ).order_by("created_at").first()
            role_id = str(tenant_default_role.id) if tenant_default_role else None

        if tenant_id:
            department = None
            if dept_id:
                department = await SystemDepartment.get_or_none(id=dept_id, is_del=False)
            await SystemTenantUser.create(
                tenant_id=tenant_id,
                user_id=str(user.id),
                department_id=str(department.id) if department else None,
                user_type=3,
                status=1,
            )

        if role_id and tenant_id:
            await SystemUserRole.create(
                tenant_id=tenant_id,
                user_id=str(user.id),
                role_id=role_id,
            )

        return {
            "success": True,
            "msg": "Register succeeded",
            "tenant": (
                {"id": str(tenant.id), "name": tenant.name, "code": tenant.code}
                if tenant
                else None
            ),
        }

    @staticmethod
    async def forgot_password_send_code(request, email: str) -> dict:
        user = await SystemUser.filter(email=email, is_del=False).first()
        if not user:
            return {"success": False, "msg": "No account is bound to this email"}

        from utils.mail import Email

        result = await Email.send_email(
            request,
            username=user.username,
            title="Reset Password",
            mail=email,
        )
        if result:
            return {"success": True, "msg": "Verification code sent"}
        return {"success": False, "msg": "Failed to send verification code"}

    @staticmethod
    async def forgot_password_reset(
        request,
        email: str,
        code: str,
        new_password: str,
    ) -> dict:
        user = await SystemUser.filter(email=email, is_del=False).first()
        if not user:
            return {"success": False, "msg": "No account is bound to this email"}

        from utils.mail import Email

        verify_result = await Email.verify_code(
            request,
            username=user.username,
            mail=email,
            code=code,
        )
        if not verify_result["status"]:
            return {"success": False, "msg": verify_result["msg"]}

        user.password = await PasswordUtil.get_password_hash(new_password)
        await user.save()

        redis = request.app.state.redis
        cache_key_user = f"{RedisKeyConfig.USER_INFO.key}:{user.id}"
        if await redis.get(cache_key_user):
            await redis.delete(cache_key_user)
        route_keys = await redis.keys(f"{RedisKeyConfig.USER_ROUTES.key}:{user.id}*")
        if route_keys:
            await redis.delete(*route_keys)

        return {"success": True, "msg": "Password reset succeeded"}

    @staticmethod
    async def get_user_routes(redis, current_user: dict) -> list:
        uid = current_user.get("id")
        tenant_id = current_user.get("tenant_id")
        user_type = current_user.get("user_type", 3)
        is_superadmin = bool(current_user.get("is_superadmin"))

        cache_key = f"{RedisKeyConfig.USER_ROUTES.key}:{uid}:{tenant_id or 'none'}"
        permission_cache = await redis.get(cache_key)
        if permission_cache:
            return json.loads(permission_cache)

        if tenant_id:
            role_codes = await SystemUserRole.filter(
                user_id=uid,
                tenant_id=tenant_id,
                is_del=False,
                role__is_del=False,
                role__status=1,
            ).values_list("role__code", flat=True)
        else:
            role_codes = await SystemUserRole.filter(
                user_id=uid,
                is_del=False,
                role__is_del=False,
                role__status=1,
            ).values_list("role__code", flat=True)
        role_codes = [str(code) for code in role_codes if code]

        if not role_codes and is_superadmin:
            role_codes = await SystemUserRole.filter(
                user_id=uid,
                is_del=False,
                role__is_del=False,
                role__status=1,
            ).values_list("role__code", flat=True)
            role_codes = [str(code) for code in role_codes if code]

        menu_ids = (
            await SystemRolePermission.filter(
                role__code__in=role_codes,
                role__is_del=False,
                role__status=1,
                permission__menu_type=0,
                permission__is_del=False,
                is_del=False,
            )
            .distinct()
            .values_list("permission_id", flat=True)
        )
        menu_ids = [str(menu_id) for menu_id in menu_ids]

        role_permissions = []
        if menu_ids:
            role_permissions = await SystemPermission.filter(
                id__in=menu_ids,
                menu_type=0,
                is_del=False,
            ).values(
                id="id",
                created_at="created_at",
                updated_at="updated_at",
                menu_type="menu_type",
                code="code",
                parent_id="parent_id",
                component="component",
                name="name",
                title="title",
                path="path",
                icon="icon",
                showBadge="showBadge",
                showTextBadge="showTextBadge",
                isHide="isHide",
                isHideTab="isHideTab",
                link="link",
                isIframe="isIframe",
                keepAlive="keepAlive",
                isFirstLevel="isFirstLevel",
                fixedTab="fixedTab",
                activePath="activePath",
                isFullPage="isFullPage",
                order="order",
                authTitle="title",
                authMark="code",
            )

        button_ids = (
            await SystemRolePermission.filter(
                role__code__in=role_codes,
                role__is_del=False,
                role__status=1,
                permission__menu_type=1,
                permission__is_del=False,
                is_del=False,
            )
            .distinct()
            .values_list("permission_id", flat=True)
        )
        button_ids = [str(button_id) for button_id in button_ids]

        button_permissions = []
        if button_ids:
            button_permissions = await SystemPermission.filter(
                id__in=button_ids,
                menu_type=1,
                is_del=False,
            ).values(
                id="id",
                parent_id="parent_id",
                code="code",
                authTitle="title",
                authMark="code",
            )

        async def get_menu_auth_list(menu_id: str) -> list:
            auth_list = []
            for permission in button_permissions:
                if str(permission.get("parent_id")) == str(menu_id):
                    auth_mark = permission.get("code") or permission.get("authMark")
                    if permission.get("authTitle") and auth_mark:
                        auth_list.append(
                            {
                                "title": permission["authTitle"],
                                "authMark": auth_mark,
                                "code": auth_mark,
                            }
                        )
            return auth_list

        async def find_node_recursive(node_id: str, data: list) -> dict:
            result = {}
            menu_data = [item for item in data if item.get("menu_type") == 0]
            for item in menu_data:
                if item["id"] == node_id:
                    children = []
                    for child_item in menu_data:
                        if child_item["parent_id"] == node_id:
                            child_node = await find_node_recursive(child_item["id"], data)
                            if child_node:
                                children.append(child_node)
                    meta = {
                        key: value
                        for key, value in {
                            "title": item["title"],
                            "order": item["order"],
                            "icon": item["icon"],
                            "showBadge": item["showBadge"],
                            "showTextBadge": item["showTextBadge"],
                            "keepAlive": item["keepAlive"],
                            "isHide": item["isHide"],
                            "isHideTab": item["isHideTab"],
                            "link": item["link"],
                            "isIframe": item["isIframe"],
                            "isFullPage": item["isFullPage"],
                            "fixedTab": item["fixedTab"],
                            "isFirstLevel": item["isFirstLevel"],
                            "authList": await get_menu_auth_list(item["id"]),
                        }.items()
                        if value is not None
                    }
                    result = {
                        "name": item["name"],
                        "path": item["path"],
                        "meta": meta,
                        "children": children,
                    }
                    if item["component"]:
                        result["component"] = (
                            item["component"]
                            .replace(".vue", "")
                            .replace(".ts", "")
                            .replace(".tsx", "")
                            .replace(".js", "")
                            .replace(".jsx", "")
                            .strip()
                        )
                    if result["name"] == "":
                        result.pop("name")
                    if not result["children"]:
                        result.pop("children")
                    else:
                        result["children"] = sorted(
                            result["children"],
                            key=lambda child: child["meta"]["order"],
                        )
                    break
            return result

        async def find_complete_data(data: list) -> list:
            complete_data = []
            root_ids = [item["id"] for item in data if not item["parent_id"]]
            for root_id in root_ids:
                complete_data.append(await find_node_recursive(root_id, data))
            return complete_data

        permissions = await find_complete_data(role_permissions)
        if is_superadmin:
            system_node = next((item for item in permissions if item.get("path") == "/system"), None)
            if system_node:
                tenant_path = "/system/tenant"
                existing_tenant = next(
                    (
                        child
                        for child in system_node.get("children", [])
                        if child.get("path") == tenant_path
                    ),
                    None,
                )
                if not existing_tenant:
                    system_node.setdefault("children", []).append(
                        {
                            "name": "Tenant",
                            "path": tenant_path,
                            "component": "/system/tenant/index",
                            "meta": {
                                "title": "menus.system.tenant",
                                "icon": "&#xe6c8;",
                                "order": 11,
                            },
                        }
                    )
                    system_node["children"] = sorted(
                        system_node["children"],
                        key=lambda child: child.get("meta", {}).get("order", 9999),
                    )
        all_routes = _BASE_PUBLIC_ROUTES + permissions

        await redis.set(
            cache_key,
            json.dumps(all_routes, ensure_ascii=False, default=str),
            ex=timedelta(minutes=30),
        )
        return all_routes


_BASE_PUBLIC_ROUTES = [
    {
        "name": "Dashboard",
        "path": "/dashboard",
        "component": "/index/index",
        "meta": {"title": "menus.dashboard.title", "icon": "&#xe721;", "order": 1},
        "children": [
            {
                "name": "Console",
                "path": "/dashboard/console",
                "component": "/dashboard/console",
                "meta": {
                    "title": "menus.dashboard.console",
                    "icon": "&#xe721;",
                    "keepAlive": False,
                    "fixedTab": True,
                },
            },
        ],
    },
    {
        "name": "UserCenter_",
        "path": "/user-center",
        "component": "/index/index",
        "meta": {"title": "menus.system.userCenter", "icon": "&#xe6bd;", "order": 999},
        "children": [
            {
                "name": "UserCenter",
                "path": "/user-center",
                "component": "/user-center",
                "meta": {
                    "title": "menus.system.userCenter",
                    "keepAlive": False,
                    "isHide": True,
                },
            },
        ],
    },
    {
        "name": "PersonalLoginRecord_",
        "path": "/personal-login-record",
        "component": "/index/index",
        "meta": {
            "title": "menus.personalLoginRecord.title",
            "icon": "&#xe6ce;",
            "order": 999,
        },
        "children": [
            {
                "name": "PersonalLoginRecord",
                "path": "/personal-login-record",
                "component": "/personal-login-record/index",
                "meta": {
                    "title": "menus.personalLoginRecord.title",
                    "keepAlive": False,
                    "isHide": True,
                },
            },
        ],
    },
    {
        "name": "PersonalOperationRecord_",
        "path": "/personal-operation-record",
        "component": "/index/index",
        "meta": {
            "title": "menus.personalOperationRecord.title",
            "icon": "&#xe6df;",
            "order": 999,
        },
        "children": [
            {
                "name": "PersonalOperationRecord",
                "path": "/personal-operation-record",
                "component": "/personal-operation-record/index",
                "meta": {
                    "title": "menus.personalOperationRecord.title",
                    "keepAlive": False,
                    "isHide": True,
                },
            },
        ],
    },
    {
        "name": "MyNotification_",
        "path": "/my-notification",
        "component": "/index/index",
        "meta": {
            "title": "menus.myNotification.title",
            "icon": "&#xe6c2;",
            "order": 999,
        },
        "children": [
            {
                "name": "MyNotification",
                "path": "/my-notification",
                "component": "/my-notification/index",
                "meta": {
                    "title": "menus.myNotification.title",
                    "keepAlive": False,
                    "isHide": True,
                },
            },
        ],
    },
]
