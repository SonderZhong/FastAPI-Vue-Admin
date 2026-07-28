# _*_ coding : UTF-8 _*_
"""
数据库操作工具

提供用户、角色、部门、权限、配置、租户等核心业务的 CRUD 操作
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import yaml
from tortoise import Tortoise


def get_db_url() -> str:
    """获取数据库连接 URL"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    nodes = config.get("database", {}).get("nodes", [])
    if not nodes:
        raise ValueError("未配置数据库节点")
    db = nodes[0]
    engine = db.get("engine", "sqlite")
    if engine == "sqlite":
        return f"sqlite://{db.get('database', 'fva.db')}"
    elif engine == "mysql":
        return f"mysql://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
    else:
        return f"postgres://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"


@asynccontextmanager
async def get_db_connection():
    """获取数据库连接上下文"""
    if not Tortoise._inited:
        await Tortoise.init(
            config={
                "connections": {"system": get_db_url()},
                "apps": {
                    "system": {
                        "models": [
                            "modules.config.model",
                            "modules.department.model",
                            "modules.dictionary.model",
                            "modules.dictionary.item_model",
                            "modules.file.model",
                            "modules.log.model",
                            "modules.notification.model",
                            "modules.permission.model",
                            "modules.role.model",
                            "modules.tenant.model",
                            "modules.user.model",
                        ],
                        "default_connection": "system",
                    }
                },
            },
        )
    yield


