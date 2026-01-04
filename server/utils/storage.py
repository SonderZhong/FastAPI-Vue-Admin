# _*_ coding : UTF-8 _*_
# @Time : 2025/12/30
# @Author : sonder
# @File : storage.py
# @Comment : 统一存储服务 - 支持本地存储和各大云存储

import uuid
import hashlib
import aiofiles
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile

from utils.log import logger


class StorageType:
    """存储类型常量"""
    LOCAL = "local"
    ALIYUN_OSS = "aliyun_oss"
    TENCENT_COS = "tencent_cos"
    QINIU = "qiniu"
    MINIO = "minio"


class BaseStorage(ABC):
    """存储基类"""
    
    @abstractmethod
    async def upload(self, file: UploadFile, path: str = "") -> dict:
        """
        上传文件
        :param file: 上传的文件
        :param path: 存储路径前缀
        :return: {"url": "文件访问URL", "key": "文件存储key", "size": 文件大小}
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除文件
        :param key: 文件存储key
        :return: 是否成功
        """
        pass
    
    @abstractmethod
    async def get_url(self, key: str, expires: int = 3600) -> str:
        """
        获取文件访问URL
        :param key: 文件存储key
        :param expires: URL有效期（秒）
        :return: 文件访问URL
        """
        pass
    
    @staticmethod
    def generate_key(filename: str, path: str = "") -> str:
        """生成唯一文件key"""
        ext = Path(filename).suffix.lower()
        date_path = datetime.now().strftime("%Y/%m/%d")
        unique_id = uuid.uuid4().hex[:16]
        key = f"{date_path}/{unique_id}{ext}"
        if path:
            key = f"{path.strip('/')}/{key}"
        return key
    
    @staticmethod
    def get_file_hash(content: bytes) -> str:
        """计算文件MD5"""
        return hashlib.md5(content).hexdigest()


class LocalStorage(BaseStorage):
    """本地存储"""
    
    def __init__(self, base_path: str = "uploads", url_prefix: str = "/files"):
        self.base_path = Path(base_path)
        self.url_prefix = url_prefix.rstrip("/")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload(self, file: UploadFile, path: str = "") -> dict:
        key = self.generate_key(file.filename, path)
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        return {
            "url": f"{self.url_prefix}/{key}",
            "key": key,
            "size": len(content),
            "hash": self.get_file_hash(content)
        }
    
    async def delete(self, key: str) -> bool:
        try:
            file_path = self.base_path / key
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error(f"删除本地文件失败: {e}")
            return False
    
    async def get_url(self, key: str, expires: int = 3600) -> str:
        return f"{self.url_prefix}/{key}"
    
    def get_file_path(self, key: str) -> Path:
        """获取文件本地路径"""
        return self.base_path / key


class AliyunOSSStorage(BaseStorage):
    """阿里云OSS存储"""
    
    def __init__(self, access_key: str, secret_key: str, bucket: str, endpoint: str, domain: str = ""):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket
        self.endpoint = endpoint
        self.domain = domain
        self._client = None
        self._bucket = None
    
    def _get_bucket(self):
        if self._bucket is None:
            try:
                import oss2
                auth = oss2.Auth(self.access_key, self.secret_key)
                self._bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
            except ImportError:
                raise ImportError("请安装 oss2: pip install oss2")
        return self._bucket
    
    async def upload(self, file: UploadFile, path: str = "") -> dict:
        import asyncio
        key = self.generate_key(file.filename, path)
        content = await file.read()
        
        bucket = self._get_bucket()
        await asyncio.to_thread(bucket.put_object, key, content)
        
        url = await self.get_url(key)
        return {
            "url": url,
            "key": key,
            "size": len(content),
            "hash": self.get_file_hash(content)
        }
    
    async def delete(self, key: str) -> bool:
        import asyncio
        try:
            bucket = self._get_bucket()
            await asyncio.to_thread(bucket.delete_object, key)
            return True
        except Exception as e:
            logger.error(f"删除阿里云OSS文件失败: {e}")
            return False
    
    async def get_url(self, key: str, expires: int = 3600) -> str:
        if self.domain:
            return f"https://{self.domain}/{key}"
        return f"https://{self.bucket_name}.{self.endpoint}/{key}"


class TencentCOSStorage(BaseStorage):
    """腾讯云COS存储"""
    
    def __init__(self, secret_id: str, secret_key: str, bucket: str, region: str, domain: str = ""):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.bucket = bucket
        self.region = region
        self.domain = domain
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from qcloud_cos import CosConfig, CosS3Client
                config = CosConfig(
                    Region=self.region,
                    SecretId=self.secret_id,
                    SecretKey=self.secret_key
                )
                self._client = CosS3Client(config)
            except ImportError:
                raise ImportError("请安装 cos-python-sdk-v5: pip install cos-python-sdk-v5")
        return self._client
    
    async def upload(self, file: UploadFile, path: str = "") -> dict:
        import asyncio
        key = self.generate_key(file.filename, path)
        content = await file.read()
        
        client = self._get_client()
        await asyncio.to_thread(
            client.put_object,
            Bucket=self.bucket,
            Body=content,
            Key=key
        )
        
        url = await self.get_url(key)
        return {
            "url": url,
            "key": key,
            "size": len(content),
            "hash": self.get_file_hash(content)
        }
    
    async def delete(self, key: str) -> bool:
        import asyncio
        try:
            client = self._get_client()
            await asyncio.to_thread(
                client.delete_object,
                Bucket=self.bucket,
                Key=key
            )
            return True
        except Exception as e:
            logger.error(f"删除腾讯云COS文件失败: {e}")
            return False
    
    async def get_url(self, key: str, expires: int = 3600) -> str:
        if self.domain:
            return f"https://{self.domain}/{key}"
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{key}"


