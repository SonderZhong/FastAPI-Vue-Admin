# _*_ coding : UTF-8 _*_
from enum import IntEnum
from typing import Optional, Set

from modules import (
    SystemDepartment,
    SystemPermission,
    SystemRoleDepartment,
    SystemUser,
    SystemUserRole,
    SystemTenantUser,
)
from modules.permission.model import PermissionType


class UserType(IntEnum):
    """
    用户类型
    """

    SUPER_ADMIN = 0
    """
    超级管理员
    """
    TENANT_ADMIN = 1
    """
    租户管理员
    """
    DEPT_ADMIN = 2
    """
    部门管理员
    """
    NORMAL_USER = 3
    """
    普通用户
    """


class DataScope(IntEnum):
    TENANT_ALL = 1
    """
    
    """
    DEPT_AND_CHILD = 2
    DEPT_ONLY = 3
    SELF_ONLY = 4
    CUSTOM_DEPT = 5
    ALL = 1


class DepartmentHelper:
    @staticmethod
    async def get_child_department_ids(
        department_id: str,
        tenant_id: Optional[str] = None,
        include_self: bool = True,
    ) -> Set[str]:
        result: Set[str] = (
            {str(department_id)} if include_self and department_id else set()
        )
        if not department_id:
            return result

        filters = {"parent_id": str(department_id), "is_del": False}
        if tenant_id:
            filters["tenant_id"] = tenant_id

        department = await SystemDepartment.filter(
            id=department_id, is_del=False
        ).first()
        if department and department.ancestor_path:
            path_filters = {
                "ancestor_path__startswith": department.ancestor_path,
                "is_del": False,
            }
            if tenant_id:
                path_filters["tenant_id"] = tenant_id
            descendants = await SystemDepartment.filter(**path_filters).values_list(
                "id", flat=True
            )
            result.update(str(item) for item in descendants)
            return result

        children = await SystemDepartment.filter(**filters).values_list("id", flat=True)
        for child_id in children:
            result.update(
                await DepartmentHelper.get_child_department_ids(
                    str(child_id),
                    tenant_id=tenant_id,
                    include_self=True,
                )
            )
        return result


