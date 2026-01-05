# _*_ coding : UTF-8 _*_
# @Time : 2025/08/01 00:14
# @Author : sonder
# @File : config.py
# @Software : PyCharm
# @Comment : 统一使用config.yaml配置文件的配置加载器，适配FastAPI+Tortoise-ORM
import datetime
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """
    基础配置类，所有配置类的父类
    提供从YAML字典初始化配置的通用方法，确保配置加载的一致性
    """

    @classmethod
    def from_yaml(cls, yaml_data: Dict[str, Any]) -> "BaseConfig":
        """
        从YAML解析的字典数据初始化配置实例

        :param yaml_data: YAML文件中解析出的字典
        :return: 配置类实例
        """
        return cls.model_validate(yaml_data)

    """配置基类，提供转换为字典的方法"""


class AppSettings(BaseConfig):
    """
    应用核心配置类
    管理应用的基础运行参数，如环境标识、端口、前缀等
    """
    env: str = 'dev'
    """
    应用运行环境标识
    - 'dev'：开发环境（默认），启用调试、自动重载等特性
    - 'prod'：生产环境，关闭调试、优化性能
    影响应用的行为模式和配置加载策略
    """

    name: str = 'FastAPI-Vue-Admin'
    """
    应用名称
    用于接口文档标题、日志输出、服务标识等场景
    建议设置为业务相关名称（如"用户管理系统"）
    """

    api_prefix: str = '/dev-api'
    """
    API接口的统一路径前缀
    - 开发环境：通常包含环境标识（如/dev-api），便于区分
    - 生产环境：建议简化（如/api），更友好的URL格式
    所有接口路径都会自动添加该前缀
    """

    api_status_enabled: bool = True
    """
    是否启用接口状态监控功能
    - True：启用（默认），提供/health等监控接口，便于运维检查服务状态
    - False：禁用，生产环境可关闭以减少接口暴露面
    """

    host: str = '0.0.0.0'
    """
    应用绑定的主机地址
    - '0.0.0.0'：监听所有网络接口（默认，适合服务器部署）
    - '127.0.0.1'：仅本地可访问（适合本地开发调试）
    生产环境需根据网络策略配置，确保安全性
    """

    port: int = 9090
    """
    应用监听的端口号
    - 范围：1-65535，需确保端口未被占用且防火墙允许访问
    - 开发环境：建议使用非80/443等常用端口（避免冲突）
    - 生产环境：可通过反向代理映射到80/443端口
    """

    version: str = '1.0.0'
    """
    应用版本号
    遵循语义化版本规范（主版本.次版本.修订号）
    用于接口文档、日志输出、版本控制等场景
    """

    reload: bool = True
    """
    是否启用代码自动重载
    - True：启用（默认），代码修改后自动重启应用（开发效率高）
    - False：禁用，生产环境必须关闭（避免性能损耗）
    仅对开发环境有效
    """

    ip_location_enabled: bool = True
    """
    是否启用IP地址地理位置查询功能
    - True：启用（默认），通过地图服务API获取用户所在城市
    - False：禁用，适合对隐私敏感或无地理位置需求的场景
    启用会增加API调用耗时，生产环境需评估性能影响
    """

    multi_login_allowed: bool = True
    """
    是否允许同一用户同时在多个设备登录
    - True：允许（默认），用户体验友好，适合多数场景
    - False：禁止，新登录会踢掉旧登录（安全性更高）
    生产环境建议根据业务场景选择，金融类应用通常禁用
    """

    init_database: bool = True
    """
    是否初始化数据库
    - True：初始化（默认），首次启动时创建数据库表结构
    - False：不初始化，仅当数据库表结构不存在时创建
    """


class JwtSettings(BaseConfig):
    """
    JWT认证配置类
    管理用户身份令牌的生成、验证参数
    """
    secret_key: str = 'FastAPI-Vue-Admin'
    """
    JWT令牌签名密钥（敏感信息！必须设置）
    用于加密和解密令牌，确保令牌不被篡改
    - 开发环境：可使用测试密钥（如示例）
    - 生产环境：必须使用强随机密钥（建议32位以上）
    生成方式：openssl rand -hex 32
    """

    algorithm: str = 'HS256'
    """
    JWT签名算法
    - 对称加密：HS256（默认）、HS384、HS512（适合单机部署）
    - 非对称加密：RS256、RS384等（适合分布式系统，安全性更高）
    生产环境建议根据部署架构选择合适算法
    """

    salt: str = 'FastAPI-Vue-Admin'
    """
    JWT加盐值
    与secret_key配合使用，增强签名安全性，抵御彩虹表攻击
    建议使用随机字符串，与secret_key不同
    """

    expire_minutes: int = 1440
    """
    JWT令牌的有效期（单位：分钟）
    - 开发环境：建议设长（如1440=24小时，方便调试）
    - 生产环境：建议设短（如60=1小时，降低泄露风险）
    过期后用户需重新登录
    """

    redis_expire_minutes: int = 30
    """
    令牌在Redis中的缓存有效期（单位：分钟）
    用于实现令牌黑名单（如主动登出功能）
    建议小于expire_minutes，减少Redis存储压力
    """


