# _*_ coding : UTF-8 _*_

from typing import Any, Dict, List, Optional, Tuple

from tortoise.transactions import in_transaction

from core.common import BaseService
from modules.department.model import SystemDepartment
from modules.permission.model import SystemPermission
from modules.role.model import SystemRole, SystemRolePermission
from modules.tenant.model import SystemTenant
from modules.user.model import SystemTenantUser, SystemUserRole


class TenantService(BaseService):
    model = SystemTenant
    excel_sheet_name = "租户数据"
    excel_columns = {
        "name": "租户名称",
        "code": "租户编码",
        "status": "状态",
        "remark": "备注",
    }

    @staticmethod
    async def _initialize_tenant_defaults(tenant: SystemTenant, creator_id: Optional[str] = None) -> None:
        default_department = await SystemDepartment.create(
            tenant_id=tenant.id,
            name=f"{tenant.name}默认部门",
            code=f"{tenant.code}_root",
            ancestor_path="/",
            parent_id=None,
            sort=0,
            status=1,
            remark="租户初始化自动创建",
        )

        tenant_admin_role = await SystemRole.create(
            tenant_id=tenant.id,
            department_id=default_department.id,
            name="租户管理员",
            code="tenant_admin",
            description="租户初始化自动创建",
            status=1,
        )

        await SystemRole.create(
            tenant_id=tenant.id,
            department_id=default_department.id,
            name="普通成员",
            code="user",
            description="租户初始化自动创建",
            status=1,
        )

        permission_ids = await SystemPermission.filter(is_del=False).values_list("id", flat=True)
        if permission_ids:
            await SystemRolePermission.bulk_create(
                [
                    SystemRolePermission(role_id=tenant_admin_role.id, permission_id=permission_id)
                    for permission_id in permission_ids
                ]
            )

        if creator_id:
            await SystemTenantUser.create(
                tenant_id=tenant.id,
                user_id=creator_id,
                department_id=default_department.id,
                user_type=1,
                status=1,
            )
            await SystemUserRole.create(
                tenant_id=tenant.id,
                user_id=creator_id,
                role_id=tenant_admin_role.id,
            )

    @classmethod
    async def create_tenant(cls, params: dict, creator_id: Optional[str] = None) -> Tuple[bool, str]:
        if await cls.model.get_or_none(code=params.get("code"), is_del=False):
            return False, "租户编码已存在！"
        if not params.get("invite_code"):
            params["invite_code"] = cls.model.generate_invite_code()

        async with in_transaction():
            tenant = await cls.model.create(**params)
            await cls._initialize_tenant_defaults(
                tenant,
                creator_id=str(creator_id) if creator_id else None,
            )

        return True, "新增成功！"

    @classmethod
    async def update_tenant(cls, tenant_id: str, update_data: dict) -> Tuple[bool, str]:
        tenant = await cls.model.get_or_none(id=tenant_id, is_del=False)
        if not tenant:
            return False, "租户不存在！"

        if update_data.get("code"):
            existing = await cls.model.get_or_none(code=update_data["code"], is_del=False)
            if existing and str(existing.id) != tenant_id:
                return False, "租户编码已存在！"

        await cls.update(tenant_id, update_data)
        return True, "修改成功！"

    @classmethod
    async def get_tenant_info(cls, tenant_id: str) -> Optional[dict]:
        tenant = await cls.model.get_or_none(id=tenant_id, is_del=False)
        if not tenant:
            return None
        return {
            "id": str(tenant.id),
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None,
            "name": tenant.name,
            "code": tenant.code,
            "status": tenant.status,
            "invite_code": tenant.invite_code,
            "allow_register": tenant.allow_register,
            "remark": tenant.remark,
        }

    @classmethod
    async def generate_invite_code(cls, tenant_id: str) -> Tuple[bool, str, Optional[dict]]:
        tenant = await cls.model.get_or_none(id=tenant_id, is_del=False)
        if not tenant:
            return False, "租户不存在！", None

        invite_code = cls.model.generate_invite_code()
        tenant.invite_code = invite_code
        await tenant.save()

        return True, "邀请码已生成！", {
            "invite_code": invite_code,
            "invite_link": f"/invite/{invite_code}",
            "allow_register": tenant.allow_register,
        }

    @classmethod
    async def toggle_allow_register(cls, tenant_id: str) -> Tuple[bool, str]:
        tenant = await cls.model.get_or_none(id=tenant_id, is_del=False)
        if not tenant:
            return False, "租户不存在！"

        tenant.allow_register = not tenant.allow_register
        await tenant.save()

        status = "开启" if tenant.allow_register else "关闭"
        return True, f"已{status}邀请注册！"

    @classmethod
    async def get_invite_code_info(cls, tenant_id: str) -> Optional[dict]:
        tenant = await cls.model.get_or_none(id=tenant_id, is_del=False)
        if not tenant:
            return None
        return {
            "id": str(tenant.id),
            "name": tenant.name,
            "code": tenant.code,
            "invite_code": tenant.invite_code,
            "invite_link": f"/invite/{tenant.invite_code}" if tenant.invite_code else None,
            "allow_register": tenant.allow_register,
        }

    @classmethod
    async def validate_invite_code(cls, code: str) -> Optional[dict]:
        tenant = await cls.model.get_or_none(invite_code=code, status=1, is_del=False)
        if not tenant:
            return None
        return {
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "tenant_code": tenant.code,
            "allow_register": tenant.allow_register,
        }

    @classmethod
    async def join_tenant(cls, user_id: str, invite_code: str, redis=None) -> Tuple[bool, str]:
        tenant = await cls.model.get_or_none(invite_code=invite_code, status=1, is_del=False)
        if not tenant:
            return False, "邀请码无效或租户已禁用！"

        if not tenant.allow_register:
            return False, "该租户未开放邀请加入！"

        existing = await SystemTenantUser.filter(
            user_id=user_id, tenant_id=tenant.id, is_del=False
        ).first()
        if existing:
            return False, "您已是该租户成员！"

        default_department = await SystemDepartment.filter(
            tenant_id=tenant.id,
            is_del=False,
            status=1,
        ).order_by("sort", "created_at").first()

        await SystemTenantUser.create(
            tenant_id=tenant.id,
            user_id=user_id,
            department_id=default_department.id if default_department else None,
            user_type=3,
            status=1,
        )

        default_role = await SystemRole.filter(
            tenant_id=tenant.id,
            code="user",
            is_del=False,
            status=1,
        ).first()
        if default_role:
            await SystemUserRole.create(
                tenant_id=tenant.id,
                user_id=user_id,
                role_id=default_role.id,
            )

        if redis:
            from utils.get_redis import RedisKeyConfig

            cache_key = f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
            if await redis.get(cache_key):
                await redis.delete(cache_key)

        return True, f"已成功加入租户 {tenant.name}！"

    @classmethod
    async def get_tenant_members(
        cls, tenant_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[dict], int]:
        filter_args = {"tenant_id": tenant_id, "is_del": False}
        total = await SystemTenantUser.filter(**filter_args).count()
        members = await SystemTenantUser.filter(**filter_args).prefetch_related(
            "user", "department"
        ).offset((page - 1) * page_size).limit(page_size).values(
            id="id",
            user_id="user__id",
            username="user__username",
            nickname="user__nickname",
            email="user__email",
            department_id="department__id",
            department_name="department__name",
            user_type="user_type",
            status="status",
            created_at="created_at",
        )
        return list(members), total

    @classmethod
    async def get_tenant_list(
        cls, page: int, page_size: int, filters: Optional[Dict[str, Any]] = None
    ):
        filter_args = {"is_del": False}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(**filter_args).count()
        data = await cls.model.filter(**filter_args).order_by("-created_at").offset(
            (page - 1) * page_size
        ).limit(page_size).values(
            id="id",
            created_at="created_at",
            updated_at="updated_at",
            name="name",
            code="code",
            status="status",
            invite_code="invite_code",
            allow_register="allow_register",
            remark="remark",
        )
        return data, total
