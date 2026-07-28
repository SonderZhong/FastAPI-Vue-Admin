# _*_ coding : UTF-8 _*_

from typing import Any, Dict, List, Optional, Tuple

from core.common import BaseService
from modules import SystemPermission, SystemRole, SystemRolePermission
from modules.permission.model import PermissionType
from modules.user.model import SystemUser, SystemTenantUser, SystemUserRole
from utils.get_redis import RedisKeyConfig


class UserService(BaseService):
    model = SystemUser
    excel_sheet_name = "用户数据"
    excel_columns = {
        "username": "用户名",
        "nickname": "昵称",
        "phone": "手机号",
        "email": "邮箱",
        "gender": "性别",
        "status": "状态",
    }

    # ==================== 缓存操作 ====================

    @staticmethod
    async def get_user_info_cache(redis, user_id: str) -> Optional[dict]:
        cache_key = f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
        cached = await redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)
        return None

    @staticmethod
    async def set_user_info_cache(redis, user_id: str, data: dict, expire: int = 3600):
        import json
        cache_key = f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
        await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)

    @staticmethod
    async def delete_user_info_cache(redis, user_id: str):
        cache_key = f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
        if await redis.get(cache_key):
            await redis.delete(cache_key)

    @staticmethod
    async def delete_user_routes_cache(redis, user_id: str):
        route_keys = await redis.keys(f"{RedisKeyConfig.USER_ROUTES.key}:{user_id}:*")
        if route_keys:
            await redis.delete(*route_keys)

    @staticmethod
    async def clear_user_all_cache(redis, user_id: str):
        await UserService.delete_user_info_cache(redis, user_id)
        await UserService.delete_user_routes_cache(redis, user_id)

    # ==================== 业务方法 ====================

    @classmethod
    async def create_user(cls, params: dict, tenant_id: Optional[str] = None,
                          department_id: Optional[str] = None) -> Tuple[bool, str]:
        if await cls.model.get_or_none(username=params.get("username"), is_del=False):
            return False, "添加失败，用户已存在！"

        user = await cls.model.create(
            username=params.get("username"),
            password=params.get("password"),
            nickname=params.get("nickname"),
            phone=params.get("phone"),
            email=params.get("email"),
            gender=params.get("gender", 0),
            status=params.get("status", 1),
        )

        # 创建租户-用户关联
        if tenant_id:
            await SystemTenantUser.create(
                tenant_id=tenant_id,
                user_id=str(user.id),
                department_id=department_id,
                user_type=params.get("user_type", 3),
                status=1,
            )

        return True, "添加成功！"

    @classmethod
    async def delete_user(cls, user_id: str, redis=None) -> bool:
        result = await cls.delete(user_id)
        if result and redis:
            await SystemUserRole.filter(user_id=user_id, is_del=False).update(is_del=True)
            await SystemTenantUser.filter(user_id=user_id, is_del=False).update(is_del=True)
            await cls.clear_user_all_cache(redis, user_id)
        return result

    @classmethod
    async def update_user(cls, user_id: str, update_data: dict, redis=None) -> bool:
        result = await cls.update(user_id, update_data)
        if result and redis:
            await cls.delete_user_info_cache(redis, user_id)
        return result

    @classmethod
    async def get_user_info(cls, user_id: str) -> Optional[dict]:
        data = await cls.model.filter(id=user_id, is_del=False).values(
            id="id", created_at="created_at", updated_at="updated_at",
            username="username", email="email", phone="phone",
            nickname="nickname", avatar="avatar", gender="gender",
            status="status",
        )
        if not data:
            return None

        user_info = data[0]
        tenant_user = await SystemTenantUser.filter(user_id=user_id, is_del=False).first()
        user_info["is_superadmin"] = bool(tenant_user and tenant_user.user_type == 0)
        return user_info

    @classmethod
    async def reset_password(cls, user_id: str, new_password: str, redis=None) -> Tuple[bool, str]:
        user = await cls.model.get_or_none(id=user_id, is_del=False)
        if not user:
            return False, "用户不存在！"

        from utils.password import PasswordUtil
        user.password = await PasswordUtil.get_password_hash(input_password=new_password)
        await user.save()

        if redis:
            await cls.clear_user_all_cache(redis, user_id)
            # 清除 Token
            access_tokens = await redis.keys(f"{RedisKeyConfig.ACCESS_TOKEN.key}:*")
            for token_key in access_tokens:
                token_val = await redis.get(token_key)
                if token_val:
                    try:
                        from jose import jwt
                        from utils.config import config
                        payload = jwt.decode(token_val, key=config.jwt().secret_key, algorithms=[config.jwt().algorithm])
                        if payload.get("id") == user_id:
                            await redis.delete(token_key)
                    except Exception:
                        pass
        return True, "重置密码成功！"

    @classmethod
    async def change_password(cls, user_id: str, old_password: str, new_password: str, redis=None) -> Tuple[bool, str]:
        user = await cls.model.get_or_none(id=user_id, is_del=False)
        if not user:
            return False, "更新失败！"

        from utils.password import PasswordUtil
        if not await PasswordUtil.verify_password(plain_password=old_password, hashed_password=user.password):
            return False, "旧密码错误！"

        user.password = await PasswordUtil.get_password_hash(input_password=new_password)
        await user.save()

        if redis:
            await cls.delete_user_info_cache(redis, user_id)
        return True, "更新成功！"

    @classmethod
    async def change_phone(cls, user_id: str, password: str, phone: str, redis=None) -> Tuple[bool, str]:
        user = await cls.model.get_or_none(id=user_id, is_del=False)
        if not user:
            return False, "更新失败！"

        from utils.password import PasswordUtil
        if not await PasswordUtil.verify_password(plain_password=password, hashed_password=user.password):
            return False, "更改失败，请正确输入密码"

        phone_exists = await cls.model.filter(phone=phone, is_del=False).exclude(id=user_id).count()
        if phone_exists > 0:
            return False, f"更改失败，手机号:{phone}已绑定其他账号！"

        user.phone = phone
        await user.save()

        if redis:
            await cls.delete_user_info_cache(redis, user_id)
        return True, "更新成功！"

    @classmethod
    async def change_email(cls, user_id: str, password: str, email: str, redis=None) -> Tuple[bool, str]:
        user = await cls.model.get_or_none(id=user_id, is_del=False)
        if not user:
            return False, "更新失败！"

        from utils.password import PasswordUtil
        if not await PasswordUtil.verify_password(plain_password=password, hashed_password=user.password):
            return False, "更改失败，请正确输入密码"

        email_exists = await cls.model.filter(email=email, is_del=False).exclude(id=user_id).count()
        if email_exists > 0:
            return False, f"更改失败，邮箱:{email}已绑定其他账号！"

        user.email = email
        await user.save()

        if redis:
            await cls.delete_user_info_cache(redis, user_id)
        return True, "更新成功！"

    @classmethod
    async def update_base_info(cls, user_id: str, name: Optional[str], gender: int, redis=None) -> Tuple[bool, str]:
        user = await cls.model.get_or_none(id=user_id, is_del=False)
        if not user:
            return False, "更新失败！"

        if name is not None:
            user.nickname = name
        user.gender = gender
        await user.save()

        if redis:
            await cls.delete_user_info_cache(redis, user_id)
        return True, "更新成功！"

    @classmethod
    async def change_tenant(cls, user_id: str, tenant_id: str, redis=None) -> Tuple[bool, str]:
        """分配用户到指定租户"""
        user = await cls.model.get_or_none(id=user_id, is_del=False)
        if not user:
            return False, "用户不存在！"

        from modules.tenant.model import SystemTenant
        tenant = await SystemTenant.get_or_none(id=tenant_id, is_del=False)
        if not tenant:
            return False, "目标租户不存在！"

        existing = await SystemTenantUser.filter(user_id=user_id, tenant_id=tenant_id, is_del=False).first()
        if existing:
            return False, "用户已在该租户中！"

        await SystemTenantUser.create(
            tenant_id=tenant_id, user_id=user_id, user_type=3, status=1,
        )

        if redis:
            await cls.delete_user_info_cache(redis, user_id)
        return True, f"已将用户分配到租户 {tenant.name}！"