class DatabaseSettings(BaseConfig):
    """
    数据库配置类（单一数据库连接）
    管理数据库实例的连接参数，适配Tortoise-ORM
    """
    engine: str = "mysql"
    """
    数据库引擎类型
    指定连接的数据库类型，支持：
    - 'mysql'：MySQL数据库（默认）
    - 'postgresql'：PostgreSQL数据库
    - 'sqlite'：SQLite数据库（文件型，无需服务）
    - 'oracle'：Oracle数据库
    不同引擎对应不同的驱动和连接参数
    """

    host: str = "127.0.0.1"
    """
    数据库主机地址
    - 本地数据库：'localhost'或'127.0.0.1'（默认）
    - 远程数据库：服务器IP地址或域名（如db.prod.com）
    - SQLite：无需设置（忽略此参数）
    """

    port: int = 3306
    """
    数据库端口号
    - MySQL：3306（默认）
    - PostgreSQL：5432
    - Oracle：1521
    - SQLite：无需设置（自动忽略）
    需与数据库服务的配置一致，否则无法连接
    """

    username: str = 'root'
    """
    数据库登录用户名
    - 开发环境：通常使用root（权限高，方便调试）
    - 生产环境：必须使用最小权限用户（仅授予必要操作权限）
    SQLite无需设置（文件权限由操作系统控制）
    """

    password: SecretStr = SecretStr('root')
    """
    数据库登录密码（敏感信息）
    - 开发环境：可使用简单密码（如root）
    - 生产环境：必须使用强密码（含大小写、数字、特殊字符）
    """

    database: str = 'FVA'
    """
    数据库名称/路径
    - 关系型数据库（MySQL/PostgreSQL）：数据库名称（如FVA_prod）
    - SQLite：数据库文件路径（如./data/app.db）
    需确保数据库已创建（SQLite会自动创建文件）
    """

    pool_size: int = 10
    """
    数据库连接池大小
    控制并发连接数：
    - 开发环境：5-10（足够调试）
    - 生产环境：根据并发量调整（10-50，不宜过大）
    连接池过大会占用过多数据库资源，过小会导致连接等待
    """

    pool_timeout: int = 30
    """
    连接池获取连接的超时时间（单位：秒）
    超过此时长未获取到连接会抛出异常
    建议设置为30秒，避免请求无限等待
    """

    echo: bool = False
    """
    是否打印SQL执行日志
    - True：打印所有SQL语句及参数（开发调试用）
    - False：不打印（生产环境必须关闭，避免性能损耗和数据泄露）
    """

    charset: str = "utf8mb4"
    """
    数据库字符集
    - MySQL：建议使用utf8mb4（支持emoji等4字节字符）
    - PostgreSQL：通常使用UTF8
    """

    timezone: str = "Asia/Shanghai"
    """
    数据库时区设置
    影响时间字段的存储和查询
    默认为'Asia/Shanghai'（中国标准时间）
    需与应用服务器时区保持一致，避免时间偏移
    """

    @field_validator('engine')
    def validate_engine(cls, v):
        """
        验证数据库引擎合法性

        :param v: 引擎名称
        :return: 验证后的引擎名称
        :raises ValueError: 当引擎不被支持时抛出
        """
        supported = ['mysql', 'postgresql', 'sqlite']
        if v not in supported:
            raise ValueError(f"不支持的数据库引擎: {v}，支持的引擎: {supported}")
        return v


