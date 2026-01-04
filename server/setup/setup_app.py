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
    engine: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    username: str = "root"
    password: str = ""
    database: str = "digital-management"


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "127.0.0.1"
    port: int = 6379
    password: str = ""
    database: int = 1


class JwtConfig(BaseModel):
    """JWT配置"""
    secret_key: str = ""
    salt: str = "digital-research-system"
    expire_minutes: int = 1440


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "数字教科研平台"
    host: str = "0.0.0.0"
    port: int = 9090
    env: str = "dev"


class AdminConfig(BaseModel):
    """管理员配置"""
    username: str = "admin"
    password: str = "admin123"
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
        if config.engine == "mysql":
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
                timeout=5
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
        return {"success": False, "msg": f"连接失败: {str(e)}"}


@setup_app.post("/api/setup/test-redis")
async def test_redis(config: RedisConfig):
    """测试Redis连接"""
    try:
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
    
    # 先确保数据库存在
    if db_config.engine == "mysql":
        import aiomysql
        conn = await aiomysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            connect_timeout=10
        )
        async with conn.cursor() as cursor:
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_config.database}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        await conn.ensure_closed()
        
        db_url = (
            f"mysql://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    else:
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
        ]}
    )
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()


async def init_admin_and_data(db_config: DatabaseConfig, admin_config: AdminConfig, jwt_salt: str):
    """初始化管理员账号和基础数据"""
    from tortoise import Tortoise
    
    if db_config.engine == "mysql":
        db_url = (
            f"mysql://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    else:
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
        ]}
    )
    
    from models import SystemUser, SystemDepartment, SystemRole
    from models.user import SystemUserRole
    
    # 1. 从JSON初始化部门数据
    await init_departments()
    
    # 2. 从JSON初始化角色数据
    await init_roles()
    
    # 3. 获取管理员角色（从JSON数据中获取）
    role = await SystemRole.get_or_none(code="admin", is_del=False)
    if not role:
        # 如果没有找到admin角色，创建一个默认的
        dept = await SystemDepartment.get_or_none(name="系统管理", is_del=False)
        role = await SystemRole.create(
            code="admin",
            name="系统管理员",
            description="系统管理员，拥有系统所有权限",
            status=1,
            department=dept
        )
    
    # 4. 创建管理员账号
    admin = await SystemUser.get_or_none(username=admin_config.username, is_del=False)
    if not admin:
        hashed_pwd = hash_password(admin_config.password, jwt_salt)
        # 获取系统管理部门
        dept = await SystemDepartment.get_or_none(name="系统管理", is_del=False)
        admin = await SystemUser.create(
            username=admin_config.username,
            password=hashed_pwd,
            nickname=admin_config.nickname,
            email=admin_config.email,
            user_type=0,  # 超级管理员
            status=1,
            department=dept
        )
        # 关联角色
        await SystemUserRole.create(user=admin, role=role)
    
    # 5. 初始化基础权限菜单
    await init_permissions()
    
    # 6. 初始化 Casbin 规则
    await init_casbin_rules()
    
    await Tortoise.close_connections()


def load_permissions_data() -> dict:
    """从 JSON 文件加载权限数据"""
    json_path = DATA_DIR / "permissions.json"
    if json_path.exists():
        import json
        return json.loads(json_path.read_text(encoding="utf-8"))
    return {"menus": [], "buttons": [], "roles": [], "departments": [], "casbin_rules": []}


async def init_casbin_rules():
    """从 JSON 文件初始化 Casbin 规则"""
    from models.casbin import CasbinRule
    
    # 检查是否已有规则
    count = await CasbinRule.filter(is_del=False).count()
    if count > 0:
        return
    
    data = load_permissions_data()
    for rule in data.get("casbin_rules", []):
        await CasbinRule.create(**rule)


async def init_departments():
    """从 JSON 文件初始化部门数据"""
    from models import SystemDepartment
    
    # 检查是否已有部门数据
    count = await SystemDepartment.filter(is_del=False).count()
    if count > 0:
        return
    
    data = load_permissions_data()
    for dept in data.get("departments", []):
        await SystemDepartment.create(**dept)


async def init_roles():
    """从 JSON 文件初始化角色数据"""
    from models import SystemRole, SystemDepartment
    
    # 检查是否已有角色数据
    count = await SystemRole.filter(is_del=False).count()
    if count > 0:
        return
    
    data = load_permissions_data()
    for role in data.get("roles", []):
        role_data = {**role}
        
        # 处理部门关联
        dept_id = role_data.pop("department_id", None)
        if dept_id:
            dept = await SystemDepartment.get_or_none(id=dept_id, is_del=False)
            if dept:
                role_data["department"] = dept
        
        await SystemRole.create(**role_data)


async def init_permissions():
    """从 JSON 文件初始化权限配置"""
    from models import SystemPermission
    
    # 检查是否已有权限数据
    count = await SystemPermission.filter(is_del=False).count()
    if count > 0:
        return
    
    import json
    
    data = load_permissions_data()
    
    # 1. 创建菜单权限（使用JSON中的真实ID）
    for menu in data.get("menus", []):
        menu_data = {**menu}
        # 确保必要字段存在
        if "component" not in menu_data:
            menu_data["component"] = None
        await SystemPermission.create(**menu_data)
    
    # 2. 创建按钮权限（使用JSON中的真实ID）
    for btn in data.get("buttons", []):
        btn_data = {**btn}
        # 确保必要字段存在
        if "component" not in btn_data:
            btn_data["component"] = None
        if "path" not in btn_data:
            btn_data["path"] = None
        # api_method 字段已经是数组格式，JSONField会自动处理
        await SystemPermission.create(**btn_data)


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

app:
  name: "{config.app.name}"
  version: "1.0.0"
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
            "msg": "系统初始化完成！配置已保存，数据库已初始化，管理员账号已创建。",
            "data": {
                "admin_username": config.admin.username,
                "app_port": config.app.port
            }
        }
    except Exception as e:
        # 如果失败，删除配置文件
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
        import traceback
        return {"success": False, "msg": f"初始化失败: {str(e)}\n{traceback.format_exc()}"}


@setup_app.get("/api/setup/status")
async def get_setup_status():
    """获取初始化状态"""
    return {
        "initialized": CONFIG_PATH.exists(),
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
