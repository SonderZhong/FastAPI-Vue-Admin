# _*_ coding : UTF-8 _*_
# @Time : 2025/01/02
# @Author : sonder
# @File : setup_app.py
# @Comment : 系统初始化应用

import secrets
import hashlib
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = Path(__file__).parent / "templates"
DATA_DIR = Path(__file__).parent / "data"
CONFIG_PATH = BASE_DIR / "config.yaml"


class DatabaseConfig(BaseModel):
    """数据库配置"""
    engine: str = "sqlite"
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    database: str = "fva.db"


class RedisConfig(BaseModel):
    """Redis配置"""
    mode: str = "memory"
    host: str = "127.0.0.1"
    port: int = 6379
    password: str = ""
    database: int = 1


class JwtConfig(BaseModel):
    """JWT配置"""
    secret_key: str = ""
    salt: str = "fastapi-vue-admin"
    expire_minutes: int = 1440


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "FastAPI-Vue-Admin"
    host: str = "0.0.0.0"
    port: int = 9090
    env: str = "dev"


class AdminConfig(BaseModel):
    """管理员配置"""
    username: str = "admin"
    password: str = "admin123@*"
    nickname: str = "超级管理员"
    email: str = "admin@example.com"


class SetupConfig(BaseModel):
    """完整初始化配置"""
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    jwt: JwtConfig = JwtConfig()
    admin: AdminConfig = AdminConfig()


# 创建初始化应用
setup_app = FastAPI(
    title="系统初始化",
    description="系统初始化配置向导",
    docs_url=None,
    redoc_url=None,
)


def get_setup_html() -> str:
    """获取初始化页面HTML"""
    html_path = TEMPLATE_DIR / "setup.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>初始化页面模板不存在</h1>"


@setup_app.get("/", response_class=HTMLResponse)
async def setup_page():
    """初始化页面"""
    return get_setup_html()


@setup_app.post("/api/setup/test-database")
async def test_database(config: DatabaseConfig):
    """测试数据库连接"""
    try:
        if config.engine == "sqlite":
            # SQLite 不需要测试连接，只需确保可以创建文件
            import aiosqlite
            import os
            db_path = config.database if config.database else "fva.db"
            # 测试是否可以创建/打开数据库文件
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("SELECT 1")
            return {"success": True, "msg": "SQLite 数据库就绪"}
        elif config.engine == "mysql":
            import aiomysql
            conn = await aiomysql.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                connect_timeout=5
            )
            # 尝试创建数据库（如果不存在）
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{config.database}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            await conn.ensure_closed()
        elif config.engine == "postgresql":
            import asyncpg
            # PostgreSQL 需要先连接默认数据库
            conn = await asyncpg.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database="postgres",
                timeout=10
            )
            # 检查数据库是否存在
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                config.database
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{config.database}"')
            await conn.close()
        return {"success": True, "msg": "数据库连接成功，数据库已就绪"}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {"success": False, "msg": f"连接失败: {type(e).__name__}: {str(e) or repr(e)}", "detail": error_detail}


@setup_app.post("/api/setup/test-redis")
async def test_redis(config: RedisConfig):
    """测试Redis连接"""
    try:
        # 内存模式无需测试
        if config.mode == "memory":
            return {"success": True, "msg": "内存模式无需测试连接"}
        
        # 服务器模式测试连接
        import redis.asyncio as aioredis
        r = aioredis.Redis(
            host=config.host,
            port=config.port,
            password=config.password or None,
            db=config.database,
            socket_timeout=5
        )
        await r.ping()
        await r.aclose()
        return {"success": True, "msg": "Redis连接成功"}
    except Exception as e:
        return {"success": False, "msg": f"连接失败: {str(e)}"}


def hash_password(password: str, salt: str) -> str:
    """密码加密"""
    password_with_salt = (salt + password).encode('utf-8')
    return hashlib.sha256(password_with_salt).hexdigest()