class RedisSettings(BaseConfig):
    """
    Redis配置类（单一Redis连接）
    管理缓存、会话等存储
    """
    host: str = '127.0.0.1'
    """
    Redis主机地址
    - 本地：'127.0.0.1'（默认）
    - 远程：服务器IP地址或域名
    """

    port: int = 6379
    """
    Redis端口号
    默认6379（Redis标准端口）
    """

    password: SecretStr = SecretStr('')
    """
    Redis登录密码（敏感信息）
    - 开发环境：可留空（关闭认证）
    - 生产环境：必须设置强密码
    """

    database: int = 1
    """
    Redis数据库索引（0-15，默认2）
    - 单节点模式：有效，用于逻辑隔离不同业务数据（如0存会话、2存缓存）
    - 集群模式：通常无效（集群不支持select命令）
    建议不同业务使用不同索引，避免key冲突
    """

    max_connections: int = 10
    """
    Redis连接池最大连接数
    需根据并发量调整，建议不超过Redis服务器的maxclients配置
    过大可能导致Redis拒绝连接
    """

    socket_timeout: int = 5
    """
    Redis连接超时时间（单位：秒）
    超过此时长未建立连接会抛出异常
    建议设置为5秒，避免请求长时间阻塞
    """

    retry_on_timeout: bool = True
    """
    超时是否自动重试
    - True：超时后自动重试一次（默认，提高可用性）
    - False：超时后直接抛出异常
    适合对可用性要求高的场景，需注意重试可能导致重复操作
    """


class UploadSettings(BaseConfig):
    """
    文件上传存储配置类
    支持本地存储和主流云端存储（阿里云OSS、腾讯云COS等）
    """
    storage_type: str = 'local'
    """
    存储类型，指定文件存储位置
    - 'local'：本地文件系统（默认，适合开发和小规模部署）
    - 'aliyun_oss'：阿里云OSS
    - 'tencent_cos'：腾讯云COS
    - 'aws_s3'：AWS S3
    生产环境建议使用云端存储，提供高可用和扩展性
    """

    allowed_extensions: List[str] = [
        'bmp', 'gif', 'jpg', 'jpeg', 'png', 'webp',
        'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf', 'txt', 'html', 'htm',
        'rar', 'zip', '7z', 'gz', 'bz2',
        'mp4', 'avi', 'mov', 'flv', 'mkv',
        'mp3', 'wav', 'flac'
    ]
    """
    允许上传的文件扩展名列表（不含前缀点）
    用于文件类型校验，防止恶意文件上传
    可根据业务需求增删（如禁止.exe等可执行文件）
    """

    max_file_size: int = 100
    """
    最大文件大小限制（单位：MB）
    默认100MB，需根据业务场景调整：
    - 图片：通常5-10MB
    - 视频：可放宽至100-500MB
    过大的文件建议使用分片上传
    """

    upload_node: str = 'node-A'
    """
    上传节点标识
    分布式部署时区分存储节点
    多机部署时，不同节点使用不同标识（如node-A、node-B）
    用于文件路径生成，避免多节点文件冲突
    """

    local_upload_path: str = 'data/local_uploads'
    """
    本地存储上传文件的根目录（storage_type=local时生效）
    建议使用绝对路径（如/var/app/uploads）
    需确保应用有读写权限，初始化时会自动创建目录
    """

    local_download_path: str = 'data/local_downloads'
    """
    本地存储下载文件的根目录（storage_type=local时生效）
    用于存储从云端同步或生成的下载文件
    """

    local_url_prefix: str = '/uploads'
    """
    本地存储文件的访问URL前缀（storage_type=local时生效）
    示例：前缀为/uploads时，文件实际访问路径为/uploads/2023/10/file.jpg
    需与Web框架的静态文件路由配置一致
    """

    cloud_access_key: Optional[str] = None
    """
    云端存储访问密钥AK（Access Key）
    用于API身份认证，需在云厂商控制台创建（如阿里云AccessKey）
    生产环境需遵循最小权限原则，仅授予上传/下载权限
    """

    cloud_secret_key: Optional[SecretStr] = None
    """
    云端存储访问密钥SK（Secret Key，敏感信息）
    与AK配对使用，用于签名API请求
    必须严格保密，泄露会导致存储资源被滥用
    """

    cloud_endpoint: Optional[str] = None
    """
    云端存储地域节点Endpoint
    不同云厂商/地域的Endpoint不同，例如：
    - 阿里云OSS（北京）：oss-cn-beijing.aliyuncs.com
    - 腾讯云COS（上海）：cos.ap-shanghai.myqcloud.com
    需从云厂商文档获取对应地域的Endpoint
    """

    cloud_timeout: int = 30
    """
    云端存储API请求超时时间（单位：秒）
    上传大文件时建议延长（如60秒）
    """

    cloud_bucket: Optional[str] = None
    """
    云端存储桶名称（Bucket）
    需提前在云厂商控制台创建，用于组织文件存储
    命名需符合云厂商规范（如阿里云Bucket名称全局唯一）
    """

    cloud_path_prefix: str = 'uploads/'
    """
    云端存储文件的路径前缀
    用于在Bucket内区分不同业务文件（如user_avatars/、logs/）
    建议以斜杠结尾（如uploads/），避免路径拼接问题
    """

    cloud_domain: Optional[str] = None
    """
    云端文件访问的自定义域名（可选）
    通常绑定CDN加速域名，例如https://cdn.yourdomain.com
    不设置则使用云厂商默认域名（如https://bucket.endpoint）
    """

    def __init__(self, **data):
        super().__init__(**data)
        if self.storage_type == 'local':
            self._ensure_local_dirs()

    def _ensure_local_dirs(self):
        """确保本地存储目录存在，不存在则自动创建"""
        os.makedirs(self.local_upload_path, exist_ok=True)
        os.makedirs(self.local_download_path, exist_ok=True)

    def get_file_url(self, file_key: str) -> str:
        """
        生成文件访问URL

        :param file_key: 文件唯一标识（含相对路径，如2023/10/avatar.jpg）
        :return: 可直接访问的URL字符串
        """
        if self.storage_type == 'local':
            return f"{self.local_url_prefix}/{file_key}"
        elif self.storage_type in ['aliyun_oss', 'tencent_cos', 'aws_s3']:
            if self.cloud_domain:
                return f"{self.cloud_domain}/{self.cloud_path_prefix}{file_key}"
            return f"https://{self.cloud_bucket}.{self.cloud_endpoint}/{self.cloud_path_prefix}{file_key}"
        raise ValueError(f"不支持的存储类型: {self.storage_type}")

    def get_storage_path(self, file_key: str) -> str:
        """
        获取文件实际存储路径

        :param file_key: 文件唯一标识
        :return: 本地路径（绝对路径）或云端key（完整路径）
        """
        return os.path.join(self.local_upload_path, file_key) if self.storage_type == 'local' \
            else f"{self.cloud_path_prefix}{file_key}"


