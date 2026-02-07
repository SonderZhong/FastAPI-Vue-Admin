# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 22:38
# @UpdateTime : 2025/08/03 22:38
# @Author : sonder
# @File : database.py
# @Software : PyCharm
# @Comment : 本程序
import logging
from typing import Dict, Any

from tortoise import Tortoise

from utils.config import config  # 导入统一配置实例
from utils.log import logger  # 日志工具


def _build_db_connection(db_config) -> Dict[str, Dict[str, Any]]:
    """构建数据库连接配置"""
    engine_map = {
        "mysql": "tortoise.backends.mysql",
        "postgresql": "tortoise.backends.asyncpg",
        "sqlite": "tortoise.backends.sqlite"
    }

    conn_config = {
        "engine": engine_map.get(db_config.engine, "tortoise.backends.mysql"),
        "credentials": {
            "host": db_config.host,
            "port": db_config.port,
            "user": db_config.username,
            "password": db_config.password.get_secret_value() if db_config.password else None,
            "database": db_config.database,
        }
    }

    # MySQL 特定配置
    if db_config.engine == "mysql":
        conn_config["credentials"]["charset"] = getattr(db_config, 'charset', 'utf8mb4')
        conn_config["credentials"]["init_command"] = "SET time_zone = '+08:00'"
        conn_config["credentials"]["connect_timeout"] = 10

    # PostgreSQL 特定配置
    elif db_config.engine == "postgresql":
        conn_config["credentials"]["ssl"] = False
        conn_config["credentials"]["timeout"] = 10 
        conn_config["credentials"]["server_settings"] = {"client_encoding": "utf8"}
    elif db_config.engine == "sqlite":
        conn_config["credentials"].pop("host", None)
        conn_config["credentials"].pop("port", None)

    return {"default": conn_config}


def _build_db_apps() -> Dict[str, Dict[str, Any]]:
    """构建应用映射配置
    
    注意：
        - models 统一指向 "models" 包，Tortoise 会自动扫描其中的所有模型
        - 时区配置在全局 tortoise_config 中设置
        - app名称必须与模型Meta中的app一致
    """
    return {
        "system": {
            "models": ["models"],
            "default_connection": "default"
        }
    }


def _configure_db_logging(enable: bool, log_level: str = "INFO"):
    """
    配置数据库日志

    :param enable: 是否启用SQL日志
    :param log_level: 日志级别
    """
    # 获取Tortoise的核心日志器
    tortoise_logger = logging.getLogger("tortoise")
    db_client_logger = logging.getLogger("tortoise.db_client")

    if enable:
        # 启用日志
        tortoise_logger.setLevel(getattr(logging, log_level))
        db_client_logger.setLevel(getattr(logging, log_level))

        # 如果没有处理器，添加一个控制台处理器（可根据需要修改）
        if not tortoise_logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            tortoise_logger.addHandler(console_handler)
            db_client_logger.addHandler(console_handler)
    else:
        # 禁用日志
        tortoise_logger.setLevel(logging.WARNING)
        db_client_logger.setLevel(logging.WARNING)


async def init_db():
    """异步初始化数据库连接"""
    try:
        db_config = config.database()

        # 构建Tortoise配置
        tortoise_config = {
            "connections": _build_db_connection(db_config),
            "apps": _build_db_apps(),
            "use_tz": False,
            "timezone": db_config.timezone
        }

        # 初始化Tortoise ORM
        logger.info(f"开始初始化数据库连接（{db_config.engine}://{db_config.host}:{db_config.port}/{db_config.database}）")
        await Tortoise.init(config=tortoise_config)

        # 配置SQL日志
        if db_config.echo:
            logger.info("SQL查询日志已启用")
            _configure_db_logging(enable=True, log_level="INFO")
        else:
            logger.info("SQL查询日志已禁用")
            _configure_db_logging(enable=False)

        # 生成表结构
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
