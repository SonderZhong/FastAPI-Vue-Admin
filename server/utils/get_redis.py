# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 22:29
# @UpdateTime : 2025/08/04 00:00
# @Author : sonder
# @File : redis.py
# @Software : PyCharm
# @Comment : Redis工具类（基于 redis-py 5.x，兼容 Python 3.11+）

import asyncio
from enum import Enum

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import (
    AuthenticationError,
    RedisError,
)

from models import SystemConfig
from utils.config import config
from utils.log import logger


class RedisKeyConfig(Enum):
    """
    定义 Redis 键的常量，用于缓存和存储数据。
    """

    @property
    def key(self) -> str:
        """获取 Redis 键名"""
        return self.value.get("key")

    @property
    def remark(self) -> str:
        """获取键名备注信息"""
        return self.value.get("remark")

    ACCESS_TOKEN = {"key": "access_token", "remark": "登录令牌信息"}
    USER_INFO = {"key": "user_info", "remark": "用户信息"}
    USER_ROUTES = {"key": "user_routes", "remark": "用户路由信息"}
    CAPTCHA_CODES = {"key": "captcha_codes", "remark": "图片验证码"}
    EMAIL_CODES = {"key": "email_codes", "remark": "邮箱验证码"}
    SYSTEM_CONFIG = {"key": "system_config", "remark": "系统配置信息"}


class RedisUtil:
    """
    Redis工具类（支持单节点与集群模式）
    提供连接管理、初始化配置等常用操作
    """

    @classmethod
    def _get_redis_config(cls):
        """获取Redis配置（从统一配置中心）"""
        return config.redis()

    @classmethod
    async def create_redis_connection(cls) -> AsyncRedis:
        redis_cfg = cls._get_redis_config()
        logger.debug("获取Redis配置...")
        logger.debug(redis_cfg)
        conn_params = {
            "decode_responses": True,
            "socket_timeout": redis_cfg.socket_timeout,
            "retry_on_timeout": redis_cfg.retry_on_timeout,
            "max_connections": redis_cfg.max_connections,
        }

        # 仅当密码非空字符串时才添加
        if redis_cfg.password and str(redis_cfg.password.get_secret_value()).strip():
            conn_params["password"] = str(redis_cfg.password.get_secret_value()).strip()

        try:
            logger.info("开始初始化Redis连接...")
            conn = AsyncRedis.from_url(
                f"redis://{redis_cfg.host}:{redis_cfg.port}",
                db=redis_cfg.database,
                **conn_params,
            )
            await conn.ping()
            logger.info(f"Redis连接成功（{redis_cfg.host}:{redis_cfg.port}）")
            return conn

        except AuthenticationError as e:
            logger.error(f"Redis认证失败: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Redis连接超时（地址: {redis_cfg.host}:{redis_cfg.port}）")
            raise
        except ConnectionRefusedError:
            logger.error(f"Redis连接被拒绝（地址: {redis_cfg.host}:{redis_cfg.port}）")
            raise
        except RedisError as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    @classmethod
    async def close_redis_connection(
            cls,
            conn: AsyncRedis,
    ):
        """关闭Redis连接"""
        try:
            await conn.aclose()
            logger.info("Redis连接已关闭")
        except RedisError as e:
            logger.warning(f"关闭Redis连接时发生错误: {e}")

    @classmethod
    def _get_config_key(cls, key: str) -> str:
        """获取系统配置的完整 Redis 键名"""
        return f"{RedisKeyConfig.SYSTEM_CONFIG.key}:{key}"

    @classmethod
    async def init_system_config(
            cls,
            conn: AsyncRedis,
    ):
        """初始化系统配置到Redis"""
        try:
            # 获取所有系统配置
            configs = await SystemConfig.filter(is_del=False).values("key", "value")
            if not configs:
                logger.warning("未查询到系统配置数据，跳过Redis初始化")
                return

            # 获取现有配置的所有 Redis 键名（带前缀）
            existing_keys = [cls._get_config_key(item['key']) for item in configs]
            
            # 删除现有的系统配置键（批量删除）
            if existing_keys:
                try:
                    await conn.delete(*existing_keys)
                except RedisError:
                    # 忽略不存在的键
                    pass

            # 重新设置所有系统配置到Redis（带前缀）
            async with conn.pipeline() as pipe:
                for item in configs:
                    redis_key = cls._get_config_key(item['key'])
                    await pipe.set(redis_key, item["value"])
                await pipe.execute()

            logger.info(f"系统配置已同步到Redis（共{len(configs)}条）")

        except RedisError as e:
            logger.error(f"初始化系统配置到Redis失败: {e}")
            raise

    @classmethod
    async def get_system_config(
            cls,
            conn: AsyncRedis,
            key: str
    ) -> str:
        """从Redis获取系统配置值"""
        try:
            redis_key = cls._get_config_key(key)
            value = await conn.get(redis_key)
            return value.decode('utf-8') if value else ""
        except RedisError as e:
            logger.error(f"获取系统配置失败 key={key}: {e}")
            return ""

    @classmethod
    async def set_system_config(
            cls,
            conn: AsyncRedis,
            key: str,
            value: str
    ) -> bool:
        """设置系统配置到Redis"""
        try:
            redis_key = cls._get_config_key(key)
            await conn.set(redis_key, value)
            logger.info(f"系统配置已更新 key={redis_key}")
            return True
        except RedisError as e:
            logger.error(f"设置系统配置失败 key={key}: {e}")
            return False