class EmailSettings(BaseConfig):
    """
    邮件服务配置类
    管理邮件发送相关参数，用于发送通知、验证码等
    """
    username: str = ''
    """
    邮件发送账号（SMTP用户名）
    通常为完整邮箱地址（如notify@yourdomain.com）
    """

    password: SecretStr = SecretStr('')
    """
    邮件发送密码（敏感信息）
    - 多数邮箱（如QQ、163）使用SMTP授权码而非登录密码
    - 需在邮箱设置中开启SMTP服务并获取授权码
    """

    host: str = 'smtp.qq.com'
    """
    SMTP服务器地址
    不同邮箱服务商的地址不同：
    - QQ邮箱：smtp.qq.com
    - 163邮箱：smtp.163.com
    - 企业微信：smtp.exmail.qq.com
    """

    port: int = 465
    """
    SMTP服务器端口
    - 465：SSL加密端口（推荐，默认）
    - 587：TLS加密端口
    需与邮箱服务商的SMTP端口一致
    """

    from_addr: str = ''
    """
    发件人地址（显示的邮箱地址）
    通常与username一致，需符合邮箱服务商的规范
    示例："系统通知" <notify@yourdomain.com>
    """


class MapSettings(BaseConfig):
    """
    地图服务配置类
    管理地图API相关参数，用于IP定位、地理编码等功能
    """
    ak: str = ''
    """
    地图服务访问密钥AK（Access Key）
    需在地图服务商控制台创建应用后获取：
    - 百度地图：控制台-应用管理-创建应用-获取AK
    - 高德地图：控制台-应用管理-创建应用-获取Key
    """

    sk: SecretStr = SecretStr('')
    """
    地图服务安全密钥SK（Secret Key，敏感信息）
    部分接口（如IP定位）需要SK进行签名验证
    与AK配对使用，需从地图服务商控制台获取
    """

    provider: str = 'baidu'
    """
    地图服务提供商
    - 'baidu'：百度地图（默认）
    - 'amap'：高德地图
    不同提供商的API接口和参数不同，需对应调整调用逻辑
    """


