# _*_ coding : UTF-8 _*_
import json
import secrets
import sys
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
DATA_DIR = Path(__file__).resolve().parent / "data"
CONFIG_PATH = BASE_DIR / "config.yaml"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class DatabaseConfig(BaseModel):
    engine: str = "sqlite"
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    database: str = "fva.db"


class RedisConfig(BaseModel):
    mode: str = "memory"
    host: str = "127.0.0.1"
    port: int = 6379
    password: str = ""
    database: int = 1


class JwtConfig(BaseModel):
    secret_key: str = ""
    salt: str = "fastapi-vue-admin"
    expire_minutes: int = 1440


class AppConfig(BaseModel):
    name: str = "FastAPI-Vue-Admin"
    host: str = "0.0.0.0"
    port: int = 9090
    env: str = "dev"
    permission_verify_enabled: bool = False


class AdminConfig(BaseModel):
    username: str = "admin"
    password: str = "admin123@*"
    nickname: str = "Super Admin"
    email: str = "admin@example.com"


class SetupConfig(BaseModel):
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    jwt: JwtConfig = JwtConfig()
    admin: AdminConfig = AdminConfig()


setup_app = FastAPI(
    title="System Setup",
    description="FastAPI-Vue-Admin setup service",
    docs_url=None,
    redoc_url=None,
)


def get_setup_html() -> str:
    html_path = TEMPLATE_DIR / "setup.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>setup.html not found</h1>"


def build_db_url(db_config: DatabaseConfig) -> str:
    if db_config.engine == "sqlite":
        db_path = db_config.database or "fva.db"
        return f"sqlite://{db_path}"
    if db_config.engine == "mysql":
        return (
            f"mysql://{db_config.username}:{db_config.password}@"
            f"{db_config.host}:{db_config.port}/{db_config.database}"
        )
    return (
        f"postgres://{db_config.username}:{db_config.password}@"
        f"{db_config.host}:{db_config.port}/{db_config.database}"
    )


def tortoise_config(db_url: str) -> dict:
    return {
        "connections": {"system": db_url},
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
    }


def read_seed_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_status(value, default: int = 1) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_ancestor_path(old_id: str, department_map: dict[str, int], old_parent_id: str | None) -> str:
    if not old_parent_id:
        return "/"
    parent_new_id = department_map.get(str(old_parent_id))
    if not parent_new_id:
        return "/"
    return f"/{parent_new_id}/"


async def create_database_if_needed(db_config: DatabaseConfig):
    if db_config.engine == "sqlite":
        import aiosqlite

        async with aiosqlite.connect(db_config.database or "fva.db") as conn:
            await conn.execute("SELECT 1")
        return

    if db_config.engine == "mysql":
        import aiomysql

        conn = await aiomysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            connect_timeout=10,
        )
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (db_config.database,),
            )
            exists = await cursor.fetchone()
            if not exists:
                await cursor.execute(
                    f"CREATE DATABASE `{db_config.database}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        await conn.ensure_closed()
        return

    import asyncpg

    conn = await asyncpg.connect(
        host=db_config.host,
        port=db_config.port,
        user=db_config.username,
        password=db_config.password,
        database="postgres",
        timeout=10,
    )
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1",
        db_config.database,
    )
    if not exists:
        await conn.execute(f'CREATE DATABASE "{db_config.database}"')
    await conn.close()


async def drop_existing_tables(conn, engine: str):
    tables_to_drop = [
        "user_notification",
        "system_login_log",
        "system_operation_log",
        "system_role_department",
        "system_role_permission",
        "system_user_role",
        "system_tenant_user",
        "system_notification",
        "system_file",
        "system_config",
        "system_dictionary_item",
        "system_dictionary",
        "system_role",
        "system_permission",
        "system_department",
        "system_user",
        "system_tenant",
    ]

    if engine == "mysql":
        try:
            await conn.execute_query("SET FOREIGN_KEY_CHECKS = 0")
        except Exception:
            pass

    for table in tables_to_drop:
        sql = f"DROP TABLE IF EXISTS `{table}`" if engine == "mysql" else f'DROP TABLE IF EXISTS "{table}"'
        try:
            await conn.execute_query(sql)
        except Exception:
            pass

    if engine == "mysql":
        try:
            await conn.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        except Exception:
            pass


async def init_database_tables(db_config: DatabaseConfig):
    from tortoise import Tortoise

    await create_database_if_needed(db_config)
    db_url = build_db_url(db_config)

    await Tortoise.init(
        config=tortoise_config(db_url),
        use_tz=False,
        timezone="Asia/Shanghai",
    )
    conn = Tortoise.get_connection("system")
    await drop_existing_tables(conn, db_config.engine)
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()


