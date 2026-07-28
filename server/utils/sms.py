# _*_ coding : UTF-8 _*_
"""
短信发送工具

支持两种短信服务商：
1. 阿里云短信 (Alibaba Cloud SMS)
2. 腾讯云短信 (Tencent Cloud SMS)

配置通过动态配置系统获取（Redis → 数据库）
支持手机号验证、每日/每分钟发送次数限制
"""

import base64
import hashlib
import hmac
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import httpx

from utils.log import logger


# ==================== 手机号验证 ====================

# 中国大陆手机号正则（1开头11位）
_PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")


def validate_phone(phone: str) -> bool:
    """验证手机号格式（中国大陆）"""
    if not phone:
        return False
    return bool(_PHONE_REGEX.match(phone.strip()))


def validate_phones(phones: List[str]) -> Tuple[List[str], List[str]]:
    """批量验证手机号，返回 (有效列表, 无效列表)"""
    valid = []
    invalid = []
    for phone in phones:
        cleaned = phone.strip()
        if validate_phone(cleaned):
            valid.append(cleaned)
        else:
            invalid.append(cleaned)
    return valid, invalid


# ==================== 发送限制 ====================


class SMSRateLimiter:
    """短信发送频率限制（基于 Redis）"""

    @staticmethod
    async def _get_limits(dynamic_config) -> Tuple[int, int]:
        """从配置获取限制：(每日上限, 每分钟上限)"""
        daily = 10
        per_minute = 1
        if dynamic_config:
            daily = int(await dynamic_config.get("sms_daily_limit", "10"))
            per_minute = int(await dynamic_config.get("sms_per_minute_limit", "1"))
        return daily, per_minute

    @staticmethod
    async def check_and_increment(
        redis, phone: str, dynamic_config=None
    ) -> Tuple[bool, str]:
        """
        检查并增加发送计数
        Returns: (是否允许发送, 提示信息)
        """
        daily_limit, per_minute_limit = await SMSRateLimiter._get_limits(dynamic_config)
        today = datetime.now().strftime("%Y-%m-%d")

        daily_key = f"sms:daily:{phone}:{today}"
        minute_key = f"sms:minute:{phone}:{int(time.time()) // 60}"

        # 检查每日限制
        daily_count = await redis.get(daily_key)
        if daily_count and int(daily_count) >= daily_limit:
            return False, f"该手机号今日已发送{daily_limit}次，请明天再试"

        # 检查每分钟限制
        minute_count = await redis.get(minute_key)
        if minute_count and int(minute_count) >= per_minute_limit:
            return False, f"操作过于频繁，请{60 - int(time.time()) % 60}秒后再试"

        # 增加计数
        pipe = redis.pipeline()
        pipe.incr(daily_key)
        pipe.expire(daily_key, 86400)  # 24小时过期
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # 2分钟过期
        await pipe.execute()

        return True, ""

    @staticmethod
    async def get_remaining_quota(redis, phone: str, dynamic_config=None) -> dict:
        """获取剩余发送次数"""
        daily_limit, per_minute_limit = await SMSRateLimiter._get_limits(dynamic_config)
        today = datetime.now().strftime("%Y-%m-%d")

        daily_count = int(await redis.get(f"sms:daily:{phone}:{today}") or 0)
        current_minute = int(time.time()) // 60
        minute_count = int(await redis.get(f"sms:minute:{phone}:{current_minute}") or 0)

        return {
            "daily_remaining": max(0, daily_limit - daily_count),
            "daily_limit": daily_limit,
            "minute_remaining": max(0, per_minute_limit - minute_count),
            "minute_limit": per_minute_limit,
        }


# ==================== 阿里云短信 ====================