async def init_database_tables(db_config: DatabaseConfig):
    """初始化数据库表结构"""
    from tortoise import Tortoise
    
    # 根据数据库类型构建连接 URL
    if db_config.engine == "sqlite":
        db_path = db_config.database if db_config.database else "fva.db"
        db_url = f"sqlite://{db_path}"
    elif db_config.engine == "mysql":
        # 先确保数据库存在
        import aiomysql
        conn = await aiomysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            connect_timeout=10
        )
        async with conn.cursor() as cursor:
            # 检查数据库是否存在
            await cursor.execute(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (db_config.database,)
            )
            db_exists = await cursor.fetchone()
            
            if not db_exists:
                # 数据库不存在，创建新数据库
                await cursor.execute(
                    f"CREATE DATABASE `{db_config.database}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        await conn.ensure_closed()
        
        db_url = (
            f"mysql://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    else:  # postgresql
        import asyncpg
        conn = await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            database="postgres",
            timeout=10
        )
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_config.database
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_config.database}"')
        await conn.close()
        
        db_url = (
            f"postgres://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    
    await Tortoise.init(
        db_url=db_url,
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
        ]},
        use_tz=False,
        timezone="Asia/Shanghai"
    )
    
    # 获取数据库连接，删除已存在的表后重建
    conn = Tortoise.get_connection("default")
    
    # 需要删除的表列表（按依赖顺序，先删除有外键依赖的表）
    tables_to_drop = [
        "system_user_role",
        "user_notification",
        "system_login_log",
        "system_operation_log",
        "system_user", 
        "system_role",
        "system_department",
        "system_permission",
        "system_config",
        "system_notification",
        "system_file",
        "casbin_rule",
    ]
    
    # 禁用外键检查（MySQL）
    try:
        await conn.execute_query("SET FOREIGN_KEY_CHECKS = 0")
    except Exception:
        pass
    
    for table in tables_to_drop:
        try:
            await conn.execute_query(f"DROP TABLE IF EXISTS `{table}`")
        except Exception:
            pass  # 表不存在则忽略
    
    # 重新启用外键检查
    try:
        await conn.execute_query("SET FOREIGN_KEY_CHECKS = 1")
    except Exception:
        pass
    
    # 重新生成表结构
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()


async def init_admin_and_data(db_config: DatabaseConfig, admin_config: AdminConfig, jwt_salt: str):
    """初始化管理员账号和基础数据 - 从 JSON 文件批量导入"""
    from tortoise import Tortoise
    from datetime import datetime
    import json
    
    # 当前时间，用于所有导入数据
    now = datetime.now()
    
    # 根据数据库类型构建连接 URL
    if db_config.engine == "sqlite":
        db_path = db_config.database if db_config.database else "fva.db"
        db_url = f"sqlite://{db_path}"
    elif db_config.engine == "mysql":
        db_url = (
            f"mysql://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    else:  # postgresql
        db_url = (
            f"postgres://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    
    await Tortoise.init(
        db_url=db_url,
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
        ]},
        use_tz=False,
        timezone="Asia/Shanghai"
    )
    
    from models import SystemUser, SystemDepartment, SystemRole, SystemPermission
    from models.user import SystemUserRole
    from models.casbin import CasbinRule
    
    # 1. 导入部门数据
    dept_file = DATA_DIR / "system_department.json"
    if dept_file.exists():
        departments = json.loads(dept_file.read_text(encoding="utf-8"))
        for dept in departments:
            await SystemDepartment.create(
                id=dept["id"],
                name=dept["name"],
                parent_id=dept.get("parent_id"),
                sort=dept.get("sort", 0),
                phone=dept.get("phone"),
                principal=dept.get("principal"),
                email=dept.get("email"),
                status=dept.get("status", 1),
                remark=dept.get("remark"),
                created_at=now,
                updated_at=now
            )
    
    # 2. 导入角色数据
    role_file = DATA_DIR / "system_role.json"
    if role_file.exists():
        roles = json.loads(role_file.read_text(encoding="utf-8"))
        for role in roles:
            await SystemRole.create(
                id=role["id"],
                name=role.get("role_name", role.get("name")),
                code=role.get("role_code", role.get("code")),
                description=role.get("role_description", role.get("description")),
                status=role.get("status", 1),
                department_id=role.get("department_id"),
                created_at=now,
                updated_at=now
            )
    
    # 3. 导入权限数据
    perm_file = DATA_DIR / "system_permission.json"
    if perm_file.exists():
        permissions = json.loads(perm_file.read_text(encoding="utf-8"))
        for perm in permissions:
            await SystemPermission.create(
                id=perm["id"],
                menu_type=perm.get("menu_type", 0),
                parent_id=perm.get("parent_id"),
                name=perm.get("name"),
                path=perm.get("path"),
                component=perm.get("component"),
                title=perm.get("title"),
                icon=perm.get("icon"),
                order=perm.get("order", 0),
                authTitle=perm.get("authTitle"),
                authMark=perm.get("authMark"),
                api_path=perm.get("api_path"),
                api_method=perm.get("api_method"),
                min_user_type=perm.get("min_user_type", 3),
                isHide=perm.get("isHide", 0),
                isHideTab=perm.get("isHideTab"),
                isIframe=perm.get("isIframe"),
                link=perm.get("link"),
                keepAlive=perm.get("keepAlive"),
                isFirstLevel=perm.get("isFirstLevel"),
                fixedTab=perm.get("fixedTab"),
                activePath=perm.get("activePath"),
                isFullPage=perm.get("isFullPage"),
                showBadge=perm.get("showBadge", 0),
                showTextBadge=perm.get("showTextBadge"),
                data_scope=perm.get("data_scope", 4),
                remark=perm.get("remark"),
                created_at=now,
                updated_at=now
            )
    
    # 4. 创建管理员账号（使用用户配置的密码重新计算）
    hashed_pwd = hash_password(admin_config.password, jwt_salt)
    dept = await SystemDepartment.get_or_none(name="系统管理", is_del=False)
    admin = await SystemUser.create(
        username=admin_config.username,
        password=hashed_pwd,
        nickname=admin_config.nickname,
        email=admin_config.email,
        user_type=0,  # 超级管理员
        status=1,
        department=dept,
        created_at=now,
        updated_at=now
    )
    
    # 5. 关联管理员角色
    admin_role = await SystemRole.get_or_none(code="admin", is_del=False)
    if admin_role:
        await SystemUserRole.create(
            user=admin, 
            role=admin_role,
            created_at=now,
            updated_at=now
        )
    
    # 6. 导入 Casbin 规则
    casbin_file = DATA_DIR / "casbin_rule.json"
    if casbin_file.exists():
        casbin_rules = json.loads(casbin_file.read_text(encoding="utf-8"))
        for rule in casbin_rules:
            await CasbinRule.create(
                id=rule["id"],
                ptype=rule["ptype"],
                v0=rule.get("v0"),
                v1=rule.get("v1"),
                v2=rule.get("v2"),
                v3=rule.get("v3"),
                v4=rule.get("v4"),
                v5=rule.get("v5"),
                created_at=now,
                updated_at=now
            )
    
    # 7. 添加新管理员用户到 Casbin（用户ID -> 角色代码）
    if admin_role:
        await CasbinRule.create(
            ptype="g",
            v0=str(admin.id),
            v1=admin_role.code,
            created_at=now,
            updated_at=now
        )
    
    await Tortoise.close_connections()


