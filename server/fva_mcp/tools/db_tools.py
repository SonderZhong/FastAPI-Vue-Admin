# _*_ coding : UTF-8 _*_
# @Time : 2025/01/02
# @Author : sonder
# @File : db_tools.py
# @Comment : 数据库操作工具

import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import yaml
from tortoise import Tortoise

from models import SystemRole, SystemDepartment, SystemPermission, SystemConfig, SystemOperationLog, SystemLoginLog


def get_db_url() -> str:
    """获取数据库连接 URL"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError("配置文件不存在，请先完成系统初始化")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    db = config.get("database", {})
    engine = db.get("engine", "mysql")
    username = db.get("username", "root")
    password = db.get("password", "")
    host = db.get("host", "127.0.0.1")
    port = db.get("port", 3306)
    database = db.get("database", "digital-management")
    
    if engine == "mysql":
        return f"mysql://{username}:{password}@{host}:{port}/{database}"
    else:
        return f"postgres://{username}:{password}@{host}:{port}/{database}"


@asynccontextmanager
async def get_db_connection():
    """获取数据库连接上下文"""
    if not Tortoise._inited:
        await Tortoise.init(
            db_url=get_db_url(),
            modules={"system": [
                "models.user",
                "models.role",
                "models.department",
                "models.permission",
                "models.log",
                "models.config",
                "models.notification",
                "models.file",
                "models.casbin",
            ]}
        )
    try:
        yield
    finally:
        pass


def register(mcp):
    """注册数据库工具到 MCP 服务器"""
    
    # 延迟导入模型
    from models import (
        SystemUser
    )
    
    # ==================== 用户管理工具 ====================
    
    @mcp.tool()
    async def list_users(
        page: int = 1,
        page_size: int = 10,
        username: Optional[str] = None,
        status: Optional[int] = None
    ) -> str:
        """
        查询用户列表
        
        Args:
            page: 页码，默认1
            page_size: 每页数量，默认10
            username: 用户名筛选（模糊匹配）
            status: 状态筛选（1启用，0禁用）
        
        Returns:
            用户列表 JSON
        """
        async with get_db_connection():
            filters = {"is_del": False}
            if username:
                filters["username__icontains"] = username
            if status is not None:
                filters["status"] = status
            
            total = await SystemUser.filter(**filters).count()
            users = await SystemUser.filter(**filters).offset((page - 1) * page_size).limit(page_size).values(
                "id", "username", "nickname", "email", "phone", "status", "user_type", "created_at"
            )
            
            return json.dumps({
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": users
            }, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def get_user(user_id: str) -> str:
        """
        获取用户详情
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户详情 JSON
        """
        async with get_db_connection():
            user = await SystemUser.filter(id=user_id, is_del=False).first().values(
                "id", "username", "nickname", "email", "phone", "avatar",
                "gender", "status", "user_type", "department_id", "created_at"
            )
            
            if not user:
                return json.dumps({"error": "用户不存在"}, ensure_ascii=False)
            
            return json.dumps(user, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def update_user_status(user_id: str, status: int) -> str:
        """
        更新用户状态
        
        Args:
            user_id: 用户ID
            status: 状态（1启用，0禁用）
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            user = await SystemUser.filter(id=user_id, is_del=False).first()
            if not user:
                return json.dumps({"success": False, "msg": "用户不存在"}, ensure_ascii=False)
            
            user.status = status
            await user.save()
            
            return json.dumps({"success": True, "msg": f"用户状态已更新为 {'启用' if status == 1 else '禁用'}"}, ensure_ascii=False)

    
    # ==================== 角色管理工具 ====================
    
    @mcp.tool()
    async def list_roles(page: int = 1, page_size: int = 10) -> str:
        """
        查询角色列表
        
        Args:
            page: 页码，默认1
            page_size: 每页数量，默认10
        
        Returns:
            角色列表 JSON
        """
        async with get_db_connection():
            total = await SystemRole.filter(is_del=False).count()
            roles = await SystemRole.filter(is_del=False).offset((page - 1) * page_size).limit(page_size).values(
                "id", "name", "code", "description", "status", "created_at"
            )
            
            return json.dumps({
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": roles
            }, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def get_role(role_id: str) -> str:
        """
        获取角色详情
        
        Args:
            role_id: 角色ID
        
        Returns:
            角色详情 JSON
        """
        async with get_db_connection():
            role = await SystemRole.filter(id=role_id, is_del=False).first().values(
                "id", "name", "code", "description", "status", "department_id", "created_at"
            )
            
            if not role:
                return json.dumps({"error": "角色不存在"}, ensure_ascii=False)
            
            return json.dumps(role, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def create_role(
        name: str,
        code: str,
        description: Optional[str] = None,
        status: int = 1,
        department_id: Optional[str] = None
    ) -> str:
        """
        创建角色
        
        Args:
            name: 角色名称
            code: 角色编码（唯一）
            description: 角色描述
            status: 状态（1启用，0禁用）
            department_id: 所属部门ID
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            # 检查编码是否已存在
            existing = await SystemRole.filter(code=code, is_del=False).first()
            if existing:
                return json.dumps({"success": False, "msg": f"角色编码 {code} 已存在"}, ensure_ascii=False)
            
            role = await SystemRole.create(
                id=str(uuid.uuid4()),
                name=name,
                code=code,
                description=description,
                status=status,
                department_id=department_id
            )
            
            return json.dumps({
                "success": True,
                "msg": "角色创建成功",
                "data": {"id": str(role.id), "name": role.name, "code": role.code}
            }, ensure_ascii=False)
    
    @mcp.tool()
    async def update_role(
        role_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[int] = None
    ) -> str:
        """
        更新角色
        
        Args:
            role_id: 角色ID
            name: 角色名称
            description: 角色描述
            status: 状态（1启用，0禁用）
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            role = await SystemRole.filter(id=role_id, is_del=False).first()
            if not role:
                return json.dumps({"success": False, "msg": "角色不存在"}, ensure_ascii=False)
            
            if name is not None:
                role.name = name
            if description is not None:
                role.description = description
            if status is not None:
                role.status = status
            
            await role.save()
            
            return json.dumps({"success": True, "msg": "角色更新成功"}, ensure_ascii=False)
    
    @mcp.tool()
    async def delete_role(role_id: str) -> str:
        """
        删除角色（软删除）
        
        Args:
            role_id: 角色ID
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            role = await SystemRole.filter(id=role_id, is_del=False).first()
            if not role:
                return json.dumps({"success": False, "msg": "角色不存在"}, ensure_ascii=False)
            
            role.is_del = True
            await role.save()
            
            return json.dumps({"success": True, "msg": "角色删除成功"}, ensure_ascii=False)

    
    # ==================== 部门管理工具 ====================
    
    @mcp.tool()
    async def list_departments() -> str:
        """
        查询部门树形列表
        
        Returns:
            部门列表 JSON
        """
        async with get_db_connection():
            departments = await SystemDepartment.filter(is_del=False).order_by("sort").values(
                "id", "name", "parent_id", "principal", "phone", "email", "status", "sort"
            )
            
            return json.dumps(departments, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def get_department(dept_id: str) -> str:
        """
        获取部门详情
        
        Args:
            dept_id: 部门ID
        
        Returns:
            部门详情 JSON
        """
        async with get_db_connection():
            dept = await SystemDepartment.filter(id=dept_id, is_del=False).first().values(
                "id", "name", "parent_id", "principal", "phone", "email", "status", "sort", "remark"
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
        status: int = 1,
        remark: Optional[str] = None
    ) -> str:
        """
        创建部门
        
        Args:
            name: 部门名称
            principal: 部门负责人
            parent_id: 上级部门ID
            phone: 部门电话
            email: 部门邮箱
            sort: 排序（0最高）
            status: 状态（1正常，0停用）
            remark: 备注
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            dept = await SystemDepartment.create(
                id=str(uuid.uuid4()),
                name=name,
                principal=principal,
                parent_id=parent_id,
                phone=phone,
                email=email,
                sort=sort,
                status=status,
                remark=remark
            )
            
            return json.dumps({
                "success": True,
                "msg": "部门创建成功",
                "data": {"id": str(dept.id), "name": dept.name}
            }, ensure_ascii=False)
    
    @mcp.tool()
    async def update_department(
        dept_id: str,
        name: Optional[str] = None,
        principal: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        sort: Optional[int] = None,
        status: Optional[int] = None,
        remark: Optional[str] = None
    ) -> str:
        """
        更新部门
        
        Args:
            dept_id: 部门ID
            name: 部门名称
            principal: 部门负责人
            phone: 部门电话
            email: 部门邮箱
            sort: 排序
            status: 状态（1正常，0停用）
            remark: 备注
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            dept = await SystemDepartment.filter(id=dept_id, is_del=False).first()
            if not dept:
                return json.dumps({"success": False, "msg": "部门不存在"}, ensure_ascii=False)
            
            if name is not None:
                dept.name = name
            if principal is not None:
                dept.principal = principal
            if phone is not None:
                dept.phone = phone
            if email is not None:
                dept.email = email
            if sort is not None:
                dept.sort = sort
            if status is not None:
                dept.status = status
            if remark is not None:
                dept.remark = remark
            
            await dept.save()
            
            return json.dumps({"success": True, "msg": "部门更新成功"}, ensure_ascii=False)
    
    @mcp.tool()
    async def delete_department(dept_id: str) -> str:
        """
        删除部门（软删除）
        
        Args:
            dept_id: 部门ID
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            dept = await SystemDepartment.filter(id=dept_id, is_del=False).first()
            if not dept:
                return json.dumps({"success": False, "msg": "部门不存在"}, ensure_ascii=False)
            
            # 检查是否有子部门
            children = await SystemDepartment.filter(parent_id=dept_id, is_del=False).count()
            if children > 0:
                return json.dumps({"success": False, "msg": "该部门下有子部门，无法删除"}, ensure_ascii=False)
            
            dept.is_del = True
            await dept.save()
            
            return json.dumps({"success": True, "msg": "部门删除成功"}, ensure_ascii=False)

    
    # ==================== 权限管理工具 ====================
    
    @mcp.tool()
    async def list_permissions(menu_type: Optional[int] = None) -> str:
        """
        查询权限列表
        
        Args:
            menu_type: 权限类型（0菜单，1按钮，2接口），不传则查询全部
        
        Returns:
            权限列表 JSON
        """
        async with get_db_connection():
            filters = {"is_del": False}
            if menu_type is not None:
                filters["menu_type"] = menu_type
            
            permissions = await SystemPermission.filter(**filters).order_by("order").values(
                "id", "menu_type", "parent_id", "name", "path", "title", "icon",
                "authTitle", "authMark", "api_path", "api_method", "order"
            )
            
            return json.dumps(permissions, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def get_permission(permission_id: str) -> str:
        """
        获取权限详情
        
        Args:
            permission_id: 权限ID
        
        Returns:
            权限详情 JSON
        """
        async with get_db_connection():
            perm = await SystemPermission.filter(id=permission_id, is_del=False).first().values(
                "id", "menu_type", "parent_id", "name", "path", "component", "title", "icon",
                "api_path", "api_method", "data_scope", "authTitle", "authMark",
                "isHide", "keepAlive", "order", "remark", "min_user_type"
            )
            
            if not perm:
                return json.dumps({"error": "权限不存在"}, ensure_ascii=False)
            
            return json.dumps(perm, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def create_permission(
        menu_type: int,
        name: str,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        path: Optional[str] = None,
        component: Optional[str] = None,
        icon: Optional[str] = None,
        api_path: Optional[str] = None,
        api_method: Optional[str] = None,
        authTitle: Optional[str] = None,
        authMark: Optional[str] = None,
        order: int = 999,
        remark: Optional[str] = None
    ) -> str:
        """
        创建权限
        
        Args:
            menu_type: 权限类型（0菜单，1按钮，2接口）
            name: 权限名称/路由名称
            title: 菜单标题
            parent_id: 父权限ID
            path: 路由路径
            component: 前端组件路径
            icon: 图标
            api_path: API接口路径（接口类型使用）
            api_method: HTTP方法JSON数组，如 '["GET","POST"]'
            authTitle: 权限标题（按钮类型使用）
            authMark: 权限标识（按钮类型使用）
            order: 排序
            remark: 备注
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            perm_data = {
                "id": str(uuid.uuid4()),
                "menu_type": menu_type,
                "name": name,
                "title": title,
                "parent_id": parent_id,
                "path": path,
                "component": component,
                "icon": icon,
                "authTitle": authTitle,
                "authMark": authMark,
                "order": order,
                "remark": remark
            }
            
            if api_path:
                perm_data["api_path"] = api_path
            if api_method:
                perm_data["api_method"] = json.loads(api_method) if isinstance(api_method, str) else api_method
            
            perm = await SystemPermission.create(**perm_data)
            
            return json.dumps({
                "success": True,
                "msg": "权限创建成功",
                "data": {"id": str(perm.id), "name": perm.name}
            }, ensure_ascii=False)
    
    @mcp.tool()
    async def update_permission(
        permission_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        path: Optional[str] = None,
        component: Optional[str] = None,
        icon: Optional[str] = None,
        api_path: Optional[str] = None,
        api_method: Optional[str] = None,
        authTitle: Optional[str] = None,
        authMark: Optional[str] = None,
        order: Optional[int] = None,
        remark: Optional[str] = None
    ) -> str:
        """
        更新权限
        
        Args:
            permission_id: 权限ID
            name: 权限名称
            title: 菜单标题
            parent_id: 父权限ID
            path: 路由路径
            component: 前端组件路径
            icon: 图标
            api_path: API接口路径
            api_method: HTTP方法JSON数组
            authTitle: 权限标题
            authMark: 权限标识
            order: 排序
            remark: 备注
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            perm = await SystemPermission.filter(id=permission_id, is_del=False).first()
            if not perm:
                return json.dumps({"success": False, "msg": "权限不存在"}, ensure_ascii=False)
            
            if name is not None:
                perm.name = name
            if title is not None:
                perm.title = title
            if parent_id is not None:
                perm.parent_id = parent_id
            if path is not None:
                perm.path = path
            if component is not None:
                perm.component = component
            if icon is not None:
                perm.icon = icon
            if api_path is not None:
                perm.api_path = api_path
            if api_method is not None:
                perm.api_method = json.loads(api_method) if isinstance(api_method, str) else api_method
            if authTitle is not None:
                perm.authTitle = authTitle
            if authMark is not None:
                perm.authMark = authMark
            if order is not None:
                perm.order = order
            if remark is not None:
                perm.remark = remark
            
            await perm.save()
            
            return json.dumps({"success": True, "msg": "权限更新成功"}, ensure_ascii=False)
    
    @mcp.tool()
    async def delete_permission(permission_id: str) -> str:
        """
        删除权限（软删除）
        
        Args:
            permission_id: 权限ID
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            perm = await SystemPermission.filter(id=permission_id, is_del=False).first()
            if not perm:
                return json.dumps({"success": False, "msg": "权限不存在"}, ensure_ascii=False)
            
            # 检查是否有子权限
            children = await SystemPermission.filter(parent_id=permission_id, is_del=False).count()
            if children > 0:
                return json.dumps({"success": False, "msg": "该权限下有子权限，无法删除"}, ensure_ascii=False)
            
            perm.is_del = True
            await perm.save()
            
            return json.dumps({"success": True, "msg": "权限删除成功"}, ensure_ascii=False)

    
    # ==================== 配置管理工具 ====================
    
    @mcp.tool()
    async def list_configs(group_name: Optional[str] = None) -> str:
        """
        查询系统配置列表
        
        Args:
            group_name: 配置分组名称
        
        Returns:
            配置列表 JSON
        """
        async with get_db_connection():
            filters = {"is_del": False}
            if group_name:
                filters["group_name"] = group_name
            
            configs = await SystemConfig.filter(**filters).values(
                "id", "name", "key", "value", "type", "group_name", "remark"
            )
            
            return json.dumps(configs, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def get_config(key: str) -> str:
        """
        获取单个配置值
        
        Args:
            key: 配置键名
        
        Returns:
            配置值
        """
        async with get_db_connection():
            config = await SystemConfig.filter(key=key, is_del=False).first()
            
            if not config:
                return json.dumps({"error": f"配置 {key} 不存在"}, ensure_ascii=False)
            
            return json.dumps({
                "key": config.key,
                "value": config.value,
                "name": config.name
            }, ensure_ascii=False)
    
    @mcp.tool()
    async def set_config(key: str, value: str) -> str:
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        
        Returns:
            操作结果
        """
        async with get_db_connection():
            config = await SystemConfig.filter(key=key, is_del=False).first()
            
            if not config:
                return json.dumps({"success": False, "msg": f"配置 {key} 不存在"}, ensure_ascii=False)
            
            config.value = value
            await config.save()
            
            return json.dumps({"success": True, "msg": f"配置 {key} 已更新"}, ensure_ascii=False)
    
    # ==================== 日志查询工具 ====================
    
    @mcp.tool()
    async def list_operation_logs(
        page: int = 1,
        page_size: int = 10,
        operation_type: Optional[int] = None
    ) -> str:
        """
        查询操作日志
        
        Args:
            page: 页码，默认1
            page_size: 每页数量，默认10
            operation_type: 操作类型（1新增，2修改，3删除，4查询）
        
        Returns:
            操作日志列表 JSON
        """
        async with get_db_connection():
            filters = {"is_del": False}
            if operation_type is not None:
                filters["operation_type"] = operation_type
            
            total = await SystemOperationLog.filter(**filters).count()
            logs = await SystemOperationLog.filter(**filters).order_by("-created_at").offset((page - 1) * page_size).limit(page_size).values(
                "id", "operation_name", "operation_type", "request_path", "request_method",
                "host", "status", "cost_time", "created_at"
            )
            
            return json.dumps({
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": logs
            }, default=str, ensure_ascii=False)
    
    @mcp.tool()
    async def list_login_logs(page: int = 1, page_size: int = 10) -> str:
        """
        查询登录日志
        
        Args:
            page: 页码，默认1
            page_size: 每页数量，默认10
        
        Returns:
            登录日志列表 JSON
        """
        async with get_db_connection():
            total = await SystemLoginLog.filter(is_del=False).count()
            logs = await SystemLoginLog.filter(is_del=False).order_by("-created_at").offset((page - 1) * page_size).limit(page_size).values(
                "id", "login_ip", "login_location", "browser", "os", "status", "created_at"
            )
            
            return json.dumps({
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": logs
            }, default=str, ensure_ascii=False)
    
    # ==================== 统计工具 ====================
    
    @mcp.tool()
    async def get_statistics() -> str:
        """
        获取系统统计数据
        
        Returns:
            统计数据 JSON（用户数、角色数、部门数等）
        """
        async with get_db_connection():
            user_count = await SystemUser.filter(is_del=False).count()
            active_user_count = await SystemUser.filter(is_del=False, status=1).count()
            role_count = await SystemRole.filter(is_del=False).count()
            dept_count = await SystemDepartment.filter(is_del=False).count()
            permission_count = await SystemPermission.filter(is_del=False).count()
            menu_count = await SystemPermission.filter(is_del=False, menu_type=0).count()
            button_count = await SystemPermission.filter(is_del=False, menu_type=1).count()
            
            return json.dumps({
                "user_count": user_count,
                "active_user_count": active_user_count,
                "role_count": role_count,
                "department_count": dept_count,
                "permission_count": permission_count,
                "menu_count": menu_count,
                "button_count": button_count
            }, ensure_ascii=False)
    
    # ==================== SQL 执行工具 ====================
    
    @mcp.tool()
    async def execute_sql(sql: str, params: Optional[str] = None) -> str:
        """
        执行只读 SQL 查询（仅支持 SELECT）
        
        Args:
            sql: SQL 查询语句（仅支持 SELECT）
            params: JSON 格式的参数列表
        
        Returns:
            查询结果 JSON
        """
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return json.dumps({"error": "仅支持 SELECT 查询"}, ensure_ascii=False)
        
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return json.dumps({"error": f"不允许使用 {keyword} 关键字"}, ensure_ascii=False)
        
        async with get_db_connection():
            conn = Tortoise.get_connection("default")
            
            try:
                if params:
                    param_list = json.loads(params)
                    result = await conn.execute_query(sql, param_list)
                else:
                    result = await conn.execute_query(sql)
                
                return json.dumps({
                    "count": result[0],
                    "data": result[1]
                }, default=str, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