class UserRoleService(BaseService):
    model = SystemUserRole

    @classmethod
    async def sync_user_roles(cls, user_id: str, role_ids: list[str], tenant_id: str = None) -> dict:
        filter_args = {"user_id": user_id, "is_del": False}
        if tenant_id:
            filter_args["tenant_id"] = tenant_id

        user_roles = await cls.model.filter(**filter_args).all()
        existing_role_ids = [str(item.role_id) for item in user_roles]

        add_roles = set(role_ids).difference(existing_role_ids)
        delete_roles = set(existing_role_ids).difference(role_ids)

        for role_id in add_roles:
            existing_role = await cls.model.filter(
                user_id=user_id, role_id=role_id, tenant_id=tenant_id, is_del=True,
            ).first()
            if existing_role:
                existing_role.is_del = False
                await existing_role.save()
            else:
                await cls.model.create(user_id=user_id, role_id=role_id, tenant_id=tenant_id)

        for role_id in delete_roles:
            await cls.model.filter(
                user_id=user_id, role_id=role_id, tenant_id=tenant_id, is_del=False,
            ).update(is_del=True)

        return {"added": len(add_roles), "removed": len(delete_roles)}

    @classmethod
    async def get_user_role_info(cls, relation_id: str):
        data = await cls.model.filter(id=relation_id, is_del=False).values(
            id="id", user_id="user__id", user_name="user__username",
            role_name="role__name", role_code="role__code", role_id="role__id",
            tenant_id="tenant__id", created_at="created_at", updated_at="updated_at",
        )
        return data[0] if data else None

    @classmethod
    async def get_user_role_list(cls, user_id: str, tenant_id: str = None):
        filter_args = {"user_id": user_id, "is_del": False}
        if tenant_id:
            filter_args["tenant_id"] = tenant_id

        result = await cls.model.filter(**filter_args).values(
            id="id", tenant_id="tenant__id",
            role_name="role__name", role_code="role__code", role_id="role__id",
            created_at="created_at", updated_at="updated_at",
        )
        return {
            "result": result,
            "total": len(result),
            "page": 1,
            "pageSize": 10,
            "roles": [item["role_code"] for item in result],
        }

    @classmethod
    async def get_user_permission_list(cls, user_id: str, operator_user_type: int, tenant_id: str = None):
        filter_args = {"user_id": user_id, "is_del": False, "role__is_del": False, "role__status": 1}
        if tenant_id:
            filter_args["tenant_id"] = tenant_id

        role_codes = await cls.model.filter(**filter_args).values_list("role__code", flat=True)
        role_codes = list(dict.fromkeys(str(rc) for rc in role_codes if rc))

        permission_rows = await SystemPermission.filter(
            role_permissions__role__code__in=role_codes,
            role_permissions__role__is_del=False,
            role_permissions__role__status=1,
            role_permissions__is_del=False,
            is_del=False,
        ).distinct().all()
        user_permissions = {
            "roles": role_codes,
            "menus": [str(p.id) for p in permission_rows if p.menu_type == PermissionType.MENU],
            "buttons": [str(p.id) for p in permission_rows if p.menu_type == PermissionType.BUTTON],
        }

        result = []
        all_permission_ids = user_permissions["menus"] + user_permissions["buttons"]
        if all_permission_ids:
            permissions = await SystemPermission.filter(
                id__in=all_permission_ids,
                is_del=False,
            ).all()

            roles = await SystemRole.filter(code__in=role_codes, is_del=False).all()
            role_map = {role.code: {"id": str(role.id), "name": role.name} for role in roles}
            role_permission_rows = await SystemRolePermission.filter(
                role__code__in=role_codes, role__is_del=False,
                is_del=False, permission__is_del=False,
            ).values("role__code", "permission_id")

            permission_role_map = {}
            for row in role_permission_rows:
                permission_role_map.setdefault(str(row["permission_id"]), []).append(
                    role_map.get(row["role__code"], {"id": None, "name": row["role__code"]})
                )

            for permission in permissions:
                perm_id = str(permission.id)
                perm_type = "menu" if perm_id in user_permissions["menus"] else "button"
                result.append({
                    "permission_id": perm_id,
                    "permission_name": permission.title or permission.name,
                    "permission_code": permission.code or permission.authMark,
                    "permission_type": perm_type,
                    "parent_id": str(permission.parent_id) if permission.parent_id else None,
                    "roles": permission_role_map.get(perm_id, []),
                })

        return {
            "result": result,
            "roles": user_permissions["roles"],
            "menus": user_permissions["menus"],
            "buttons": user_permissions["buttons"],
        }


