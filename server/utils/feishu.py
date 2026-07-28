# _*_ coding : UTF-8 _*_
"""
飞书通知工具

支持两种通知方式：
1. Webhook 群机器人 - 向飞书群聊发送消息
2. 应用消息 - 通过企业自建应用向个人发送消息

配置通过动态配置系统获取（Redis → 数据库）
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional

import httpx

from utils.log import logger


class FeishuWebhook:
    """飞书群机器人 Webhook"""

    @staticmethod
    async def _get_config(dynamic_config) -> dict:
        return {
            "webhook_url": await dynamic_config.get("feishu_webhook_url"),
            "webhook_secret": await dynamic_config.get("feishu_webhook_secret"),
        }

    @staticmethod
    def _sign(timestamp: str, secret: str = None) -> str:
        if not secret:
            return ""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    @staticmethod
    async def send_text(text: str, dynamic_config=None) -> bool:
        config = await FeishuWebhook._get_config(dynamic_config)
        if not config["webhook_url"]:
            logger.warning("飞书 Webhook 未配置，跳过发送")
            return False
        return await FeishuWebhook._post({"msg_type": "text", "content": {"text": text}}, config)

    @staticmethod
    async def send_rich_text(title: str, content_lines: List[List[Dict[str, Any]]], dynamic_config=None) -> bool:
        config = await FeishuWebhook._get_config(dynamic_config)
        if not config["webhook_url"]:
            logger.warning("飞书 Webhook 未配置，跳过发送")
            return False
        payload = {
            "msg_type": "post",
            "content": {"post": {"zh_cn": {"title": title, "content": content_lines}}},
        }
        return await FeishuWebhook._post(payload, config)

    @staticmethod
    async def send_interactive(title: str, content: str, button_text: str = "", button_url: str = "", dynamic_config=None) -> bool:
        config = await FeishuWebhook._get_config(dynamic_config)
        if not config["webhook_url"]:
            logger.warning("飞书 Webhook 未配置，跳过发送")
            return False

        elements = [{"tag": "div", "text": {"content": content, "tag": "lark_md"}}]
        if button_text and button_url:
            elements.append({
                "tag": "action",
                "actions": [{"tag": "button", "text": {"content": button_text, "tag": "plain_text"}, "url": button_url, "type": "primary"}],
            })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"content": title, "tag": "plain_text"}, "template": "blue"},
                "elements": elements,
            },
        }
        return await FeishuWebhook._post(payload, config)

    @staticmethod
    async def _post(payload: Dict[str, Any], config: dict) -> bool:
        try:
            url = config["webhook_url"]
            webhook_secret = config.get("webhook_secret") or ""
            if webhook_secret:
                timestamp = str(int(time.time()))
                payload["timestamp"] = timestamp
                payload["sign"] = FeishuWebhook._sign(timestamp, webhook_secret)

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") == 0 or result.get("StatusCode") == 0:
                    logger.info("飞书 Webhook 消息发送成功")
                    return True
                else:
                    logger.error(f"飞书 Webhook 发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"飞书 Webhook 请求异常: {e}")
            return False


class FeishuAppMessage:
    """飞书应用消息（企业自建应用）"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages"

    _tenant_access_token: Optional[str] = None
    _token_expires_at: float = 0

    @classmethod
    async def _get_config(cls, dynamic_config) -> dict:
        return {
            "app_id": await dynamic_config.get("feishu_app_id"),
            "app_secret": await dynamic_config.get("feishu_app_secret"),
        }

    @classmethod
    async def _get_tenant_access_token(cls, dynamic_config) -> Optional[str]:
        now = time.time()
        if cls._tenant_access_token and now < cls._token_expires_at:
            return cls._tenant_access_token

        config = await cls._get_config(dynamic_config)
        if not (config["app_id"] and config["app_secret"]):
            logger.warning("飞书 app_id/app_secret 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(cls.TOKEN_URL, json={"app_id": config["app_id"], "app_secret": config["app_secret"]})
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") == 0:
                    cls._tenant_access_token = result["tenant_access_token"]
                    cls._token_expires_at = now + result.get("expire", 7200) - 300
                    return cls._tenant_access_token
                logger.error(f"获取飞书 token 失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取飞书 token 异常: {e}")
            return None

    @classmethod
    async def send_text(cls, open_id: str, text: str, dynamic_config=None) -> bool:
        return await cls._send(open_id, "text", {"text": text}, dynamic_config)

    @classmethod
    async def send_interactive(cls, open_id: str, title: str, content_text: str, dynamic_config=None) -> bool:
        card = {
            "header": {"title": {"content": title, "tag": "plain_text"}, "template": "blue"},
            "elements": [{"tag": "div", "text": {"content": content_text, "tag": "lark_md"}}],
        }
        return await cls._send(open_id, "interactive", card, dynamic_config)

    @classmethod
    async def _send(cls, open_id: str, msg_type: str, content: Dict[str, Any], dynamic_config=None) -> bool:
        token = await cls._get_tenant_access_token(dynamic_config)
        if not token:
            return False

        try:
            payload = {"receive_id": open_id, "msg_type": msg_type, "content": json.dumps(content)}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{cls.SEND_URL}?receive_id_type=open_id",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") == 0:
                    logger.info(f"飞书消息发送成功: {open_id}")
                    return True
                logger.error(f"飞书消息发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"飞书消息请求异常: {e}")
            return False