class QiniuStorage(BaseStorage):
    """七牛云存储"""
    
    def __init__(self, access_key: str, secret_key: str, bucket: str, domain: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.domain = domain
        self._auth = None
    
    def _get_auth(self):
        if self._auth is None:
            try:
                from qiniu import Auth
                self._auth = Auth(self.access_key, self.secret_key)
            except ImportError:
                raise ImportError("请安装 qiniu: pip install qiniu")
        return self._auth
    
    async def upload(self, file: UploadFile, path: str = "") -> dict:
        import asyncio
        from qiniu import put_data
        
        key = self.generate_key(file.filename, path)
        content = await file.read()
        
        auth = self._get_auth()
        token = auth.upload_token(self.bucket, key)
        
        ret, info = await asyncio.to_thread(put_data, token, key, content)
        
        if info.status_code != 200:
            raise Exception(f"七牛云上传失败: {info.error}")
        
        url = await self.get_url(key)
        return {
            "url": url,
            "key": key,
            "size": len(content),
            "hash": self.get_file_hash(content)
        }
    
    async def delete(self, key: str) -> bool:
        import asyncio
        try:
            from qiniu import BucketManager
            auth = self._get_auth()
            bucket_manager = BucketManager(auth)
            ret, info = await asyncio.to_thread(bucket_manager.delete, self.bucket, key)
            return info.status_code == 200
        except Exception as e:
            logger.error(f"删除七牛云文件失败: {e}")
            return False
    
    async def get_url(self, key: str, expires: int = 3600) -> str:
        return f"https://{self.domain}/{key}"


class MinIOStorage(BaseStorage):
    """MinIO存储"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from minio import Minio
                self._client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
                # 确保bucket存在
                if not self._client.bucket_exists(self.bucket):
                    self._client.make_bucket(self.bucket)
            except ImportError:
                raise ImportError("请安装 minio: pip install minio")
        return self._client
    
    async def upload(self, file: UploadFile, path: str = "") -> dict:
        import asyncio
        from io import BytesIO
        
        key = self.generate_key(file.filename, path)
        content = await file.read()
        
        client = self._get_client()
        await asyncio.to_thread(
            client.put_object,
            self.bucket,
            key,
            BytesIO(content),
            len(content)
        )
        
        url = await self.get_url(key)
        return {
            "url": url,
            "key": key,
            "size": len(content),
            "hash": self.get_file_hash(content)
        }
    
    async def delete(self, key: str) -> bool:
        import asyncio
        try:
            client = self._get_client()
            await asyncio.to_thread(client.remove_object, self.bucket, key)
            return True
        except Exception as e:
            logger.error(f"删除MinIO文件失败: {e}")
            return False
    
    async def get_url(self, key: str, expires: int = 3600) -> str:
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket}/{key}"


class StorageFactory:
    """存储工厂"""
    
    @staticmethod
    async def create(dynamic_config) -> BaseStorage:
        """
        根据配置创建存储实例
        :param dynamic_config: 动态配置服务
        :return: 存储实例
        """
        storage_type = await dynamic_config.get("upload_storage_type", StorageType.LOCAL)
        
        if storage_type == StorageType.LOCAL:
            base_path = await dynamic_config.get("upload_local_path", "uploads")
            url_prefix = await dynamic_config.get("upload_url_prefix", "/files")
            # 确保 url_prefix 不包含 /api 前缀（前端代理会处理）
            if url_prefix.startswith("/api"):
                url_prefix = url_prefix[4:]  # 去掉 /api 前缀
            return LocalStorage(base_path, url_prefix)
        
        elif storage_type == StorageType.ALIYUN_OSS:
            return AliyunOSSStorage(
                access_key=await dynamic_config.get("aliyun_oss_access_key", ""),
                secret_key=await dynamic_config.get("aliyun_oss_secret_key", ""),
                bucket=await dynamic_config.get("aliyun_oss_bucket", ""),
                endpoint=await dynamic_config.get("aliyun_oss_endpoint", ""),
                domain=await dynamic_config.get("aliyun_oss_domain", "")
            )
        
        elif storage_type == StorageType.TENCENT_COS:
            return TencentCOSStorage(
                secret_id=await dynamic_config.get("tencent_cos_secret_id", ""),
                secret_key=await dynamic_config.get("tencent_cos_secret_key", ""),
                bucket=await dynamic_config.get("tencent_cos_bucket", ""),
                region=await dynamic_config.get("tencent_cos_region", ""),
                domain=await dynamic_config.get("tencent_cos_domain", "")
            )
        
        elif storage_type == StorageType.QINIU:
            return QiniuStorage(
                access_key=await dynamic_config.get("qiniu_access_key", ""),
                secret_key=await dynamic_config.get("qiniu_secret_key", ""),
                bucket=await dynamic_config.get("qiniu_bucket", ""),
                domain=await dynamic_config.get("qiniu_domain", "")
            )
        
        elif storage_type == StorageType.MINIO:
            return MinIOStorage(
                endpoint=await dynamic_config.get("minio_endpoint", ""),
                access_key=await dynamic_config.get("minio_access_key", ""),
                secret_key=await dynamic_config.get("minio_secret_key", ""),
                bucket=await dynamic_config.get("minio_bucket", ""),
                secure=await dynamic_config.get_bool("minio_secure", False)
            )
        
        else:
            # 默认使用本地存储
            return LocalStorage()
