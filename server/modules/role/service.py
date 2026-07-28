# _*_ coding : UTF-8 _*_

from typing import List, Optional, Tuple

from core.common import BaseService
from modules import SystemDepartment
from modules.permission.model import PermissionType, SystemPermission
from modules.role.model import SystemRole, SystemRoleDepartment, SystemRolePermission
from utils.get_redis import RedisKeyConfig


class RoleService(BaseService):
    model = SystemRole
    excel_sheet_name = "角色数据"
    excel_columns = {
        "code": "角色编码",
        "name": "角色名称",
        "description": "角色描述",
        "status": "状态",
    }

    @staticmethod
    async def clear_role_cache(redis):
        try:
            user_infos = await redis.keys(f"{RedisKeyConfig.USER_INFO.key}*")
            if user_infos:
                await redis.delete(*user_infos)

            user_routes = await redis.keys(f"{RedisKeyConfig.USER_ROUTES.key}*")
            if user_routes:
                await redis.delete(*user_routes)

            role_keys = await redis.keys("role_*")
            if role_keys:
                await redis.delete(*role_keys)
        except Exception as e:
            print(f"清除缓存失败: {e}")

    @classmethod
    async def get_role_permission_ids(cls, role_id: str) -> dict:
        permissions = await SystemPermission.filter(
            role_permissions__role_id=role_id,
            role_permissions__is_del=False,
            is_del=False,
        ).all()
        return {
            "menus": [
                str(permission.id)
                for permission in permissions
                if permission.menu_type == PermissionType.MENU
            ],
            "buttons": [
                str(permission.id)
                for permission in permissions
                if permission.menu_type == PermissionType.BUTTON
            ],
            "apis": [
                str(permission.id)
                for permission in permissions
                if permission.menu_type == PermissionType.API
            ],
        }

    @classmethod
    async def set_role_permissions(cls, role_id: str, permission_ids: list[str]) -> dict:
        valid_ids = await SystemPermission.filter(
            id__in=[str(permission_id) for permission_id in permission_ids],
            menu_type__in=[
                PermissionType.MENU,
                PermissionType.BUTTON,
                PermissionType.API,
            ],
            is_del=False,
        ).values_list("id", flat=True)
        new_ids = set(str(permission_id) for permission_id in valid_ids)

        current_ids = set(
            str(permission_id)
            for permission_id in await SystemRolePermission.filter(
                role_id=role_id,
                permission__menu_type__in=[
                    PermissionType.MENU,
                    PermissionType.BUTTON,
                    PermissionType.API,
                ],
                is_del=False,
            ).values_list("permission_id", flat=True)
        )

        to_add = new_ids - current_ids
        to_remove = current_ids - new_ids

        added = 0
        for permission_id in to_add:
            relation = await SystemRolePermission.filter(
                role_id=role_id,
                permission_id=permission_id,
                is_del=True,
            ).first()
            if relation:
                relation.is_del = False
                await relation.save()
            else:
                await SystemRolePermission.create(
                    role_id=role_id, permission_id=permission_id
                )
            added += 1

        removed = 0
        if to_remove:
            removed = await SystemRolePermission.filter(
                role_id=role_id,
                permission_id__in=list(to_remove),
                is_del=False,
            ).update(is_del=True)

        return {"added": added, "removed": removed}

    @classmethod
    async def get_role_info_data(cls, role_id: str):
        role_data = await cls.model.filter(id=role_id, is_del=False).values(
            id="id",
            created_at="created_at",
            updated_at="updated_at",
            code="code",
            name="name",
            status="status",
            description="description",
            department_id="department_id",
            tenant_id="tenant_id",
            department_name="department__name",
            department_principal="department__principal",
            department_phone="department__phone",
            department_email="department__email",
        )
        if not role_data:
            return None

        role_info = role_data[0]
        permissions = await cls.get_role_permission_ids(role_id)
        role_info["permissions"] = (
            [{"obj": permission_id, "act": "menu"} for permission_id in permissions["menus"]]
            + [{"obj": permission_id, "act": "button"} for permission_id in permissions["buttons"]]
            + [{"obj": permission_id, "act": "api"} for permission_id in permissions["apis"]]
        )
        role_info["menu_ids"] = permissions["menus"]
        role_info["button_ids"] = permissions["buttons"]
        role_info["api_ids"] = permissions["apis"]
        return role_info

    @classmethod
    async def get_role_list_data(cls, filter_args: dict, page: int, page_size: int):
        total = await cls.model.filter(**filter_args, is_del=False).count()
        data = (
            await cls.model.filter(**filter_args, is_del=False)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values(
                id="id",
                created_at="created_at",
                updated_at="updated_at",
                code="code",
                name="name",
                status="status",
                description="description",
                tenant_id="tenant_id",
                department_id="department__id",
                department_name="department__name",
                department_principal="department__principal",
                department_phone="department__phone",
                department_email="department__email",
            )
        )
        return {
            "result": data,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    @classmethod
    async def get_role_permission_info_data(cls, role: SystemRole, permission: SystemPermission):
        if permission.menu_type == PermissionType.API:
            perm_type = "api"
        elif permission.menu_type == PermissionType.BUTTON:
            perm_type = "button"
        else:
            perm_type = "menu"

        has_permission = await SystemRolePermission.filter(
            role_id=role.id,
            permission_id=permission.id,
            is_del=False,
        ).exists()

        return {
            "role_id": str(role.id),
            "role_name": role.name,
            "role_code": role.code,
            "permission_id": str(permission.id),
            "permission_name": permission.title,
            "permission_auth": permission.code or permission.authMark,
            "permission_code": permission.code,
            "permission_type": permission.menu_type,
            "perm_type": perm_type,
            "has_permission": has_permission,
            "api_path": permission.api_path,
            "api_method": permission.api_method,
        }

    @classmethod
    async def get_role_permission_list_data(cls, role_id: str):
        permissions = await cls.get_role_permission_ids(role_id)
        menu_ids = permissions["menus"]
        button_ids = permissions["buttons"]
        api_ids = permissions["apis"]
        return {
            "actual_permission_ids": menu_ids + button_ids + api_ids,
            "menu_ids": menu_ids,
            "button_ids": button_ids,
            "api_ids": api_ids,
            "api_permission_ids": api_ids,
        }

    @classmethod
    async def create_role(cls, params: dict, tenant_id: Optional[str] = None) -> Tuple[bool, str]:
        if not params.get("department_id"):
            return False, "部门ID不能为空"

        if await cls.model.get_or_none(
            code=params.get("code"), tenant_id=tenant_id, is_del=False
        ):
            return False, "角色编码已存在"

        department = await SystemDepartment.get_or_none(
            id=params.get("department_id"), is_del=False
        )
        if not department:
            return False, "指定的部门不存在"

        await cls.model.create(
            code=params["code"],
            name=params["name"],
            description=params.get("description"),
            status=params.get("status", 1),
            department_id=department.id,
            tenant_id=tenant_id,
        )
        return True, "新增角色成功"

    @classmethod
    async def update_role(cls, role_id: str, update_data: dict) -> Tuple[bool, str]:
        role = await cls.model.get_or_none(id=role_id, is_del=False)
        if not role:
            return False, "角色不存在"

        if update_data.get("code"):
            existing = await cls.model.get_or_none(
                code=update_data["code"],
                tenant_id=role.tenant_id,
                is_del=False,
            )
            if existing and str(existing.id) != role_id:
                return False, "角色编码已存在"

        if update_data.get("department_id"):
            department = await SystemDepartment.get_or_none(
                id=update_data["department_id"], is_del=False
            )
            update_data["department_id"] = department.id if department else None

        update_data.pop("data_scope", None)

        await cls.update(role_id, update_data)
        return True, "修改角色成功"

    @classmethod
    async def add_role_permissions(cls, role_id: str, permission_ids: List[str]) -> Tuple[bool, str]:
        role = await cls.model.get_or_none(id=role_id, is_del=False)
        if not role:
            return False, "角色不存在"

        valid_permissions = await SystemPermission.filter(
            id__in=permission_ids,
            is_del=False,
        ).all()

        current_ids = set(
            str(pid)
            for pid in await SystemRolePermission.filter(
                role_id=role.id,
                is_del=False,
            ).values_list("permission_id", flat=True)
        )

        await cls.set_role_permissions(
            str(role.id), list(current_ids | {str(p.id) for p in valid_permissions})
        )
        return True, "新增角色权限成功"

    @classmethod
    async def delete_role_permission(cls, role_id: str, permission_id: str) -> Tuple[bool, str]:
        role = await cls.model.get_or_none(id=role_id, is_del=False)
        if not role:
            return False, "角色不存在"

        permission = await SystemPermission.get_or_none(id=permission_id, is_del=False)
        if not permission:
            return False, "权限不存在"

        await SystemRolePermission.filter(
            role_id=role.id,
            permission_id=permission_id,
            is_del=False,
        ).update(is_del=True)
        return True, "删除角色权限成功"

    @classmethod
    async def update_role_permissions(cls, role_id: str, permission_ids: List[str]) -> Tuple[bool, str]:
        role = await cls.model.get_or_none(id=role_id, is_del=False)
        if not role:
            return False, "角色不存在"

        await cls.set_role_permissions(str(role.id), permission_ids)
        return True, "修改角色权限成功"


class RolePermissionService(BaseService):
    model = SystemRolePermission


class RoleDepartmentService(BaseService):
    model = SystemRoleDepartment