class ConfigLoader:
    """
    配置加载器（核心类）
    统一使用config.yaml配置文件，简化配置管理
    """

    def __init__(self):
        self.config = self._load_yaml_file()  # 加载YAML配置文件

    def _load_yaml_file(self) -> Dict[str, Any]:
        """
        加载config.yaml配置文件

        :return: 配置字典
        :raises FileNotFoundError: 当配置文件不存在时抛出
        """
        # 获取项目根目录（server目录）
        # 当前文件在 server/utils/config.py，所以需要向上两级
        current_file = Path(__file__)
        project_root = current_file.parent.parent
        config_path = project_root / "config.yaml"

        # 加载配置文件（必须存在且为文件）
        if not config_path.exists() or not config_path.is_file():
            raise FileNotFoundError(f"配置文件不存在或不是有效文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        return config

    @lru_cache(maxsize=None)
    def app(self) -> AppSettings:
        """获取应用核心配置实例"""
        return AppSettings.from_yaml(self.config.get('app', {}))

    @lru_cache(maxsize=None)
    def jwt(self) -> JwtSettings:
        """获取JWT认证配置实例"""
        return JwtSettings.from_yaml(self.config.get('jwt', {}))

    @lru_cache(maxsize=None)
    def database(self) -> DatabaseSettings:
        """获取数据库配置实例"""
        db_data = self.config.get('database', {})
        return DatabaseSettings.from_yaml(db_data)

    @lru_cache(maxsize=None)
    def redis(self) -> RedisSettings:
        """获取Redis配置实例"""
        redis_data = self.config.get('redis', {})
        return RedisSettings.from_yaml(redis_data)

    @lru_cache(maxsize=None)
    def upload(self) -> UploadSettings:
        """获取文件上传配置实例"""
        return UploadSettings.from_yaml(self.config.get('upload', {}))

    @lru_cache(maxsize=None)
    def email(self) -> EmailSettings:
        """获取邮件服务配置实例"""
        return EmailSettings.from_yaml(self.config.get('email', {}))

    @lru_cache(maxsize=None)
    def map(self) -> MapSettings:
        """获取地图服务配置实例"""
        return MapSettings.from_yaml(self.config.get('map', {}))


    def to_dict(self) -> Dict[str, Any]:
        """返回清洗后的配置字典（用于导出YAML）"""
        return _clean_config_data(self.config)

    def export_to_yaml(self, file_path: str):
        """导出配置为YAML文件"""
        export_config_to_yaml(self.to_dict(), file_path)

    def _update_nested_dict(self, target: Dict, key_path: List[str], value: Any) -> None:
        """
        递归更新嵌套字典中的值

        :param target: 目标字典
        :param key_path: 键路径列表（如 ["database", "nodes", "0", "host"]）
        :param value: 要设置的新值
        """
        if len(key_path) == 1:
            # 处理列表索引（如 "nodes.0" 中的 "0"）
            key = key_path[0]
            if isinstance(target, list) and key.isdigit():
                key = int(key)
            target[key] = value
            return

        # 递归处理嵌套结构
        current_key = key_path[0]
        # 处理列表索引
        if isinstance(target, list) and current_key.isdigit():
            current_key = int(current_key)

        # 确保中间节点存在
        if current_key not in target:
            # 判断下一个键是否为列表索引
            next_key = key_path[1]
            target[current_key] = [] if next_key.isdigit() else {}

        self._update_nested_dict(target[current_key], key_path[1:], value)

    def set_config_value(self, key: str, value: Any) -> None:
        """
        动态修改配置值

        :param key: 配置键（支持点分隔符，如 "database.nodes.0.host"）
        :param value: 新值
        """
        # 1. 解析键路径（如 "database.nodes.0.host" -> ["database", "nodes", "0", "host"]）
        key_path = key.split(".")
        if not key_path:
            raise ValueError("配置键不能为空")

        # 2. 更新内存中的 config（原始配置字典）
        self._update_nested_dict(self.config, key_path, value)

        # 3. 清除缓存的配置模型（使修改立即生效）
        for method in [self.app, self.jwt, self.database, self.redis, self.upload, self.email, self.map]:
            method.cache_clear()


def _clean_config_data(data: Any) -> Any:
    """
    递归清洗配置数据，将Pydantic模型转换为纯字典，移除内部字段

    :param data: 原始配置数据（可能包含Pydantic模型、列表、字典等）
    :return: 清洗后的纯数据结构
    """
    # 处理Pydantic模型（判断是否有model_dump方法）
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    # 处理列表
    if isinstance(data, list):
        return [_clean_config_data(item) for item in data]

    # 处理字典
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # 过滤Pydantic内部字段（以__开头的字段）
            if key.startswith("__"):
                continue
            # 处理敏感信息
            # if isinstance(value, SecretStr):
            #     cleaned[key] = "***PROTECTED***"  # 敏感信息占位符
            # else:
            cleaned[key] = _clean_config_data(value)
        return cleaned

    # 其他基础类型直接返回
    return data


def export_config_to_yaml(
        config: Dict[str, Any],
        file_path: str,
        include_comments: bool = True
) -> None:
    """
    将清洗后的配置导出为带注释的YAML文件（符合预期格式）

    :param config: 清洗后的配置字典（通过config.merged_config获取）
    :param file_path: 导出路径
    :param include_comments: 是否添加注释
    """
    # 第一步：清洗配置数据（移除Pydantic元信息）
    cleaned_data = _clean_config_data(config)

    # 第二步：构建带注释的YAML内容
    content: List[str] = []

    # 添加头部注释
    if include_comments:
        content.extend([
            "# 自动生成的配置文件",
            f"# 生成时间: {datetime.datetime.now().isoformat()}",
            "# 注意: 敏感信息已替换为占位符",
            ""
        ])

    # 按模块添加配置（带结构化注释）
    modules = [
        ("app", "应用核心配置"),
        ("jwt", "JWT认证配置"),
        ("database", "数据库配置"),
        ("redis", "Redis配置"),
        ("upload", "文件上传配置"),
        ("email", "邮件服务配置"),
        ("map", "地图服务配置"),
        ("elasticsearch", "Elasticsearch配置")
    ]

    for module, desc in modules:
        if module not in cleaned_data:
            continue

        # 添加模块注释
        content.extend([
            f"# {desc}",
            f"{module}:"
        ])

        # 处理数据库节点的特殊注释（最复杂的嵌套结构）
        if module == "database" and "nodes" in cleaned_data[module]:
            content.append("  # 数据库全局配置")
            for key, value in cleaned_data[module].items():
                if key == "nodes":
                    continue  # 节点单独处理
                content.append(f"  {key}: {value}")

            # 处理数据库节点列表
            content.extend([
                "  # 数据库连接节点列表",
                "  nodes:"
            ])
            for node in cleaned_data[module]["nodes"]:
                content.extend([
                    f"    - # 节点: {node['alias']}（{node['engine']}）",
                    f"      alias: {node['alias']!r}",
                    f"      engine: {node['engine']!r}",
                    f"      host: {node['host']!r}",
                    f"      port: {node['port']}",
                    f"      username: {node['username']!r}",
                    f"      password: {node['password']!r}",
                    f"      database: {node['database']!r}",
                    f"      pool_size: {node['pool_size']}",
                    f"      pool_timeout: {node['pool_timeout']}",
                    f"      echo: {node['echo']}",
                    "      extra_options:"
                ])
                # 处理数据库额外参数
                for opt_key, opt_val in node["extra_options"].items():
                    content.append(f"        {opt_key}: {opt_val!r}")
                content.append("")  # 节点间空行

        # 处理Redis集群节点
        elif module == "redis" and "cluster_nodes" in cleaned_data[module]:
            content.append("  # Redis全局配置")
            for key, value in cleaned_data[module].items():
                if key == "cluster_nodes":
                    continue  # 集群节点单独处理
                content.append(f"  {key}: {value}")

            # 处理Redis集群节点
            content.extend([
                "  # Redis集群节点（仅cluster_mode=true时生效）",
                "  cluster_nodes:"
            ])
            for node in cleaned_data[module]["cluster_nodes"]:
                content.extend([
                    f"    - host: {node['host']!r}",
                    f"      port: {node['port']}"
                ])
            content.append("")

        # 其他普通模块
        else:
            module_data = cleaned_data[module]
            for key, value in module_data.items():
                # 列表类型单独处理（如upload.allowed_extensions）
                if isinstance(value, list):
                    content.append(f"  {key}:")
                    for item in value:
                        content.append(f"    - {item!r}")
                else:
                    content.append(f"  {key}: {value!r}" if isinstance(value, str) else f"  {key}: {value}")
            content.append("")  # 模块间空行

    # 写入文件
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"配置已导出至: {file_path}")


# 全局配置实例（项目中直接导入使用）
config = ConfigLoader()