class AliyunSMS:
    """阿里云短信服务"""

    API_URL = "https://dysmsapi.aliyuncs.com"

    @staticmethod
    async def _get_config(dynamic_config) -> dict:
        return {
            "access_key_id": await dynamic_config.get("sms_aliyun_access_key_id"),
            "access_key_secret": await dynamic_config.get(
                "sms_aliyun_access_key_secret"
            ),
            "sign_name": await dynamic_config.get("sms_aliyun_sign_name"),
            "template_code": await dynamic_config.get("sms_aliyun_template_code"),
        }

    @staticmethod
    def _percent_encode(s: str) -> str:
        return (
            quote_plus(s, safe="")
            .replace("+", "%20")
            .replace("*", "%2A")
            .replace("%7E", "~")
        )

    @staticmethod
    def _sign(params: dict, access_key_secret: str) -> str:
        sorted_params = sorted(params.items())
        canonicalized = "&".join(
            f"{AliyunSMS._percent_encode(k)}={AliyunSMS._percent_encode(str(v))}"
            for k, v in sorted_params
        )
        string_to_sign = f"GET&%2F&{AliyunSMS._percent_encode(canonicalized)}"
        sign_key = f"{access_key_secret}&"
        hmac_hash = hmac.new(
            sign_key.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1
        ).digest()
        return base64.b64encode(hmac_hash).decode("utf-8")

    @staticmethod
    async def send(
        phone_numbers: List[str],
        template_param: Optional[Dict[str, str]] = None,
        dynamic_config=None,
    ) -> Dict[str, bool]:
        config = await AliyunSMS._get_config(dynamic_config)
        if not config["access_key_id"]:
            logger.warning("阿里云短信未配置，跳过发送")
            return {phone: False for phone in phone_numbers}

        results = {}
        for phone in phone_numbers:
            try:
                params = {
                    "AccessKeyId": config["access_key_id"],
                    "Action": "SendSms",
                    "Format": "JSON",
                    "PhoneNumbers": phone,
                    "RegionId": "cn-hangzhou",
                    "SignName": config["sign_name"],
                    "SignatureMethod": "HMAC-SHA1",
                    "SignatureNonce": str(uuid.uuid4()),
                    "SignatureVersion": "1.0",
                    "TemplateCode": config["template_code"],
                    "Timestamp": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "Version": "2017-05-25",
                }
                if template_param:
                    params["TemplateParam"] = json.dumps(
                        template_param, ensure_ascii=False
                    )

                params["Signature"] = AliyunSMS._sign(
                    params, config["access_key_secret"]
                )

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(AliyunSMS.API_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                if data.get("Code") == "OK":
                    results[phone] = True
                    logger.info(f"阿里云短信发送成功: {phone}")
                else:
                    results[phone] = False
                    logger.warning(
                        f"阿里云短信发送失败: {phone}, Code={data.get('Code')}"
                    )
            except Exception as e:
                results[phone] = False
                logger.error(f"阿里云短信发送异常: {phone}, {e}")
        return results


# ==================== 腾讯云短信 ====================


class TencentSMS:
    """腾讯云短信服务"""

    API_URL = "https://sms.tencentcloudapi.com"
    SERVICE = "sms"
    VERSION = "2021-01-11"
    ACTION = "SendSms"

    @staticmethod
    async def _get_config(dynamic_config) -> dict:
        return {
            "secret_id": await dynamic_config.get("sms_tencent_secret_id"),
            "secret_key": await dynamic_config.get("sms_tencent_secret_key"),
            "sdk_app_id": await dynamic_config.get("sms_tencent_sdk_app_id"),
            "sign_name": await dynamic_config.get("sms_tencent_sign_name"),
            "template_id": await dynamic_config.get("sms_tencent_template_id"),
        }

    @staticmethod
    def _sign_v3(secret_key: str, date: str, service: str, string_to_sign: str) -> str:
        def _hmac_sha256(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _hmac_sha256(f"TC3{secret_key}".encode("utf-8"), date)
        secret_service = _hmac_sha256(secret_date, service)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        return hmac.new(
            secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    async def send(
        phone_numbers: List[str],
        template_param_set: Optional[List[str]] = None,
        dynamic_config=None,
    ) -> Dict[str, bool]:
        config = await TencentSMS._get_config(dynamic_config)
        if not config["secret_id"]:
            logger.warning("腾讯云短信未配置，跳过发送")
            return {phone: False for phone in phone_numbers}

        formatted_phones = [
            f"+86{phone}" if not phone.startswith("+") else phone
            for phone in phone_numbers
        ]

        payload = {
            "SmsSdkAppId": config["sdk_app_id"],
            "SignName": config["sign_name"],
            "TemplateId": config["template_id"],
            "PhoneNumberSet": formatted_phones,
        }
        if template_param_set:
            payload["TemplateParamSet"] = template_param_set

        payload_json = json.dumps(payload)
        now = int(time.time())
        date = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")

        hashed_payload = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        canonical_request = f"POST\n/\n\ncontent-type:application/json; charset=utf-8\nhost:sms.tencentcloudapi.com\n\ncontent-type;host\n{hashed_payload}"

        credential_scope = f"{date}/{TencentSMS.SERVICE}/tc3_request"
        hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (
            f"TC3-HMAC-SHA256\n{now}\n{credential_scope}\n{hashed_canonical}"
        )

        signature = TencentSMS._sign_v3(
            config["secret_key"], date, TencentSMS.SERVICE, string_to_sign
        )

        headers = {
            "Authorization": f"TC3-HMAC-SHA256 Credential={config['secret_id']}/{credential_scope}, SignedHeaders=content-type;host, Signature={signature}",
            "Content-Type": "application/json; charset=utf-8",
            "Host": "sms.tencentcloudapi.com",
            "X-TC-Action": TencentSMS.ACTION,
            "X-TC-Version": TencentSMS.VERSION,
            "X-TC-Timestamp": str(now),
        }

        results = {phone: False for phone in phone_numbers}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    TencentSMS.API_URL, headers=headers, content=payload_json
                )
                resp.raise_for_status()
                data = resp.json()

            response = data.get("Response", {})
            if "Error" in response:
                logger.error(f"腾讯云短信发送失败: {response['Error']}")
                return results

            for i, status in enumerate(response.get("SendStatusSet", [])):
                original_phone = (
                    phone_numbers[i] if i < len(phone_numbers) else "unknown"
                )
                if status.get("Code") == "Ok":
                    results[original_phone] = True
                    logger.info(f"腾讯云短信发送成功: {original_phone}")
        except Exception as e:
            logger.error(f"腾讯云短信发送异常: {e}")
        return results


# ==================== 统一短信发送器 ====================


class SMSSender:
    """统一短信发送器（带手机号验证和频率限制）"""

    @staticmethod
    async def send(
        phone_numbers: List[str],
        title: str,
        content: str,
        redis=None,
        dynamic_config=None,
    ) -> Dict[str, Any]:
        """
        发送短信通知（带验证和限流）

        Args:
            phone_numbers: 手机号列表
            title: 通知标题
            content: 通知内容
            redis: Redis连接
            dynamic_config: 动态配置服务

        Returns:
            {"success": {phone: bool}, "invalid": [phones], "rate_limited": [phones]}
        """
        if not phone_numbers:
            return {"success": {}, "invalid": [], "rate_limited": []}

        # 1. 手机号格式验证
        valid_phones, invalid_phones = validate_phones(phone_numbers)
        if invalid_phones:
            logger.warning(f"无效手机号: {invalid_phones}")

        if not valid_phones:
            return {"success": {}, "invalid": invalid_phones, "rate_limited": []}

        # 2. 频率限制检查
        allowed_phones = []
        rate_limited_phones = []

        if redis:
            for phone in valid_phones:
                ok, msg = await SMSRateLimiter.check_and_increment(
                    redis, phone, dynamic_config
                )
                if ok:
                    allowed_phones.append(phone)
                else:
                    rate_limited_phones.append(phone)
                    logger.warning(f"手机号 {phone} 发送受限: {msg}")
        else:
            allowed_phones = valid_phones

        if not allowed_phones:
            return {
                "success": {},
                "invalid": invalid_phones,
                "rate_limited": rate_limited_phones,
            }

        # 3. 发送短信
        provider = "aliyun"
        if dynamic_config:
            provider = await dynamic_config.get("sms_provider", "aliyun")

        if provider == "tencent":
            result = await TencentSMS.send(
                phone_numbers=allowed_phones,
                template_param_set=[title, content],
                dynamic_config=dynamic_config,
            )
        else:
            result = await AliyunSMS.send(
                phone_numbers=allowed_phones,
                template_param={"title": title, "content": content},
                dynamic_config=dynamic_config,
            )

        return {
            "success": result,
            "invalid": invalid_phones,
            "rate_limited": rate_limited_phones,
        }

    @staticmethod
    async def get_quota(phone: str, redis=None, dynamic_config=None) -> dict:
        """获取手机号发送配额"""
        if not redis:
            return {"daily_remaining": -1, "minute_remaining": -1}
        return await SMSRateLimiter.get_remaining_quota(redis, phone, dynamic_config)
