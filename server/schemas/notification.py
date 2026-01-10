# _*_ coding : UTF-8 _*_
# @Time : 2026/01/03 01:33
# @Author : sonder
# @File : notification.py
# @Comment : 系统通知表

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class NotificationInfo(DataBaseModel):
    """
    系统通知表信息模型
    """
    model_config = ConfigDict()
    title: str = Field(..., max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    type: int = Field(default=2, description="通知类型：0登录通知 1全局公告 2系统消息")
    scope: int = Field(default=0, description="通知范围：0全部 1指定部门 2指定用户")
    scope_ids: Optional[List[str]] = Field(default=None, description="范围ID列表（部门ID或用户ID）")
    status: int = Field(default=0, description="状态：0草稿 1已发布 2已撤回")
    priority: int = Field(default=0, description="优先级：0普通 1重要 2紧急")
    publish_time: Optional[str] = Field(default=None, description="发布时间")
    expire_time: Optional[str] = Field(default=None, description="过期时间")
    creator: Optional[str] = Field(default=None, description="创建者")


class CreateNotificationParams(BaseModel):
    """创建通知参数"""
    title: str = Field(..., max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    type: int = Field(default=2, description="通知类型：0登录通知 1全局公告 2系统消息")
    scope: int = Field(default=0, description="通知范围：0全部 1指定部门 2指定用户")
    scope_ids: List[str] = Field(default=[], description="范围ID列表（部门ID或用户ID）")
    priority: int = Field(default=0, description="优先级：0普通 1重要 2紧急")
    expire_time: Optional[str] = Field(default=None, description="过期时间")


class UpdateNotificationParams(BaseModel):
    """更新通知参数"""
    title: Optional[str] = Field(default=None, max_length=200, description="通知标题")
    content: Optional[str] = Field(default=None, description="通知内容")
    type: Optional[int] = Field(default=None, description="通知类型")
    scope: Optional[int] = Field(default=None, description="通知范围")
    scope_ids: Optional[List[str]] = Field(default=None, description="范围ID列表")
    priority: Optional[int] = Field(default=None, description="优先级")
    expire_time: Optional[str] = Field(default=None, description="过期时间")


class GetNotificationListResult(ListQueryResult):
    """
    获取系统通知表列表结果模型
    """
    result: List[NotificationInfo] = Field(default=[], description="系统通知表列表")


class GetNotificationInfoResponse(BaseResponse):
    """
    获取系统通知表详情响应模型
    """
    data: NotificationInfo = Field(default=None, description="系统通知表信息")


class GetNotificationListResponse(BaseResponse):
    """
    获取系统通知表列表响应模型
    """
    data: GetNotificationListResult = Field(default=None, description="响应数据")

