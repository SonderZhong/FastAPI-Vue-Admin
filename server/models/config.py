# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 00:09
# @UpdateTime : 2025/08/04 00:09
# @Author : sonder
# @File : config.py
# @Software : PyCharm
# @Comment : 本程序
from tortoise import fields

from models.common import BaseModel


class ConfigGroup:
    """配置分组常量"""
    SYSTEM = "system"       # 系统基础配置
    EMAIL = "email"         # 邮件配置
    MAP = "map"             # 地图配置
    UPLOAD = "upload"       # 上传配置
    SECURITY = "security"   # 安全配置
    ACCOUNT = "account"     # 账户配置


class SystemConfig(BaseModel):
    """
    系统配置模型
    """
    name = fields.CharField(
        max_length=100,
        description="配置名称",
        source_field="name"
    )
    """
    配置名称。
    - 最大长度为 100 个字符
    - 映射到数据库字段 name
    """
    key = fields.CharField(
        max_length=100,
        description="配置键名",
        source_field="key"
    )
    """
    配置键名。
    - 最大长度为 100 个字符
    - 映射到数据库字段 key
    """
    value = fields.TextField(
        description="配置值",
        source_field="value"
    )
    """
    配置值。
    - 使用 TextField 支持长文本
    - 映射到数据库字段 value
    """
    group = fields.CharField(
        max_length=50,
        default="system",
        null=True,
        description="配置分组",
        source_field="group_name"
    )
    """
    配置分组。
    - 用于区分不同类型的配置
    - 默认为 system
    - 可为空（兼容旧数据）
    """
    type = fields.BooleanField(
        default=False,
        description="系统内置",
        source_field="type"
    )
    """
    是否为系统内置
    - 默认为不是
    """
    remark = fields.TextField(
        null=True,
        description="备注",
        source_field="remark"
    )
    """
    备注信息。
    - 最大长度为 255 个字符
    - 可为空
    """

    class Meta:
        table = "system_config"
        table_description = "系统配置表"
