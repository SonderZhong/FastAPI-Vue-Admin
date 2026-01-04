# _*_ coding : UTF-8 _*_
# @Time : 2025/12/28
# @Author : sonder
# @File : notification.py
# @Comment : 通知模型

from enum import IntEnum
from tortoise import fields
from models.common import BaseModel


class NotificationType(IntEnum):
    """通知类型"""
    LOGIN = 0       # 登录通知
    ANNOUNCEMENT = 1  # 全局公告
    MESSAGE = 2     # 系统消息


class NotificationScope(IntEnum):
    """通知范围"""
    ALL = 0         # 全部用户
    DEPARTMENT = 1  # 指定部门
    USER = 2        # 指定用户


class NotificationStatus(IntEnum):
    """通知状态"""
    DRAFT = 0       # 草稿
    PUBLISHED = 1   # 已发布
    REVOKED = 2     # 已撤回


class SystemNotification(BaseModel):
    """系统通知表"""
    
    title = fields.CharField(max_length=200, description="通知标题")
    content = fields.TextField(description="通知内容")
    type = fields.SmallIntField(default=2, description="通知类型：0登录通知 1全局公告 2系统消息")
    scope = fields.SmallIntField(default=0, description="通知范围：0全部 1指定部门 2指定用户")
    scope_ids = fields.JSONField(null=True, description="范围ID列表（部门ID或用户ID）")
    status = fields.SmallIntField(default=0, description="状态：0草稿 1已发布 2已撤回")
    priority = fields.SmallIntField(default=0, description="优先级：0普通 1重要 2紧急")
    publish_time = fields.DatetimeField(null=True, description="发布时间")
    expire_time = fields.DatetimeField(null=True, description="过期时间")
    creator = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="created_notifications",
        on_delete=fields.SET_NULL,
        null=True,
        description="创建者"
    )
    
    class Meta:
        table = "system_notification"
        table_description = "系统通知表"
        ordering = ["-created_at"]


class UserNotification(BaseModel):
    """用户通知关联表（记录用户已读状态）"""
    
    notification = fields.ForeignKeyField(
        "system.SystemNotification",
        related_name="user_notifications",
        on_delete=fields.CASCADE,
        description="通知"
    )
    user = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="notifications",
        on_delete=fields.CASCADE,
        description="用户"
    )
    is_read = fields.BooleanField(default=False, description="是否已读")
    read_time = fields.DatetimeField(null=True, description="阅读时间")
    
    class Meta:
        table = "user_notification"
        table_description = "用户通知关联表"
        unique_together = [("notification", "user")]
        ordering = ["-created_at"]
