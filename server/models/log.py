# _*_ coding : UTF-8 _*_
# @Time : 2025/08/18 01:50
# @UpdateTime : 2025/08/18 01:50
# @Author : sonder
# @File : log.py
# @Software : PyCharm
# @Comment : 本程序
from tortoise import fields

from models.common import BaseModel


class SystemLoginLog(BaseModel):
    """
    系统访问记录表模型。
    """

    user_id = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="login_logs",
        description="用户ID",
        source_field="user_id"
    )
    """
    用户ID。
    - 外键关联到 User 表。
    - 映射到数据库字段 user_id。
    """

    login_ip = fields.CharField(
        max_length=256,
        description="登录IP地址",
        source_field="login_ip"
    )
    """
    登录IP地址。
    - 最大长度为 50 个字符。
    - 映射到数据库字段 login_ip。
    """

    login_location = fields.CharField(
        max_length=255,
        null=True,
        description="登录地点",
        source_field="login_location"
    )
    """
    登录地点。
    - 根据 IP 地址解析的地理位置信息。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 login_location。
    """

    browser = fields.CharField(
        max_length=255,
        null=True,
        description="浏览器类型",
        source_field="browser"
    )
    """
    浏览器类型。
    - 记录用户登录时使用的浏览器类型。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 browser。
    """

    os = fields.CharField(
        max_length=255,
        null=True,
        description="操作系统",
        source_field="os"
    )
    """
    操作系统。
    - 记录用户登录时使用的操作系统。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 os。
    """

    status = fields.SmallIntField(
        default=1,
        description="登录状态（1成功，0失败）",
        source_field="status"
    )
    """
    登录状态。
    - 1：成功
    - 0：失败
    - 默认为 1。
    - 映射到数据库字段 status。
    """

    session_id = fields.CharField(
        max_length=36,
        null=True,
        description="会话ID",
        source_field="session_id"
    )
    """
    会话ID。
    - 记录用户登录时的会话ID。
    - 允许为空。
    - 映射到数据库字段 session_id。
    """

    class Meta:
        table = "system_login_log"
        table_description = "系统访问记录表"
        ordering = ["-created_at"]


class SystemOperationLog(BaseModel):
    """
    操作日志表模型。
    """

    operation_name = fields.CharField(
        max_length=255,
        description="操作名称",
        source_field="operation_name"
    )
    """
    操作名称。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 operation_name。
    """

    operation_type = fields.SmallIntField(
        description="操作类型（增删改查）",
        source_field="operation_type"
    )
    """
    操作类型。
    - 增、删、改、查等操作类型。
    - 最大长度为 50 个字符。
    - 映射到数据库字段 operation_type。
    """

    request_path = fields.TextField(
        description="请求路径",
        source_field="request_path"
    )
    """
    请求路径。
    - 记录用户请求的 API 路径。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 request_path。
    """

    request_method = fields.CharField(
        max_length=10,
        description="请求方法",
        source_field="request_method"
    )
    """
    请求方法。
    - 记录用户请求的 HTTP 方法（如 GET、POST、PUT、DELETE）。
    - 最大长度为 10 个字符。
    - 映射到数据库字段 request_method。
    """

    operator = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="operation_logs",
        null=True,
        description="操作人员",
        source_field="operator_id"
    )
    """
    操作人员。
    - 外键关联到 User 表。
    - 允许为空。
    - 映射到数据库字段 operator_id。
    """

    host = fields.CharField(
        max_length=50,
        description="主机地址",
        source_field="host"
    )
    """
    主机地址。
    - 记录用户请求的 IP 地址。
    - 最大长度为 50 个字符。
    - 映射到数据库字段 host。
    """

    location = fields.CharField(
        max_length=255,
        null=True,
        description="操作地点",
        source_field="location"
    )
    """
    操作地点。
    - 根据 IP 地址解析的地理位置信息。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 location。
    """

    user_agent = fields.TextField(
        null=True,
        description="用户请求头",
        source_field="user_agent"
    )
    """
    用户请求头。
    - 记录用户请求的 User-Agent 信息。
    - 允许为空。
    - 映射到数据库字段 user_agent。
    """

    browser = fields.CharField(
        max_length=255,
        null=True,
        description="浏览器类型",
        source_field="browser"
    )
    """
    浏览器类型。
    - 记录用户登录时使用的浏览器类型。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 browser。
    """

    os = fields.CharField(
        max_length=255,
        null=True,
        description="操作系统",
        source_field="os"
    )
    """
    操作系统。
    - 记录用户登录时使用的操作系统。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 os。
    """

    request_params = fields.TextField(
        null=True,
        description="请求参数",
        source_field="request_params"
    )
    """
    请求参数。
    - 记录用户请求的参数（任意格式，如字符串、JSON、XML 等）。
    - 允许为空。
    - 映射到数据库字段 request_params。
    """

    response_result = fields.TextField(
        null=True,
        description="返回结果",
        source_field="response_result"
    )
    """
    返回结果。
    - 记录操作的返回结果（任意格式，如字符串、JSON、XML 等）。
    - 允许为空。
    - 映射到数据库字段 response_result。
    """

    status = fields.SmallIntField(
        default=1,
        description="操作状态（1成功，0失败）",
        source_field="status"
    )
    """
    操作状态。
    - 1：成功
    - 0：失败
    - 默认为 1。
    - 映射到数据库字段 status。
    """

    cost_time = fields.FloatField(
        default=0,
        description="消耗时间（毫秒）",
        source_field="cost_time"
    )
    """
    消耗时间。
    - 记录操作消耗的时间（单位：毫秒）。
    - 默认为 0。
    - 映射到数据库字段 cost_time。
    """

    class Meta:
        table = "system_operation_log"
        table_description = "操作日志表"
        ordering = ["-created_at"]
