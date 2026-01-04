# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 20:15
# @UpdateTime : 2025/08/03 20:15
# @Author : sonder
# @File : mail.py
# @Software : PyCharm
# @Comment : 本程序
import random
from datetime import timedelta
from email.message import EmailMessage
from email.utils import formataddr

from aiosmtplib import send
from fastapi import Request
from jinja2 import Environment, FileSystemLoader

from utils.config import config
from utils.get_redis import RedisKeyConfig
from utils.log import logger


class Email:
    """
    邮件发送类，用于发送邮件。
    支持从动态配置读取邮件服务器参数
    """

    @classmethod
    async def generate_verification_code(cls, length: int = 4) -> str:
        """
        随机生成数字验证码
        :param length: 验证码长度
        :return:
        """

        return ''.join(str(random.randint(0, 9)) for _ in range(length))

    @classmethod
    async def _get_email_config(cls, request: Request) -> dict:
        """
        获取邮件配置（优先从动态配置读取）
        """
        dynamic_config = getattr(request.app.state, 'dynamic_config', None)
        
        if dynamic_config:
            # 从动态配置读取
            host = await dynamic_config.get("email_host") or config.email().host
            port = await dynamic_config.get_int("email_port") or config.email().port
            username = await dynamic_config.get("email_username") or config.email().username
            password = await dynamic_config.get("email_password") or str(config.email().password.get_secret_value())
            from_addr = await dynamic_config.get("email_from_addr") or config.email().from_addr
            from_name = await dynamic_config.get("email_from_name") or ""
            use_ssl = await dynamic_config.get_bool("email_use_ssl", True)
        else:
            # 回退到静态配置
            host = config.email().host
            port = config.email().port
            username = config.email().username
            password = str(config.email().password.get_secret_value())
            from_addr = config.email().from_addr
            from_name = ""
            use_ssl = True
        
        return {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "from_addr": from_addr,
            "from_name": from_name,
            "use_ssl": use_ssl
        }

    @classmethod
    async def send_email(cls, request: Request, username: str, title: str = "注册", mail: str = "") -> bool:
        """
        发送邮件
        :param request: 请求对象
        :param username: 用户账号
        :param title: 邮件标题
        :param mail: 邮箱地址
        """
        # 获取邮件配置
        email_cfg = await cls._get_email_config(request)
        
        code = await cls.generate_verification_code(4)
        codeStr = ""
        for i in code:
            codeStr += f"""<button class="button">{i}</button>"""
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('mail_en.html')
        
        # 获取系统名称
        dynamic_config = getattr(request.app.state, 'dynamic_config', None)
        system_name = config.app().name
        if dynamic_config:
            system_name = await dynamic_config.get("system_name") or system_name
        
        content = template.render(
            TITLE=title,
            CODE=codeStr,
            PROJECTNAME=system_name,
        )
        subject = f"{system_name}-{title} Verification Code"
        
        # 发件人名称：优先使用配置的名称，否则使用系统名称
        sendName = email_cfg["from_name"] or system_name
        
        message = EmailMessage()
        message["From"] = formataddr((sendName, email_cfg["username"]))
        message["To"] = mail
        message["Subject"] = subject
        message.set_content(content, subtype="html")
        
        try:
            await send(
                message,
                hostname=email_cfg["host"],
                port=email_cfg["port"],
                username=email_cfg["username"],
                password=email_cfg["password"],
                use_tls=email_cfg["use_ssl"]
            )
            await request.app.state.redis.set(
                f"{RedisKeyConfig.EMAIL_CODES.key}:{mail}-{username}",
                code,
                ex=timedelta(minutes=2)
            )
            logger.info(f"发送邮件至{mail}成功，验证码：{code}")
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    @classmethod
    async def verify_code(cls, request: Request, username: str, mail: str, code: str) -> dict:
        """
        验证验证码
        :param request: 请求对象
        :param username: 用户账号
        :param mail: 邮箱地址
        :param code: 验证码
        """
        redis_code = await request.app.state.redis.get(f"{RedisKeyConfig.EMAIL_CODES.key}:{mail}-{username}")
        if redis_code is None:
            return {
                "status": False,
                "msg": "验证码已过期"
            }
        if str(redis_code).lower() == code.lower():
            await request.app.state.redis.delete(f"{RedisKeyConfig.EMAIL_CODES.key}:{mail}-{username}")
            return {
                "status": True,
                "msg": "验证码正确"
            }
        return {
            "status": False,
            "msg": "验证码错误"
        }
