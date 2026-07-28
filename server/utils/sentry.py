# _*_ coding : UTF-8 _*_
"""
Sentry 错误上报集成

当配置了 sentry_dsn 时，自动上报异常到 Sentry
"""

from typing import Optional

import sentry_sdk

from utils.log import logger


_sentry_initialized = False


async def init_sentry(dynamic_config) -> None:
    """初始化 Sentry（根据配置决定是否启用）"""
    global _sentry_initialized
    if _sentry_initialized:
        return

    dsn = await dynamic_config.get("sentry_dsn")
    if not dsn:
        logger.info("Sentry DSN 未配置，跳过初始化")
        return

    traces_sample_rate = float(
        await dynamic_config.get("sentry_traces_sample_rate", "1.0")
    )
    environment = await dynamic_config.get("sentry_environment", "production")

    try:
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=traces_sample_rate,
            environment=environment,
            send_default_pii=False,
        )
        _sentry_initialized = True
        logger.info(f"Sentry 初始化成功（环境: {environment}）")
    except Exception as e:
        logger.error(f"Sentry 初始化失败: {e}")


def capture_exception(exc: Exception, extra: Optional[dict] = None) -> None:
    """上报异常到 Sentry"""
    if not _sentry_initialized:
        return
    try:
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
    except Exception as e:
        logger.error(f"Sentry 上报异常失败: {e}")


def capture_message(
    message: str, level: str = "info", extra: Optional[dict] = None
) -> None:
    """上报消息到 Sentry"""
    if not _sentry_initialized:
        return
    try:
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error(f"Sentry 上报消息失败: {e}")
