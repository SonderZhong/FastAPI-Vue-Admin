# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 00:10
# @UpdateTime : 2025/08/04 00:10
# @Author : sonder
# @File : common.py
# @Software : PyCharm
# @Comment : 本程序

from tortoise import fields, models


class BaseModel(models.Model):
    """
    抽象模型，用于定义数据表的公共字段。
    """

    id = fields.UUIDField(pk=True, description="主键", autoincrement=True, source_field="id")
    """
    自增 UUID，作为主键。
    - 使用 UUIDField 生成唯一标识符。
    """

    is_del = fields.BooleanField(default=False, description="删除标志", source_field="is_del")
    """
    删除标志。
    - 1 代表存在，0 代表删除。
    - 默认为 1。
    """

    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间", null=True, source_field="created_at")
    """
    创建时间。
    - 自动设置为当前时间。
    - 允许为空（null=True）。
    """

    updated_at = fields.DatetimeField(auto_now=True, description="更新时间", null=True, source_field="updated_at")
    """
    更新时间。
    - 自动更新为当前时间。
    - 允许为空（null=True）。
    """

    class Meta:
        abstract = True  # 标记为抽象类，不会创建对应的数据库表
        ordering = ["-created_at"]  # 默认按创建时间倒序排序
        indexes = ("is_del",)  # 为 is_del 字段创建索引
