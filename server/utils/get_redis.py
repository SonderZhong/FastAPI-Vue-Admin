# _*_ coding : UTF-8 _*_

import asyncio
from enum import Enum
from typing import Dict, Optional

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import AuthenticationError, RedisError

from modules import SystemConfig
from utils.config import config, RedisNodeSettings
from utils.log import logger


class RedisKeyConfig(Enum):
    """定义 Redis 键的常量，用于缓存和存储数据。"""

    @property
    def key(self) -> str:
        return self.value.get("key")

    @property
    def remark(self) -> str:
        return self.value.get("remark")

    ACCESS_TOKEN = {"key": "access_token", "remark": "登录令牌信息"}
    USER_INFO = {"key": "user_info", "remark": "用户信息"}
    USER_ROUTES = {"key": "user_routes", "remark": "用户路由信息"}
    CAPTCHA_CODES = {"key": "captcha_codes", "remark": "图片验证码"}
    EMAIL_CODES = {"key": "email_codes", "remark": "邮箱验证码"}
    SYSTEM_CONFIG = {"key": "system_config", "remark": "系统配置信息"}
    SYSTEMDICTIONARY_INFO = {"key": "system_dictionary_info", "remark": "数据字典信息"}
    SYSTEMDICTIONARYITEM_INFO = {"key": "system_dictionary_item_info", "remark": "数据字典项信息"}


class RedisUtil:
    """
    Redis 工具类（支持多实例）
    默认别名 "system" 为主缓存实例
    """

    _connections: Dict[str, any] = {}

    @classmethod
    async def create_redis_connection(cls, alias: str = "system"):
        """创建指定别名的 Redis 连接"""
        redis_cfg = config.redis().get_node(alias)
        logger.debug(f"获取Redis配置（别名: {alias}）...")

        if redis_cfg.mode == "memory":
            logger.info(f"使用内存模拟Redis模式（别名: {alias}）")
            from utils.memory_redis import MemoryRedis
            conn = MemoryRedis()
            cls._connections[alias] = conn
            return conn

        conn_params = {
            "decode_responses": True,
            "socket_timeout": redis_cfg.socket_timeout,
            "retry_on_timeout": redis_cfg.retry_on_timeout,
            "max_connections": redis_cfg.max_connections,
        }

        if redis_cfg.password and str(redis_cfg.password.get_secret_value()).strip():
            conn_params["password"] = str(redis_cfg.password.get_secret_value()).strip()

        try:
            logger.info(f"开始初始化Redis连接（别名: {alias}）...")
            conn = AsyncRedis.from_url(
                f"redis://{redis_cfg.host}:{redis_cfg.port}",
                db=redis_cfg.database,
                **conn_params,
            )
            await conn.ping()
            logger.info(f"Redis连接成功（别名: {alias}, {redis_cfg.host}:{redis_cfg.port}）")
            cls._connections[alias] = conn
            return conn

        except AuthenticationError as e:
            logger.error(f"Redis认证失败（别名: {alias}）: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Redis连接超时（别名: {alias}, {redis_cfg.host}:{redis_cfg.port}）")
            raise
        except ConnectionRefusedError:
            logger.error(f"Redis连接被拒绝（别名: {alias}, {redis_cfg.host}:{redis_cfg.port}）")
            raise
        except RedisError as e:
            logger.error(f"Redis连接失败（别名: {alias}）: {e}")
            raise

    @classmethod
    async def create_all_connections(cls) -> Dict[str, any]:
        """创建所有配置的 Redis 连接"""
        connections = {}
        for node in config.redis().get_all_nodes():
            conn = await cls.create_redis_connection(node.alias)
            connections[node.alias] = conn
        return connections

    @classmethod
    def get_connection(cls, alias: str = "system"):
        """获取指定别名的 Redis 连接"""
        if alias not in cls._connections:
            raise ValueError(f"Redis连接 '{alias}' 未初始化")
        return cls._connections[alias]

    @classmethod
    async def close_redis_connection(cls, conn):
        """关闭 Redis 连接"""
        try:
            if hasattr(conn, '__class__') and conn.__class__.__name__ == 'MemoryRedis':
                logger.info("内存Redis模式，无需关闭连接")
                return
            await conn.aclose()
            logger.info("Redis连接已关闭")
        except RedisError as e:
            logger.warning(f"关闭Redis连接时发生错误: {e}")

    @classmethod
    async def close_all_connections(cls):
        """关闭所有 Redis 连接"""
        for alias, conn in cls._connections.items():
            try:
                if hasattr(conn, '__class__') and conn.__class__.__name__ == 'MemoryRedis':
                    continue
                await conn.aclose()
                logger.info(f"Redis连接已关闭（别名: {alias}）")
            except RedisError as e:
                logger.warning(f"关闭Redis连接失败（别名: {alias}）: {e}")
        cls._connections.clear()

    @classmethod
    def _get_config_key(cls, key: str) -> str:
        return f"{RedisKeyConfig.SYSTEM_CONFIG.key}:{key}"

    @classmethod
    async def init_system_config(cls, conn):
        """初始化系统配置到 Redis"""
        try:
            configs = await SystemConfig.filter(is_del=False).values("key", "value")
            if not configs:
                logger.warning("未查询到系统配置数据，跳过Redis初始化")
                return

            existing_keys = [cls._get_config_key(item['key']) for item in configs]
            if existing_keys:
                try:
                    await conn.delete(*existing_keys)
                except (RedisError, Exception):
                    pass

            if hasattr(conn, '__class__') and conn.__class__.__name__ == 'MemoryRedis':
                for item in configs:
                    redis_key = cls._get_config_key(item['key'])
                    await conn.set(redis_key, item["value"])
            else:
                async with conn.pipeline() as pipe:
                    for item in configs:
                        redis_key = cls._get_config_key(item['key'])
                        await pipe.set(redis_key, item["value"])
                    await pipe.execute()

            logger.info(f"系统配置已同步到Redis（共{len(configs)}条）")
        except (RedisError, Exception) as e:
            logger.error(f"初始化系统配置到Redis失败: {e}")
            raise

    @classmethod
    async def get_system_config(cls, conn, key: str) -> str:
        try:
            redis_key = cls._get_config_key(key)
            value = await conn.get(redis_key)
            if isinstance(value, bytes):
                return value.decode('utf-8')
            return value or ""
        except (RedisError, Exception) as e:
            logger.error(f"获取系统配置失败 key={key}: {e}")
            return ""

    @classmethod
    async def set_system_config(cls, conn, key: str, value: str) -> bool:
        try:
            redis_key = cls._get_config_key(key)
            await conn.set(redis_key, value)
            logger.info(f"系统配置已更新 key={redis_key}")
            return True
        except (RedisError, Exception) as e:
            logger.error(f"设置系统配置失败 key={key}: {e}")
            return False
