# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:38
# @UpdateTime : 2025/08/04 01:38
# @Author : sonder
# @File : password.py
# @Software : PyCharm
# @Comment : 本程序
import hashlib

from utils.config import config


class PasswordUtil:
    """
    密码工具类
    """

    @classmethod
    async def verify_password(cls, plain_password, hashed_password):
        """
        工具方法：校验当前输入的密码与数据库存储的密码是否一致

        :param plain_password: 当前输入的密码
        :param hashed_password: 数据库存储的密码
        :return: 校验结果
        """
        salt = config.jwt().salt
        # 将盐值和密码拼接在一起
        password_with_salt = (salt + plain_password).encode('utf-8')
        # 使用SHA256算法对拼接后的密码进行加密
        password_hashed = hashlib.sha256(password_with_salt).hexdigest()
        return password_hashed == hashed_password

    @classmethod
    async def get_password_hash(cls, input_password: str):
        """
        工具方法：对当前输入的密码进行加密

        :param input_password: 输入的密码
        :return: 加密成功的密码
        """
        salt = config.jwt().salt
        # 将盐值和密码拼接在一起
        password_with_salt = (salt + input_password).encode('utf-8')
        # 使用SHA256算法对拼接后的密码进行加密
        return hashlib.sha256(password_with_salt).hexdigest()