def register(mcp):
    """注册数据库工具"""

    from modules import (
        SystemUser,
        SystemRole,
        SystemDepartment,
        SystemPermission,
        SystemConfig,
        SystemTenant,
    )

    # ==================== 用户管理 ====================

    @mcp.tool()
    async def list_users(
        page: int = 1,
        page_size: int = 10,
        username: Optional[str] = None,
        status: Optional[int] = None,
    ) -> str:
        """查询用户列表"""
        async with get_db_connection():
            filters = {"is_del": False}
            if username:
                filters["username__icontains"] = username
            if status is not None:
                filters["status"] = status
            total = await SystemUser.filter(**filters).count()
            users = (
                await SystemUser.filter(**filters)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .values(
                    "id",
                    "username",
                    "nickname",
                    "email",
                    "phone",
                    "status",
                    "created_at",
                )
            )
            return json.dumps(
                {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": list(users),
                },
                default=str,
                ensure_ascii=False,
            )

    @mcp.tool()
    async def get_user(user_id: str) -> str:
        """获取用户详情"""
        async with get_db_connection():
            user = (
                await SystemUser.filter(id=user_id, is_del=False)
                .first()
                .values(
                    "id",
                    "username",
                    "nickname",
                    "email",
                    "phone",
                    "avatar",
                    "gender",
                    "status",
                    "created_at",
                )
            )
            if not user:
                return json.dumps({"error": "用户不存在"}, ensure_ascii=False)
            return json.dumps(user, default=str, ensure_ascii=False)

    @mcp.tool()
    async def search_users(keyword: str, page: int = 1, page_size: int = 10) -> str:
        """搜索用户（支持用户名、昵称、邮箱、手机号模糊搜索）"""
        async with get_db_connection():
            from tortoise.expressions import Q

            q = (
                Q(username__icontains=keyword)
                | Q(nickname__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(phone__icontains=keyword)
            )
            total = await SystemUser.filter(q, is_del=False).count()
            users = (
                await SystemUser.filter(q, is_del=False)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .values("id", "username", "nickname", "email", "phone", "status")
            )
            return json.dumps(
                {"total": total, "data": list(users)}, default=str, ensure_ascii=False
            )

    # ==================== 角色管理 ====================

    @mcp.tool()
    async def list_roles(page: int = 1, page_size: int = 10) -> str:
        """查询角色列表"""
        async with get_db_connection():
            total = await SystemRole.filter(is_del=False).count()
            roles = (
                await SystemRole.filter(is_del=False)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .values("id", "name", "code", "description", "status", "created_at")
            )
            return json.dumps(
                {"total": total, "data": list(roles)}, default=str, ensure_ascii=False
            )

    @mcp.tool()
    async def get_role(role_id: str) -> str:
        """获取角色详情"""
        async with get_db_connection():
            role = (
                await SystemRole.filter(id=role_id, is_del=False)
                .first()
                .values(
                    "id",
                    "name",
                    "code",
                    "description",
                    "status",
                    "department_id",
                    "created_at",
                )
            )
            if not role:
                return json.dumps({"error": "角色不存在"}, ensure_ascii=False)
            return json.dumps(role, default=str, ensure_ascii=False)

    @mcp.tool()
    async def create_role(
        name: str, code: str, description: Optional[str] = None, status: int = 1
    ) -> str:
        """创建角色"""
        async with get_db_connection():
            if await SystemRole.filter(code=code, is_del=False).first():
                return json.dumps(
                    {"success": False, "msg": f"角色编码 {code} 已存在"},
                    ensure_ascii=False,
                )
            role = await SystemRole.create(
                name=name, code=code, description=description, status=status
            )
            return json.dumps(
                {
                    "success": True,
                    "id": str(role.id),
                    "name": role.name,
                    "code": role.code,
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def update_role(
        role_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[int] = None,
    ) -> str:
        """更新角色"""
        async with get_db_connection():
            role = await SystemRole.filter(id=role_id, is_del=False).first()
            if not role:
                return json.dumps(
                    {"success": False, "msg": "角色不存在"}, ensure_ascii=False
                )
            if name is not None:
                role.name = name
            if description is not None:
                role.description = description
            if status is not None:
                role.status = status
            await role.save()
            return json.dumps(
                {"success": True, "msg": "角色更新成功"}, ensure_ascii=False
            )

    @mcp.tool()
    async def delete_role(role_id: str) -> str:
        """删除角色（软删除）"""
        async with get_db_connection():
            role = await SystemRole.filter(id=role_id, is_del=False).first()
            if not role:
                return json.dumps(
                    {"success": False, "msg": "角色不存在"}, ensure_ascii=False
                )
            role.is_del = True
            await role.save()
            return json.dumps(
                {"success": True, "msg": "角色删除成功"}, ensure_ascii=False
            )

    # ==================== 部门管理 ====================

    @mcp.tool()
    async def list_departments() -> str:
        """查询部门列表"""
        async with get_db_connection():
            departments = (
                await SystemDepartment.filter(is_del=False)
                .order_by("sort")
                .values(
                    "id",
                    "name",
                    "parent_id",
                    "principal",
                    "phone",
                    "email",
                    "status",
                    "sort",
                )
            )
            return json.dumps(list(departments), default=str, ensure_ascii=False)

    @mcp.tool()
    async def get_department(dept_id: str) -> str:
        """获取部门详情"""
        async with get_db_connection():
            dept = (
                await SystemDepartment.filter(id=dept_id, is_del=False)
                .first()
                .values(
                    "id",
                    "name",
                    "parent_id",
                    "principal",
                    "phone",
                    "email",
                    "status",
                    "sort",
                    "remark",
                )
            )
            if not dept:
                return json.dumps({"error": "部门不存在"}, ensure_ascii=False)
            return json.dumps(dept, default=str, ensure_ascii=False)

    @mcp.tool()
    async def create_department(
        name: str,
        principal: str,
        parent_id: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        sort: int = 0,
    ) -> str:
        """创建部门"""
        async with get_db_connection():
            dept = await SystemDepartment.create(
                name=name,
                principal=principal,
                parent_id=parent_id,
                phone=phone,
                email=email,
                sort=sort,
            )
            return json.dumps(
                {"success": True, "id": str(dept.id), "name": dept.name},
                ensure_ascii=False,
            )

    @mcp.tool()
    async def update_department(
        dept_id: str,
        name: Optional[str] = None,
        principal: Optional[str] = None,
        status: Optional[int] = None,
    ) -> str:
        """更新部门"""
        async with get_db_connection():
            dept = await SystemDepartment.filter(id=dept_id, is_del=False).first()
            if not dept:
                return json.dumps(
                    {"success": False, "msg": "部门不存在"}, ensure_ascii=False
                )
            if name is not None:
                dept.name = name
            if principal is not None:
                dept.principal = principal
            if status is not None:
                dept.status = status
            await dept.save()
            return json.dumps(
                {"success": True, "msg": "部门更新成功"}, ensure_ascii=False
            )

    @mcp.tool()
    async def delete_department(dept_id: str) -> str:
        """删除部门（软删除）"""
        async with get_db_connection():
            dept = await SystemDepartment.filter(id=dept_id, is_del=False).first()
            if not dept:
                return json.dumps(
                    {"success": False, "msg": "部门不存在"}, ensure_ascii=False
                )
            children = await SystemDepartment.filter(
                parent_id=dept_id, is_del=False
            ).count()
            if children > 0:
                return json.dumps(
                    {"success": False, "msg": "该部门下有子部门，无法删除"},
                    ensure_ascii=False,
                )
            dept.is_del = True
            await dept.save()
            return json.dumps(
                {"success": True, "msg": "部门删除成功"}, ensure_ascii=False
            )

    # ==================== 租户管理 ====================

    @mcp.tool()
    async def list_tenants(page: int = 1, page_size: int = 10) -> str:
        """查询租户列表"""
        async with get_db_connection():
            total = await SystemTenant.filter(is_del=False).count()
            tenants = (
                await SystemTenant.filter(is_del=False)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .values(
                    "id",
                    "name",
                    "code",
                    "status",
                    "invite_code",
                    "allow_register",
                    "created_at",
                )
            )
            return json.dumps(
                {"total": total, "data": list(tenants)}, default=str, ensure_ascii=False
            )

    @mcp.tool()
    async def get_tenant(tenant_id: str) -> str:
        """获取租户详情"""
        async with get_db_connection():
            tenant = (
                await SystemTenant.filter(id=tenant_id, is_del=False)
                .first()
                .values(
                    "id",
                    "name",
                    "code",
                    "status",
                    "invite_code",
                    "allow_register",
                    "remark",
                    "created_at",
                )
            )
            if not tenant:
                return json.dumps({"error": "租户不存在"}, ensure_ascii=False)
            return json.dumps(tenant, default=str, ensure_ascii=False)

    @mcp.tool()
    async def get_tenant_members(
        tenant_id: str, page: int = 1, page_size: int = 10
    ) -> str:
        """获取租户成员列表"""
        async with get_db_connection():
            from modules.user.model import SystemTenantUser

            total = await SystemTenantUser.filter(
                tenant_id=tenant_id, is_del=False
            ).count()
            members = (
                await SystemTenantUser.filter(tenant_id=tenant_id, is_del=False)
                .prefetch_related(
                    "user",
                    "department",
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
                .values(
                    id="id",
                    user_id="user__id",
                    username="user__username",
                    nickname="user__nickname",
                    department_id="department__id",
                    department_name="department__name",
                    user_type="user_type",
                    status="status",
                )
            )
            return json.dumps(
                {"total": total, "data": list(members)}, default=str, ensure_ascii=False
            )

    # ==================== 配置管理 ====================

    @mcp.tool()
    async def list_configs(group: Optional[str] = None) -> str:
        """查询系统配置列表"""
        async with get_db_connection():
            filters = {"is_del": False}
            if group:
                filters["group"] = group
            configs = await SystemConfig.filter(**filters).values(
                "id", "name", "key", "value", "group", "type", "remark"
            )
            return json.dumps(list(configs), default=str, ensure_ascii=False)

    @mcp.tool()
    async def get_config(key: str) -> str:
        """获取单个配置值"""
        async with get_db_connection():
            config = await SystemConfig.filter(key=key, is_del=False).first()
            if not config:
                return json.dumps({"error": f"配置 {key} 不存在"}, ensure_ascii=False)
            return json.dumps(
                {
                    "key": config.key,
                    "value": config.value,
                    "name": config.name,
                    "group": config.group,
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def set_config(key: str, value: str) -> str:
        """设置配置值"""
        async with get_db_connection():
            config = await SystemConfig.filter(key=key, is_del=False).first()
            if not config:
                return json.dumps(
                    {"success": False, "msg": f"配置 {key} 不存在"}, ensure_ascii=False
                )
            config.value = value
            await config.save()
            return json.dumps(
                {"success": True, "msg": f"配置 {key} 已更新"}, ensure_ascii=False
            )

    # ==================== 权限管理 ====================

    @mcp.tool()
    async def list_permissions(menu_type: Optional[int] = None) -> str:
        """查询权限列表（0菜单，1按钮，2接口）"""
        async with get_db_connection():
            filters = {"is_del": False}
            if menu_type is not None:
                filters["menu_type"] = menu_type
            permissions = (
                await SystemPermission.filter(**filters)
                .order_by("order")
                .values(
                    "id",
                    "menu_type",
                    "parent_id",
                    "name",
                    "path",
                    "title",
                    "icon",
                    "authMark",
                    "api_path",
                    "order",
                )
            )
            return json.dumps(list(permissions), default=str, ensure_ascii=False)

    @mcp.tool()
    async def get_permission(permission_id: str) -> str:
        """获取权限详情"""
        async with get_db_connection():
            perm = (
                await SystemPermission.filter(id=permission_id, is_del=False)
                .first()
                .values(
                    "id",
                    "menu_type",
                    "parent_id",
                    "name",
                    "path",
                    "component",
                    "title",
                    "icon",
                    "api_path",
                    "api_method",
                    "data_scope",
                    "authMark",
                    "isHide",
                    "keepAlive",
                    "order",
                    "remark",
                )
            )
            if not perm:
                return json.dumps({"error": "权限不存在"}, ensure_ascii=False)
            return json.dumps(perm, default=str, ensure_ascii=False)

    # ==================== SQL 执行 ====================

    @mcp.tool()
    async def execute_sql(sql: str) -> str:
        """执行只读 SQL 查询（仅支持 SELECT）"""
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return json.dumps({"error": "仅支持 SELECT 查询"}, ensure_ascii=False)
        dangerous = [
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "TRUNCATE",
            "ALTER",
            "CREATE",
        ]
        for kw in dangerous:
            if kw in sql_upper:
                return json.dumps({"error": f"不允许使用 {kw}"}, ensure_ascii=False)

        async with get_db_connection():
            conn = Tortoise.get_connection("system")
            try:
                result = await conn.execute_query(sql)
                return json.dumps(
                    {"count": result[0], "data": result[1]},
                    default=str,
                    ensure_ascii=False,
                )
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    # ==================== 统计工具 ====================

    @mcp.tool()
    async def get_statistics() -> str:
        """获取系统统计数据"""
        async with get_db_connection():
            user_count = await SystemUser.filter(is_del=False).count()
            active_users = await SystemUser.filter(is_del=False, status=1).count()
            role_count = await SystemRole.filter(is_del=False).count()
            dept_count = await SystemDepartment.filter(is_del=False).count()
            perm_count = await SystemPermission.filter(is_del=False).count()
            tenant_count = await SystemTenant.filter(is_del=False).count()
            return json.dumps(
                {
                    "user_count": user_count,
                    "active_users": active_users,
                    "role_count": role_count,
                    "department_count": dept_count,
                    "permission_count": perm_count,
                    "tenant_count": tenant_count,
                },
                ensure_ascii=False,
            )