class PermissionService:
    """Database-backed RBAC and data-scope service."""

    @staticmethod
    def is_platform_admin(user: dict | SystemUser) -> bool:
        user_type = user.get("user_type") if isinstance(user, dict) else user.user_type
        return user_type == UserType.SUPER_ADMIN

    @staticmethod
    def apply_tenant_filter(
        filters: dict, current_user: dict, field: str = "tenant_id"
    ) -> dict:
        tenant_id = current_user.get("tenant_id")
        if tenant_id:
            filters[field] = tenant_id
        return filters

    @classmethod
    async def get_user_permission_codes(
        cls, user_id: str, permission_type: int | None = None
    ) -> Set[str]:
        filters = {
            "role_permissions__role__user_roles__user_id": user_id,
            "role_permissions__role__user_roles__is_del": False,
            "role_permissions__role__is_del": False,
            "role_permissions__role__status": 1,
            "role_permissions__is_del": False,
            "is_del": False,
        }
        if permission_type is not None:
            filters["menu_type"] = permission_type

        permissions = await SystemPermission.filter(**filters).distinct().all()
        codes: Set[str] = set()
        for permission in permissions:
            code = permission.code or permission.authMark
            if code:
                codes.add(code)
        return codes

    @classmethod
    async def can_access_api(cls, user_id: str, path: str, method: str) -> bool:
        permissions = (
            await SystemPermission.filter(
                role_permissions__role__user_roles__user_id=user_id,
                role_permissions__role__user_roles__is_del=False,
                role_permissions__role__is_del=False,
                role_permissions__role__status=1,
                role_permissions__is_del=False,
                menu_type=PermissionType.API,
                is_del=False,
            )
            .distinct()
            .all()
        )

        method = method.upper()
        normalized_path = path[4:] if path.startswith("/api/") else path
        normalized_path = (
            normalized_path
            if normalized_path.startswith("/")
            else f"/{normalized_path}"
        )

        for permission in permissions:
            api_path = permission.api_path or permission.path
            if not api_path:
                continue
            methods = permission.api_method or ["*"]
            methods = [item.upper() for item in methods]
            if "*" not in methods and method not in methods:
                continue
            if cls._match_path(normalized_path, api_path):
                return True
        return False

    @classmethod
    async def get_data_scope(cls, user_id: str) -> dict:
        user = await SystemUser.filter(id=user_id, is_del=False).first()
        if not user:
            return cls._empty_scope(user_id)

        # 从 TenantUser 获取租户/部门/角色类型信息
        tenant_user = await SystemTenantUser.filter(
            user_id=user_id, is_del=False
        ).first()
        if not tenant_user:
            return cls._self_scope(user_id, UserType.NORMAL_USER, None, None)

        tenant_id = str(tenant_user.tenant_id) if tenant_user.tenant_id else None
        department_id = (
            str(tenant_user.department_id) if tenant_user.department_id else None
        )
        user_type = tenant_user.user_type

        # 超管直接返回全部权限
        if user_type == UserType.SUPER_ADMIN:
            return cls._all_scope(user_id, UserType.SUPER_ADMIN, tenant_id, department_id)

        user_roles = (
            await SystemUserRole.filter(
                user_id=user_id,
                is_del=False,
                role__is_del=False,
                role__status=1,
            )
            .prefetch_related("role")
            .all()
        )
        if not user_roles:
            return cls._self_scope(user_id, user_type, tenant_id, department_id)

        department_ids: Set[str] = set()
        strongest_scope = DataScope.SELF_ONLY
        has_all = False

        for user_role in user_roles:
            role = await user_role.role
            if tenant_id and role.tenant_id and str(role.tenant_id) != tenant_id:
                continue

            raw_scope = getattr(role, "data_scope", None)
            if raw_scope is None:
                if user_type == UserType.TENANT_ADMIN:
                    raw_scope = DataScope.TENANT_ALL
                elif user_type == UserType.DEPT_ADMIN:
                    raw_scope = DataScope.DEPT_AND_CHILD
                else:
                    raw_scope = DataScope.SELF_ONLY

            scope = DataScope(raw_scope or DataScope.SELF_ONLY)
            strongest_scope = min(strongest_scope, scope)

            if scope == DataScope.TENANT_ALL:
                has_all = True
            elif scope == DataScope.DEPT_AND_CHILD and department_id:
                department_ids.update(
                    await DepartmentHelper.get_child_department_ids(
                        department_id, tenant_id=tenant_id
                    )
                )
            elif scope == DataScope.DEPT_ONLY and department_id:
                department_ids.add(department_id)
            elif scope == DataScope.CUSTOM_DEPT:
                custom_ids = await SystemRoleDepartment.filter(
                    role_id=role.id,
                    is_del=False,
                    department__is_del=False,
                ).values_list("department_id", flat=True)
                department_ids.update(str(item) for item in custom_ids)

        if has_all:
            return cls._all_scope(user_id, user_type, tenant_id, department_id)
        if department_ids:
            return {
                "scope": strongest_scope,
                "user_id": user_id,
                "user_type": user_type,
                "tenant_id": tenant_id,
                "department_id": department_id,
                "department_ids": department_ids,
                "all": False,
            }
        return cls._self_scope(user_id, user_type, tenant_id, department_id)

    @staticmethod
    def _match_path(request_path: str, permission_path: str) -> bool:
        import re

        permission_path = (
            permission_path
            if permission_path.startswith("/")
            else f"/{permission_path}"
        )
        if request_path == permission_path:
            return True
        if "*" not in permission_path:
            return False
        pattern = "^" + re.escape(permission_path).replace(r"\*", ".*") + "$"
        return bool(re.match(pattern, request_path))

    @classmethod
    async def can_access_user_data(cls, operator_id: str, target_user_id: str) -> bool:
        if operator_id == target_user_id:
            return True

        scope = await cls.get_data_scope(operator_id)
        if scope["user_type"] == UserType.SUPER_ADMIN:
            return True

        target = await SystemUser.filter(id=target_user_id, is_del=False).first()
        if not target:
            return False

        target_tenant_user = await SystemTenantUser.filter(
            user_id=target_user_id,
            is_del=False,
        ).first()
        if not target_tenant_user or not cls._same_tenant(scope["tenant_id"], target_tenant_user):
            return False

        if scope["all"]:
            return True
        return bool(
            target_tenant_user.department_id
            and str(target_tenant_user.department_id) in scope["department_ids"]
        )

    @classmethod
    async def can_access_department_data(
        cls, operator_id: str, target_dept_id: str
    ) -> bool:
        scope = await cls.get_data_scope(operator_id)
        if scope["user_type"] == UserType.SUPER_ADMIN:
            return True
        if scope["all"]:
            if not scope["tenant_id"]:
                return True
            dept = await SystemDepartment.filter(
                id=target_dept_id, is_del=False
            ).first()
            return bool(dept and str(dept.tenant_id) == scope["tenant_id"])
        return target_dept_id in scope["department_ids"]

    @staticmethod
    def _same_tenant(tenant_id: Optional[str], obj) -> bool:
        if not tenant_id:
            return True
        return str(getattr(obj, "tenant_id", "")) == tenant_id

    @staticmethod
    def _empty_scope(user_id: str) -> dict:
        return {
            "scope": DataScope.SELF_ONLY,
            "user_id": user_id,
            "user_type": UserType.NORMAL_USER,
            "tenant_id": None,
            "department_id": None,
            "department_ids": set(),
            "all": False,
        }

    @staticmethod
    def _all_scope(
        user_id: str,
        user_type: int,
        tenant_id: Optional[str],
        department_id: Optional[str],
    ) -> dict:
        return {
            "scope": DataScope.TENANT_ALL,
            "user_id": user_id,
            "user_type": user_type,
            "tenant_id": tenant_id,
            "department_id": department_id,
            "department_ids": set(),
            "all": True,
        }

    @staticmethod
    def _self_scope(
        user_id: str,
        user_type: int,
        tenant_id: Optional[str],
        department_id: Optional[str],
    ) -> dict:
        return {
            "scope": DataScope.SELF_ONLY,
            "user_id": user_id,
            "user_type": user_type,
            "tenant_id": tenant_id,
            "department_id": department_id,
            "department_ids": {department_id} if department_id else set(),
            "all": False,
        }