@setup_app.post("/api/setup/initialize")
async def initialize_system(config: SetupConfig):
    """初始化系统配置"""
    try:
        # 生成 JWT 密钥
        jwt_secret = config.jwt.secret_key or secrets.token_hex(32)
        jwt_salt = config.jwt.salt or "digital-research-system"
        
        # 1. 生成配置文件
        config_content = f"""# 应用基础配置
# 此文件由系统初始化向导自动生成
# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 已初始化标记
initialized: true

app:
  name: "{config.app.name}"
  version: "1.0.7"
  host: "{config.app.host}"
  port: {config.app.port}
  env: "{config.app.env}"
  api_prefix: "/api"
  reload: {str(config.app.env == 'dev').lower()}
  api_status_enabled: {str(config.app.env != 'prod').lower()}

jwt:
  algorithm: "HS256"
  secret_key: "{jwt_secret}"
  salt: "{jwt_salt}"
  expire_minutes: {config.jwt.expire_minutes}
  redis_expire_minutes: 30

database:
  engine: "{config.database.engine}"
  host: "{config.database.host}"
  port: {config.database.port}
  username: "{config.database.username}"
  password: "{config.database.password}"
  database: "{config.database.database}"
  pool_size: 10
  pool_timeout: 30
  echo: false
  timezone: "Asia/Shanghai"
  charset: "utf8mb4"

redis:
  mode: "{config.redis.mode}"
  host: "{config.redis.host}"
  port: {config.redis.port}
  password: "{config.redis.password}"
  database: {config.redis.database}
  max_connections: 10
  socket_timeout: 5
  retry_on_timeout: true
"""
        
        # 写入配置文件
        CONFIG_PATH.write_text(config_content, encoding="utf-8")
        
        # 2. 初始化数据库表结构
        await init_database_tables(config.database)
        
        # 3. 初始化管理员和基础数据
        await init_admin_and_data(config.database, config.admin, jwt_salt)
        
        return {
            "success": True,
            "msg": "系统初始化完成！请重启应用以生效",
            "data": {
                "admin_username": config.admin.username,
                "app_port": config.app.port
            }
        }
    except Exception as e:
        import traceback
        return {"success": False, "msg": f"初始化失败: {str(e)}\n{traceback.format_exc()}"}


@setup_app.get("/api/setup/status")
async def get_setup_status():
    """获取初始化状态"""
    initialized = False
    if CONFIG_PATH.exists() and CONFIG_PATH.is_file():
        try:
            import yaml
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            initialized = config.get('initialized', False) is True
        except Exception:
            pass
    
    return {
        "initialized": initialized,
        "config_path": str(CONFIG_PATH)
    }


def run_setup_server(host: str = "0.0.0.0", port: int = 9090):
    """运行初始化服务器"""
    print("\n" + "=" * 60)
    print("  🚀 系统初始化向导")
    print("=" * 60)
    print("\n  检测到系统尚未初始化，请访问以下地址完成配置：")
    print(f"\n  ➜  http://localhost:{port}")
    print(f"  ➜  http://127.0.0.1:{port}")
    print("\n" + "=" * 60 + "\n")
    
    uvicorn.run(
        setup_app,
        host=host,
        port=port,
        log_level="warning"
    )


if __name__ == "__main__":
    run_setup_server()