async def seed_system_configs(SystemConfig, default_department_id: str, default_role_id: str, default_tenant_id: str):
    from modules.config.model import ConfigGroup
    from utils.dynamic_config import DynamicConfigService

    for cfg in DynamicConfigService.DEFAULT_CONFIGS:
        await SystemConfig.create(
            name=cfg["name"],
            key=cfg["key"],
            value=cfg["value"],
            group=cfg["group"],
            type=cfg["type"],
            remark=cfg.get("remark", ""),
        )

    await SystemConfig.create(
        name="Default Tenant",
        key="default_tenant_id",
        value=default_tenant_id,
        group=ConfigGroup.ACCOUNT,
        type=True,
        remark="Default tenant id for new users",
    )
    await SystemConfig.filter(key="default_department_id", is_del=False).update(
        value=default_department_id
    )
    await SystemConfig.filter(key="default_role_id", is_del=False).update(
        value=default_role_id
    )


async def init_admin_and_data(db_config: DatabaseConfig, admin_config: AdminConfig):
    from tortoise import Tortoise

    db_url = build_db_url(db_config)
    await Tortoise.init(
        config=tortoise_config(db_url),
        use_tz=False,
        timezone="Asia/Shanghai",
    )

    from modules import (
        SystemConfig,
        SystemDepartment,
        SystemPermission,
        SystemRole,
        SystemRolePermission,
        SystemTenant,
        SystemTenantUser,
        SystemUser,
        SystemUserRole,
    )
    from utils.password import PasswordUtil

    now = datetime.now()

    default_tenant = await SystemTenant.create(
        name="Default Tenant",
        code="default",
        status=1,
        invite_code=SystemTenant.generate_invite_code(),
        allow_register=True,
        remark="Seed tenant created by setup",
        created_at=now,
        updated_at=now,
    )

    departments = read_seed_json("system_department.json")
    department_map: dict[str, int] = {}
    for dept in departments:
        created = await SystemDepartment.create(
            tenant_id=default_tenant.id,
            name=dept["name"],
            code=dept.get("code"),
            ancestor_path="/",
            parent_id=None,
            sort=dept.get("sort", 0),
            phone=dept.get("phone"),
            principal=dept.get("principal"),
            email=dept.get("email"),
            status=normalize_status(dept.get("status"), 1),
            remark=dept.get("remark"),
            created_at=now,
            updated_at=now,
        )
        department_map[str(dept["id"])] = created.id

    for dept in departments:
        new_id = department_map.get(str(dept["id"]))
        if not new_id:
            continue
        old_parent_id = dept.get("parent_id")
        parent_new_id = department_map.get(str(old_parent_id)) if old_parent_id else None
        ancestor_path = dept.get("ancestor_path")
        if ancestor_path:
            parts = [part for part in str(ancestor_path).strip("/").split("/") if part]
            mapped_parts = [str(department_map[part]) for part in parts if part in department_map]
            normalized_ancestor_path = f"/{'/'.join(mapped_parts)}/" if mapped_parts else "/"
        else:
            normalized_ancestor_path = build_ancestor_path(str(dept["id"]), department_map, old_parent_id)
        await SystemDepartment.filter(id=new_id).update(
            parent_id=str(parent_new_id) if parent_new_id else None,
            ancestor_path=normalized_ancestor_path,
        )

    roles = read_seed_json("system_role.json")
    role_map: dict[str, int] = {}
    admin_role_id = None
    default_role_id = None
    default_department_id = next(iter(department_map.values()), None)
    for role in roles:
        old_department_id = role.get("department_id")
        created = await SystemRole.create(
            tenant_id=default_tenant.id,
            department_id=department_map.get(str(old_department_id)) or default_department_id,
            name=role.get("role_name", role.get("name")),
            code=role.get("role_code", role.get("code")),
            description=role.get("role_description", role.get("description")),
            status=normalize_status(role.get("status"), 1),
            created_at=now,
            updated_at=now,
        )
        role_map[str(role["id"])] = created.id
        if created.code == "admin":
            admin_role_id = created.id
        if created.code == "user":
            default_role_id = created.id

    permissions = read_seed_json("system_permission.json")
    permission_map: dict[str, int] = {}
    for perm in permissions:
        created = await SystemPermission.create(
            menu_type=perm.get("menu_type", 0),
            code=perm.get("code") or perm.get("permission_code") or perm.get("authMark") or perm.get("name"),
            parent_id=None,
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
            updated_at=now,
        )
        permission_map[str(perm["id"])] = created.id

    for perm in permissions:
        new_id = permission_map.get(str(perm["id"]))
        if not new_id:
            continue
        old_parent_id = perm.get("parent_id")
        parent_new_id = permission_map.get(str(old_parent_id)) if old_parent_id else None
        await SystemPermission.filter(id=new_id).update(parent_id=parent_new_id)

    hashed_pwd = await PasswordUtil.get_password_hash(admin_config.password)
    admin_user = await SystemUser.create(
        username=admin_config.username,
        password=hashed_pwd,
        nickname=admin_config.nickname,
        email=admin_config.email,
        status=1,
        created_at=now,
        updated_at=now,
    )

    await SystemTenantUser.create(
        tenant_id=default_tenant.id,
        user_id=admin_user.id,
        department_id=default_department_id,
        user_type=0,
        status=1,
        created_at=now,
        updated_at=now,
    )

    if admin_role_id:
        await SystemUserRole.create(
            tenant_id=default_tenant.id,
            user_id=admin_user.id,
            role_id=admin_role_id,
            created_at=now,
            updated_at=now,
        )
        for permission_id in permission_map.values():
            await SystemRolePermission.create(
                role_id=admin_role_id,
                permission_id=permission_id,
                created_at=now,
                updated_at=now,
            )

    await seed_system_configs(
        SystemConfig,
        default_department_id=str(default_department_id or ""),
        default_role_id=str(default_role_id or admin_role_id or ""),
        default_tenant_id=str(default_tenant.id),
    )

    await Tortoise.close_connections()


