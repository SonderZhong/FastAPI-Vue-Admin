# _*_ coding : UTF-8 _*_
# @Time : 2025/12/30
# @Author : sonder
# @File : dynamic_config.py
# @Comment : 动态配置服务 - 支持从数据库加载配置到Redis，运行时动态读取

from typing import Any, Dict, List, Optional
from redis.asyncio import Redis as AsyncRedis

from models import SystemConfig
from models.config import ConfigGroup
from utils.log import logger
from utils.get_redis import RedisKeyConfig


class DynamicConfigService:
    """
    动态配置服务
    - 应用启动时从数据库加载配置到 Redis
    - 运行时从 Redis 读取配置
    - 配置更新时同步更新数据库和 Redis
    """
    
    # Redis 配置前缀
    CONFIG_PREFIX = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:"
    
    # 默认配置定义（首次启动时初始化到数据库）
    DEFAULT_CONFIGS = [
        # 邮件配置
        {"group": ConfigGroup.EMAIL, "key": "email_host", "name": "SMTP服务器", "value": "smtp.qq.com", "type": True, "remark": "SMTP服务器地址"},
        {"group": ConfigGroup.EMAIL, "key": "email_port", "name": "SMTP端口", "value": "465", "type": True, "remark": "SMTP端口，SSL:465, TLS:587"},
        {"group": ConfigGroup.EMAIL, "key": "email_username", "name": "邮箱账号", "value": "", "type": True, "remark": "发件邮箱账号"},
        {"group": ConfigGroup.EMAIL, "key": "email_password", "name": "邮箱密码/授权码", "value": "", "type": True, "remark": "邮箱授权码（非登录密码）"},
        {"group": ConfigGroup.EMAIL, "key": "email_from_addr", "name": "发件人地址", "value": "", "type": True, "remark": "发件人显示地址"},
        {"group": ConfigGroup.EMAIL, "key": "email_from_name", "name": "发件人名称", "value": "", "type": True, "remark": "发件人显示名称，如：系统管理员"},
        {"group": ConfigGroup.EMAIL, "key": "email_use_ssl", "name": "启用SSL", "value": "true", "type": True, "remark": "是否启用SSL加密"},
        {"group": ConfigGroup.EMAIL, "key": "email_timeout", "name": "超时时间", "value": "30", "type": True, "remark": "邮件发送超时时间（秒）"},
        
        # 地图配置
        {"group": ConfigGroup.MAP, "key": "map_provider", "name": "地图服务商", "value": "baidu", "type": True, "remark": "地图服务提供商：baidu/amap/tencent"},
        {"group": ConfigGroup.MAP, "key": "map_ak", "name": "地图AK", "value": "", "type": True, "remark": "地图服务访问密钥"},
        {"group": ConfigGroup.MAP, "key": "map_sk", "name": "地图SK", "value": "", "type": True, "remark": "地图服务安全密钥"},
        {"group": ConfigGroup.MAP, "key": "map_timeout", "name": "超时时间", "value": "10", "type": True, "remark": "地图API超时时间（秒）"},
        
        # 系统配置
        {"group": ConfigGroup.SYSTEM, "key": "system_name", "name": "系统名称", "value": "FastAPI-Vue-Admin", "type": True, "remark": "系统显示名称"},
        {"group": ConfigGroup.SYSTEM, "key": "system_version", "name": "系统版本", "value": "1.0.0", "type": True, "remark": "系统版本号"},
        {"group": ConfigGroup.SYSTEM, "key": "api_status_enabled", "name": "启用状态接口", "value": "true", "type": True, "remark": "是否启用/health等状态接口"},
        {"group": ConfigGroup.SYSTEM, "key": "ip_location_enabled", "name": "启用IP定位", "value": "true", "type": True, "remark": "是否启用IP地理位置查询"},
        
        # 安全配置
        {"group": ConfigGroup.SECURITY, "key": "multi_login_allowed", "name": "允许多设备登录", "value": "true", "type": True, "remark": "是否允许同一用户多设备登录"},
        {"group": ConfigGroup.SECURITY, "key": "login_expire_minutes", "name": "登录有效期", "value": "1440", "type": True, "remark": "登录令牌有效期（分钟）"},
        
        # 账户配置
        {"group": ConfigGroup.ACCOUNT, "key": "account_captcha_enabled", "name": "启用验证码", "value": "true", "type": True, "remark": "登录是否需要验证码"},
        {"group": ConfigGroup.ACCOUNT, "key": "account_captcha_type", "name": "验证码类型", "value": "0", "type": True, "remark": "验证码类型：0=算术题，1=字母数字"},
        {"group": ConfigGroup.ACCOUNT, "key": "account_register_enabled", "name": "开放注册", "value": "true", "type": True, "remark": "是否开放用户注册"},
        {"group": ConfigGroup.ACCOUNT, "key": "default_department_id", "name": "默认部门", "value": "", "type": True, "remark": "新用户默认部门ID"},
        {"group": ConfigGroup.ACCOUNT, "key": "default_role_id", "name": "默认角色", "value": "", "type": True, "remark": "新用户默认角色ID"},
        
        # 上传配置 - 基础
        {"group": ConfigGroup.UPLOAD, "key": "upload_storage_type", "name": "存储类型", "value": "local", "type": True, "remark": "文件存储类型：local/aliyun_oss/tencent_cos/qiniu/minio"},
        {"group": ConfigGroup.UPLOAD, "key": "upload_max_size", "name": "单文件大小限制", "value": "100", "type": True, "remark": "单个文件上传的最大大小（MB）"},
        {"group": ConfigGroup.UPLOAD, "key": "upload_allowed_extensions", "name": "允许的扩展名", "value": "bmp,gif,jpg,jpeg,png,webp,doc,docx,xls,xlsx,ppt,pptx,pdf,txt,zip,rar", "type": True, "remark": "允许上传的文件扩展名，逗号分隔"},
        {"group": ConfigGroup.UPLOAD, "key": "upload_local_path", "name": "本地存储路径", "value": "uploads", "type": True, "remark": "本地文件存储目录"},
        {"group": ConfigGroup.UPLOAD, "key": "upload_url_prefix", "name": "访问URL前缀", "value": "/files", "type": True, "remark": "文件访问URL前缀"},
        
        # 阿里云OSS配置
        {"group": ConfigGroup.UPLOAD, "key": "aliyun_oss_access_key", "name": "阿里云AccessKey", "value": "", "type": True, "remark": "阿里云OSS AccessKey ID"},
        {"group": ConfigGroup.UPLOAD, "key": "aliyun_oss_secret_key", "name": "阿里云SecretKey", "value": "", "type": True, "remark": "阿里云OSS AccessKey Secret"},
        {"group": ConfigGroup.UPLOAD, "key": "aliyun_oss_bucket", "name": "阿里云Bucket", "value": "", "type": True, "remark": "阿里云OSS Bucket名称"},
        {"group": ConfigGroup.UPLOAD, "key": "aliyun_oss_endpoint", "name": "阿里云Endpoint", "value": "", "type": True, "remark": "阿里云OSS Endpoint，如：oss-cn-hangzhou.aliyuncs.com"},
        {"group": ConfigGroup.UPLOAD, "key": "aliyun_oss_domain", "name": "阿里云自定义域名", "value": "", "type": True, "remark": "阿里云OSS自定义域名（可选）"},
        
        # 腾讯云COS配置
        {"group": ConfigGroup.UPLOAD, "key": "tencent_cos_secret_id", "name": "腾讯云SecretId", "value": "", "type": True, "remark": "腾讯云COS SecretId"},
        {"group": ConfigGroup.UPLOAD, "key": "tencent_cos_secret_key", "name": "腾讯云SecretKey", "value": "", "type": True, "remark": "腾讯云COS SecretKey"},
        {"group": ConfigGroup.UPLOAD, "key": "tencent_cos_bucket", "name": "腾讯云Bucket", "value": "", "type": True, "remark": "腾讯云COS Bucket名称"},
        {"group": ConfigGroup.UPLOAD, "key": "tencent_cos_region", "name": "腾讯云Region", "value": "", "type": True, "remark": "腾讯云COS Region，如：ap-guangzhou"},
        {"group": ConfigGroup.UPLOAD, "key": "tencent_cos_domain", "name": "腾讯云自定义域名", "value": "", "type": True, "remark": "腾讯云COS自定义域名（可选）"},
        
        # 七牛云配置
        {"group": ConfigGroup.UPLOAD, "key": "qiniu_access_key", "name": "七牛云AccessKey", "value": "", "type": True, "remark": "七牛云AccessKey"},
        {"group": ConfigGroup.UPLOAD, "key": "qiniu_secret_key", "name": "七牛云SecretKey", "value": "", "type": True, "remark": "七牛云SecretKey"},
        {"group": ConfigGroup.UPLOAD, "key": "qiniu_bucket", "name": "七牛云Bucket", "value": "", "type": True, "remark": "七牛云Bucket名称"},
        {"group": ConfigGroup.UPLOAD, "key": "qiniu_domain", "name": "七牛云域名", "value": "", "type": True, "remark": "七牛云访问域名"},
        
        # MinIO配置
        {"group": ConfigGroup.UPLOAD, "key": "minio_endpoint", "name": "MinIO地址", "value": "", "type": True, "remark": "MinIO服务地址，如：localhost:9000"},
        {"group": ConfigGroup.UPLOAD, "key": "minio_access_key", "name": "MinIO AccessKey", "value": "", "type": True, "remark": "MinIO AccessKey"},
        {"group": ConfigGroup.UPLOAD, "key": "minio_secret_key", "name": "MinIO SecretKey", "value": "", "type": True, "remark": "MinIO SecretKey"},
        {"group": ConfigGroup.UPLOAD, "key": "minio_bucket", "name": "MinIO Bucket", "value": "", "type": True, "remark": "MinIO Bucket名称"},
        {"group": ConfigGroup.UPLOAD, "key": "minio_secure", "name": "MinIO启用HTTPS", "value": "false", "type": True, "remark": "MinIO是否启用HTTPS"},
    ]
    
    def __init__(self, redis: AsyncRedis):
        self.redis = redis
    
    async def init_default_configs(self):
        """
        初始化默认配置到数据库
        仅当配置不存在时才创建
        """
        for cfg in self.DEFAULT_CONFIGS:
            try:
                # 尝试查询（可能 group 字段不存在）
                existing = await SystemConfig.filter(key=cfg["key"], is_del=False).first()
                if not existing:
                    # 创建时尝试包含 group 字段
                    try:
                        await SystemConfig.create(
                            name=cfg["name"],
                            key=cfg["key"],
                            value=cfg["value"],
                            group=cfg["group"],
                            type=cfg["type"],
                            remark=cfg.get("remark", "")
                        )
                    except Exception:
                        # 如果 group 字段不存在，不带 group 创建
                        await SystemConfig.create(
                            name=cfg["name"],
                            key=cfg["key"],
                            value=cfg["value"],
                            type=cfg["type"],
                            remark=cfg.get("remark", "")
                        )
                    logger.info(f"初始化配置: {cfg['key']}")
            except Exception as e:
                logger.warning(f"初始化配置 {cfg['key']} 失败: {e}")
    
    async def load_all_to_redis(self):
        """
        从数据库加载所有配置到 Redis
        """
        try:
            configs = await SystemConfig.filter(is_del=False).values("key", "value")
            if not configs:
                logger.warning("未查询到系统配置数据")
                return
            
            async with self.redis.pipeline() as pipe:
                for cfg in configs:
                    redis_key = f"{self.CONFIG_PREFIX}{cfg['key']}"
                    await pipe.set(redis_key, cfg["value"])
                await pipe.execute()
            
            logger.info(f"已加载 {len(configs)} 条配置到 Redis")
        except Exception as e:
            logger.error(f"加载配置到 Redis 失败: {e}")
    
    async def get(self, key: str, default: Any = None) -> Optional[str]:
        """
        获取配置值（优先从 Redis 读取）
        
        :param key: 配置键名
        :param default: 默认值
        :return: 配置值
        """
        redis_key = f"{self.CONFIG_PREFIX}{key}"
        value = await self.redis.get(redis_key)
        if value is not None:
            return value
        
        # Redis 中不存在，从数据库读取并缓存
        config = await SystemConfig.get_or_none(key=key, is_del=False)
        if config:
            await self.redis.set(redis_key, config.value)
            return config.value
        
        return default
    
    async def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型配置"""
        value = await self.get(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    async def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型配置"""
        value = await self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    async def get_list(self, key: str, separator: str = ",", default: List[str] = None) -> List[str]:
        """获取列表类型配置"""
        value = await self.get(key)
        if value is None:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    async def set(self, key: str, value: str, name: str = None, group: str = None, remark: str = None) -> bool:
        """
        设置配置值（同时更新数据库和 Redis）
        
        :param key: 配置键名
        :param value: 配置值
        :param name: 配置名称（新建时必填）
        :param group: 配置分组
        :param remark: 备注
        :return: 是否成功
        """
        try:
            # 更新或创建数据库记录
            config = await SystemConfig.get_or_none(key=key, is_del=False)
            if config:
                config.value = value
                if name:
                    config.name = name
                if group:
                    config.group = group
                if remark is not None:
                    config.remark = remark
                await config.save()
            else:
                await SystemConfig.create(
                    key=key,
                    value=value,
                    name=name or key,
                    group=group or ConfigGroup.SYSTEM,
                    remark=remark or ""
                )
            
            # 更新 Redis
            redis_key = f"{self.CONFIG_PREFIX}{key}"
            await self.redis.set(redis_key, value)
            
            logger.info(f"配置已更新: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"设置配置失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除配置（软删除数据库记录，删除 Redis 缓存）
        """
        try:
            config = await SystemConfig.get_or_none(key=key, is_del=False)
            if config:
                config.is_del = True
                await config.save()
            
            redis_key = f"{self.CONFIG_PREFIX}{key}"
            await self.redis.delete(redis_key)
            
            logger.info(f"配置已删除: {key}")
            return True
        except Exception as e:
            logger.error(f"删除配置失败 {key}: {e}")
            return False
    
    async def get_by_group(self, group: str) -> Dict[str, str]:
        """
        获取指定分组的所有配置
        
        :param group: 配置分组
        :return: 配置字典 {key: value}
        """
        try:
            configs = await SystemConfig.filter(group=group, is_del=False).values("key", "value")
            return {cfg["key"]: cfg["value"] for cfg in configs}
        except Exception:
            # group 字段可能不存在
            return {}
    
    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """
        获取所有配置分组及其配置项
        """
        try:
            configs = await SystemConfig.filter(is_del=False).order_by("group", "key").values(
                "id", "key", "name", "value", "group", "type", "remark"
            )
        except Exception:
            # group 字段可能不存在，回退到不带 group 的查询
            configs = await SystemConfig.filter(is_del=False).order_by("key").values(
                "id", "key", "name", "value", "type", "remark"
            )
            # 为每个配置添加默认分组
            for cfg in configs:
                cfg["group"] = self._guess_group(cfg["key"])
        
        # 按分组整理
        groups = {}
        for cfg in configs:
            group = cfg.get("group") or self._guess_group(cfg["key"])
            if group not in groups:
                groups[group] = {
                    "group": group,
                    "label": self._get_group_label(group),
                    "configs": []
                }
            groups[group]["configs"].append(cfg)
        
        return list(groups.values())
    
    def _guess_group(self, key: str) -> str:
        """根据 key 前缀猜测分组"""
        if key.startswith("email_"):
            return ConfigGroup.EMAIL
        elif key.startswith("map_"):
            return ConfigGroup.MAP
        elif key.startswith("upload_"):
            return ConfigGroup.UPLOAD
        elif key.startswith("account_") or key.startswith("default_"):
            return ConfigGroup.ACCOUNT
        elif key in ("multi_login_allowed", "login_expire_minutes"):
            return ConfigGroup.SECURITY
        return ConfigGroup.SYSTEM
    
    def _get_group_label(self, group: str) -> str:
        """获取分组显示名称"""
        labels = {
            ConfigGroup.SYSTEM: "系统配置",
            ConfigGroup.EMAIL: "邮件配置",
            ConfigGroup.MAP: "地图配置",
            ConfigGroup.UPLOAD: "上传配置",
            ConfigGroup.SECURITY: "安全配置",
            ConfigGroup.ACCOUNT: "账户配置",
        }
        return labels.get(group, group)
    
    async def refresh_from_db(self):
        """
        从数据库刷新所有配置到 Redis
        """
        # 删除所有现有配置缓存
        keys = []
        async for key in self.redis.scan_iter(f"{self.CONFIG_PREFIX}*"):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)
        
        # 重新加载
        await self.load_all_to_redis()
        logger.info("配置已从数据库刷新")


# 全局配置服务实例（需要在应用启动时初始化）
_dynamic_config: Optional[DynamicConfigService] = None


def get_dynamic_config() -> Optional[DynamicConfigService]:
    """获取动态配置服务实例"""
    return _dynamic_config


def init_dynamic_config(redis: AsyncRedis) -> DynamicConfigService:
    """初始化动态配置服务"""
    global _dynamic_config
    _dynamic_config = DynamicConfigService(redis)
    return _dynamic_config
