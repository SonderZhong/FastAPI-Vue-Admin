# _*_ coding : UTF-8 _*_
"""
钉钉通知工具

支持两种通知方式：
1. Webhook 群机器人 - 向钉钉群聊发送消息
2. 工作通知 - 通过企业内部应用向个人发送工作通知

配置通过动态配置系统获取（Redis → 数据库）
"""

import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx

from utils.log import logger


class DingTalkWebhook:
    """钉钉群机器人 Webhook"""

    @staticmethod
    async def _get_config(dynamic_config) -> dict:
        return {
            "webhook_url": await dynamic_config.get("dingtalk_webhook_url"),
            "webhook_secret": await dynamic_config.get("dingtalk_webhook_secret"),
        }

    @staticmethod
    def _sign_with_secret(secret: str) -> Dict[str, str]:
        if not secret:
            return {}
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return {"timestamp": timestamp, "sign": sign}

    @staticmethod
    async def send_text(
        content: str,
        at_mobiles: List[str] = None,
        at_all: bool = False,
        dynamic_config=None,
    ) -> bool:
        config = await DingTalkWebhook._get_config(dynamic_config)
        if not config["webhook_url"]:
            logger.warning("钉钉 Webhook 未配置，跳过发送")
            return False
        payload = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {"atMobiles": at_mobiles or [], "isAtAll": at_all},
        }
        return await DingTalkWebhook._post(payload, config)

    @staticmethod
    async def send_markdown(
        title: str,
        text: str,
        at_mobiles: List[str] = None,
        at_all: bool = False,
        dynamic_config=None,
    ) -> bool:
        config = await DingTalkWebhook._get_config(dynamic_config)
        if not config["webhook_url"]:
            logger.warning("钉钉 Webhook 未配置，跳过发送")
            return False
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"atMobiles": at_mobiles or [], "isAtAll": at_all},
        }
        return await DingTalkWebhook._post(payload, config)

    @staticmethod
    async def send_action_card(
        title: str,
        text: str,
        single_url: str = "",
        single_title: str = "查看详情",
        dynamic_config=None,
    ) -> bool:
        config = await DingTalkWebhook._get_config(dynamic_config)
        if not config["webhook_url"]:
            logger.warning("钉钉 Webhook 未配置，跳过发送")
            return False
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "singleTitle": single_title,
                "singleURL": single_url,
            },
        }
        return await DingTalkWebhook._post(payload, config)

    @staticmethod
    async def _post(payload: Dict[str, Any], config: dict) -> bool:
        try:
            url = config["webhook_url"]
            sign_params = DingTalkWebhook._sign_with_secret(
                config.get("webhook_secret") or ""
            )
            if sign_params:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}timestamp={sign_params['timestamp']}&sign={sign_params['sign']}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("钉钉 Webhook 消息发送成功")
                    return True
                logger.error(f"钉钉 Webhook 发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"钉钉 Webhook 请求异常: {e}")
            return False


class DingTalkWorkNotice:
    """钉钉工作通知（企业内部应用）"""

    TOKEN_URL = "https://oapi.dingtalk.com/gettoken"
    SEND_URL = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"

    _access_token: Optional[str] = None
    _token_expires_at: float = 0

    @classmethod
    async def _get_config(cls, dynamic_config) -> dict:
        return {
            "app_id": await dynamic_config.get("dingtalk_app_id"),
            "app_secret": await dynamic_config.get("dingtalk_app_secret"),
            "agent_id": await dynamic_config.get("dingtalk_agent_id"),
        }

    @classmethod
    async def _get_access_token(cls, dynamic_config) -> Optional[str]:
        now = time.time()
        if cls._access_token and now < cls._token_expires_at:
            return cls._access_token

        config = await cls._get_config(dynamic_config)
        if not (config["app_id"] and config["app_secret"]):
            logger.warning("钉钉 app_id/app_secret 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cls.TOKEN_URL,
                    params={
                        "appkey": config["app_id"],
                        "appsecret": config["app_secret"],
                    },
                )
                resp.raise_for_status()
                result = resp.json()
                if result.get("errcode") == 0:
                    cls._access_token = result["access_token"]
                    cls._token_expires_at = now + result.get("expires_in", 7200) - 300
                    return cls._access_token
                logger.error(f"获取钉钉 token 失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取钉钉 token 异常: {e}")
            return None

    @classmethod
    async def send_text(
        cls, userid_list: List[str], content: str, dynamic_config=None
    ) -> bool:
        return await cls._send(
            userid_list,
            {"msgtype": "text", "text": {"content": content}},
            dynamic_config,
        )

    @classmethod
    async def send_markdown(
        cls, userid_list: List[str], title: str, text: str, dynamic_config=None
    ) -> bool:
        return await cls._send(
            userid_list,
            {"msgtype": "markdown", "markdown": {"title": title, "text": text}},
            dynamic_config,
        )

    @classmethod
    async def send_action_card(
        cls,
        userid_list: List[str],
        title: str,
        markdown: str,
        single_url: str = "",
        single_title: str = "查看详情",
        dynamic_config=None,
    ) -> bool:
        return await cls._send(
            userid_list,
            {
                "msgtype": "action_card",
                "action_card": {
                    "title": title,
                    "markdown": markdown,
                    "single_title": single_title,
                    "single_url": single_url,
                },
            },
            dynamic_config,
        )

    @classmethod
    async def _send(
        cls, userid_list: List[str], msg: Dict[str, Any], dynamic_config=None
    ) -> bool:
        token = await cls._get_access_token(dynamic_config)
        if not token:
            return False

        config = await cls._get_config(dynamic_config)
        agent_id = config["agent_id"]

        try:
            payload = {
                "agent_id": agent_id,
                "userid_list": ",".join(userid_list[:100]),
                "msg": msg,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    cls.SEND_URL, params={"access_token": token}, json=payload
                )
                resp.raise_for_status()
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info(f"钉钉工作通知发送成功: {len(userid_list)} 人")
                    return True
                logger.error(f"钉钉工作通知发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"钉钉工作通知请求异常: {e}")
            return False
