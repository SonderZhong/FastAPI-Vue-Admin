# _*_ coding : UTF-8 _*_

import logging
from typing import Dict, Any

from tortoise import Tortoise

from utils.config import config, DatabaseNodeSettings
from utils.log import logger


def _build_single_connection(node: DatabaseNodeSettings) -> Dict[str, Any]:
    """构建单个数据库节点的连接配置"""
    engine_map = {
        "mysql": "tortoise.backends.mysql",
        "postgresql": "tortoise.backends.asyncpg",
        "sqlite": "tortoise.backends.sqlite",
    }

    if node.engine == "sqlite":
        db_path = node.database if node.database else "fva.db"
        return {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": db_path},
        }

    credentials = {
        "host": node.host,
        "port": node.port,
        "user": node.username,
        "password": node.password.get_secret_value() if node.password else None,
        "database": node.database,
    }

    if node.engine == "mysql":
        credentials["charset"] = node.charset
        credentials["init_command"] = "SET time_zone = '+08:00'"
        credentials["connect_timeout"] = 10
    elif node.engine == "postgresql":
        credentials["ssl"] = False
        credentials["timeout"] = 10
        credentials["server_settings"] = {"client_encoding": "utf8"}

    return {
        "engine": engine_map.get(node.engine, "tortoise.backends.mysql"),
        "credentials": credentials,
    }


def _build_db_connections() -> Dict[str, Dict[str, Any]]:
    """构建所有数据库连接配置"""
    connections = {}
    for node in config.database().get_all_nodes():
        connections[node.alias] = _build_single_connection(node)
    return connections


def _build_db_apps() -> Dict[str, Dict[str, Any]]:
    """构建应用映射配置"""
    return {
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
    }


def _configure_db_logging(enable: bool, log_level: str = "INFO"):
    tortoise_logger = logging.getLogger("tortoise")
    db_client_logger = logging.getLogger("tortoise.db_client")

    if enable:
        tortoise_logger.setLevel(getattr(logging, log_level))
        db_client_logger.setLevel(getattr(logging, log_level))
        if not tortoise_logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            tortoise_logger.addHandler(console_handler)
            db_client_logger.addHandler(console_handler)
    else:
        tortoise_logger.setLevel(logging.WARNING)
        db_client_logger.setLevel(logging.WARNING)


async def init_db():
    """异步初始化数据库连接（支持多数据源）"""
    try:
        connections = _build_db_connections()
        default_node = config.database().get_node("system")

        tortoise_config = {
            "connections": connections,
            "apps": _build_db_apps(),
            "use_tz": False,
            "timezone": default_node.timezone,
        }

        if default_node.engine == "sqlite":
            logger.info(f"开始初始化数据库连接（{default_node.engine}://{default_node.database}）")
        else:
            logger.info(f"开始初始化数据库连接（{default_node.engine}://{default_node.host}:{default_node.port}/{default_node.database}）")

        logger.info(f"已配置 {len(connections)} 个数据库节点: {list(connections.keys())}")
        await Tortoise.init(config=tortoise_config)

        if default_node.echo:
            logger.info("SQL查询日志已启用")
            _configure_db_logging(enable=True, log_level="INFO")
        else:
            logger.info("SQL查询日志已禁用")
            _configure_db_logging(enable=False)

        logger.info("开始生成数据库表结构...")
        await Tortoise.generate_schemas()
        logger.success("数据库连接初始化成功")
        return tortoise_config

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"数据库初始化失败: {error_msg}", exc_info=True)
        raise


async def close_db():
    """关闭所有数据库连接"""
    try:
        await Tortoise.close_connections()
        logger.success("所有数据库连接已关闭")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"关闭数据库连接失败: {error_msg}", exc_info=True)