class TenantUserService(BaseService):
    """租户-用户中间表服务"""
    model = SystemTenantUser

    @classmethod
    async def get_user_tenants(cls, user_id: str) -> List[dict]:
        """获取用户所属的所有租户"""
        tenant_users = await cls.model.filter(user_id=user_id, is_del=False).values(
            id="id", tenant_id="tenant__id", tenant_name="tenant__name",
            tenant_code="tenant__code", department_id="department__id",
            department_name="department__name", user_type="user_type",
            status="status",
        )
        return list(tenant_users)

    @classmethod
    async def add_user_to_tenant(cls, user_id: str, tenant_id: str,
                                  department_id: str = None, user_type: int = 3) -> Tuple[bool, str]:
        existing = await cls.model.filter(user_id=user_id, tenant_id=tenant_id, is_del=False).first()
        if existing:
            return False, "用户已在该租户中！"

        await cls.model.create(
            tenant_id=tenant_id, user_id=user_id,
            department_id=department_id, user_type=user_type, status=1,
        )
        return True, "添加成功！"

    @classmethod
    async def remove_user_from_tenant(cls, user_id: str, tenant_id: str) -> Tuple[bool, str]:
        tenant_user = await cls.model.filter(user_id=user_id, tenant_id=tenant_id, is_del=False).first()
        if not tenant_user:
            return False, "用户不在该租户中！"

        tenant_user.is_del = True
        await tenant_user.save()
        return True, "移除成功！"

    @classmethod
    async def update_user_tenant(cls, user_id: str, tenant_id: str,
                                  department_id: str = None, user_type: int = None) -> Tuple[bool, str]:
        tenant_user = await cls.model.filter(user_id=user_id, tenant_id=tenant_id, is_del=False).first()
        if not tenant_user:
            return False, "用户不在该租户中！"

        if department_id is not None:
            tenant_user.department_id = department_id
        if user_type is not None:
            tenant_user.user_type = user_type
        await tenant_user.save()
        return True, "更新成功！"
