# _*_ coding : UTF-8 _*_
"""
RSA 数据加密工具

- 服务端生成密钥对（公钥给前端，私钥留后端）
- 前端用公钥加密请求数据
- 后端用私钥解密请求数据
- 后端用公钥加密响应数据（可选）
- 密钥存储在 Redis 中，支持动态刷新

配置通过动态配置系统控制开关
"""

import base64
from typing import Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from utils.log import logger


class RSAEncryption:
    """RSA 加解密服务"""

    REDIS_PUB_KEY = "rsa:public_key"
    REDIS_PRI_KEY = "rsa:private_key"

    @staticmethod
    async def generate_keypair(redis, key_size: int = 2048) -> Tuple[str, str]:
        """生成 RSA 密钥对并存储到 Redis"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        await redis.set(RSAEncryption.REDIS_PRI_KEY, private_pem)
        await redis.set(RSAEncryption.REDIS_PUB_KEY, public_pem)

        logger.info("RSA 密钥对已生成并存储到 Redis")
        return public_pem, private_pem

    @staticmethod
    async def get_or_generate_keypair(redis, key_size: int = 2048) -> Tuple[str, str]:
        """获取或生成密钥对"""
        public_pem = await redis.get(RSAEncryption.REDIS_PUB_KEY)
        private_pem = await redis.get(RSAEncryption.REDIS_PRI_KEY)

        if public_pem and private_pem:
            return public_pem, private_pem

        return await RSAEncryption.generate_keypair(redis, key_size)

    @staticmethod
    def encrypt_with_public_key(public_pem: str, data: str) -> str:
        """使用公钥加密数据"""
        public_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))
        encrypted = public_key.encrypt(
            data.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def decrypt_with_private_key(private_pem: str, encrypted_data: str) -> str:
        """使用私钥解密数据"""
        private_key = serialization.load_pem_private_key(
            private_pem.encode("utf-8"),
            password=None,
        )
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_data),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return decrypted.decode("utf-8")

    @staticmethod
    async def encrypt_response(redis, data: str) -> str:
        """加密响应数据"""
        public_pem, _ = await RSAEncryption.get_or_generate_keypair(redis)
        return RSAEncryption.encrypt_with_public_key(public_pem, data)

    @staticmethod
    async def decrypt_request(redis, encrypted_data: str) -> str:
        """解密请求数据"""
        _, private_pem = await RSAEncryption.get_or_generate_keypair(redis)
        return RSAEncryption.decrypt_with_private_key(private_pem, encrypted_data)