@setup_app.get("/", response_class=HTMLResponse)
async def setup_page():
    return get_setup_html()


@setup_app.post("/api/setup/test-database")
async def test_database(config: DatabaseConfig):
    try:
        await create_database_if_needed(config)
        return {"success": True, "msg": "Database connection succeeded"}
    except Exception as exc:
        import traceback

        return {
            "success": False,
            "msg": f"{type(exc).__name__}: {str(exc) or repr(exc)}",
            "detail": traceback.format_exc(),
        }


@setup_app.post("/api/setup/test-redis")
async def test_redis(config: RedisConfig):
    try:
        if config.mode == "memory":
            return {"success": True, "msg": "Memory mode does not require Redis"}

        import redis.asyncio as aioredis

        client = aioredis.Redis(
            host=config.host,
            port=config.port,
            password=config.password or None,
            db=config.database,
            socket_timeout=5,
        )
        await client.ping()
        await client.aclose()
        return {"success": True, "msg": "Redis connection succeeded"}
    except Exception as exc:
        return {"success": False, "msg": f"{type(exc).__name__}: {exc}"}


@setup_app.post("/api/setup/initialize")
async def initialize_system(config: SetupConfig):
    try:
        jwt_secret = config.jwt.secret_key or secrets.token_hex(32)
        jwt_salt = config.jwt.salt or "fastapi-vue-admin"
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        config_content = f"""# Generated by setup service
# Generated at: {now_text}

initialized: true

app:
  name: "{config.app.name}"
  version: "1.0.8"
  host: "{config.app.host}"
  port: {config.app.port}
  env: "{config.app.env}"
  api_prefix: "/api"
  reload: {str(config.app.env == "dev").lower()}
  api_status_enabled: {str(config.app.env != "prod").lower()}
  permission_verify_enabled: {str(config.app.permission_verify_enabled).lower()}

jwt:
  algorithm: "HS256"
  secret_key: "{jwt_secret}"
  salt: "{jwt_salt}"
  expire_minutes: {config.jwt.expire_minutes}
  redis_expire_minutes: 30

database:
  nodes:
    - alias: "system"
      engine: "{config.database.engine}"
      host: "{config.database.host}"
      port: {config.database.port}
      username: "{config.database.username}"
      password: "{config.database.password}"
      database: "{config.database.database}"
      pool_size: 10
      pool_timeout: 30
      echo: false
      charset: "utf8mb4"
      timezone: "Asia/Shanghai"

redis:
  nodes:
    - alias: "system"
      mode: "{config.redis.mode}"
      host: "{config.redis.host}"
      port: {config.redis.port}
      password: "{config.redis.password}"
      database: {config.redis.database}
      max_connections: 10
      socket_timeout: 5
      retry_on_timeout: true
"""

        CONFIG_PATH.write_text(config_content, encoding="utf-8")
        await init_database_tables(config.database)
        await init_admin_and_data(config.database, config.admin)

        return {
            "success": True,
            "msg": "System initialized successfully. Restart the app to apply changes.",
            "data": {
                "admin_username": config.admin.username,
                "app_port": config.app.port,
            },
        }
    except Exception as exc:
        import traceback

        return {
            "success": False,
            "msg": f"Initialization failed: {exc}\n{traceback.format_exc()}",
        }


@setup_app.get("/api/setup/status")
async def get_setup_status():
    initialized = False
    if CONFIG_PATH.exists() and CONFIG_PATH.is_file():
        try:
            import yaml

            with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}
            initialized = config.get("initialized", False) is True
        except Exception:
            initialized = False

    return {"initialized": initialized, "config_path": str(CONFIG_PATH)}


def run_setup_server(host: str = "0.0.0.0", port: int = 9090):
    print("\n" + "=" * 60)
    print("  FastAPI-Vue-Admin Setup")
    print("=" * 60)
    print(f"\n  http://localhost:{port}")
    print(f"  http://127.0.0.1:{port}")
    print("\n" + "=" * 60 + "\n")

    uvicorn.run(setup_app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run_setup_server()
