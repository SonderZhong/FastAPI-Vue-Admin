# _*_ coding : UTF-8 _*_
# @Time : 2026/07/02 23:13
# @UpdateTime : 2026/07/02 23:13
# @Author : SonderZhong
# @File : model.py
# @Software : VSCode
# @Comment : 本程序用于


from tortoise import fields
from core.common import DbBaseModel


class SystemDictionary(DbBaseModel):
    """
    数据字典表
    """

    dict_name = fields.CharField(
        max_length=100, null=False, description="字典名称", source_field="dict_name"
    )
    """
    字典名称
    """
    dict_code = fields.CharField(
        max_length=100,
        null=False,
        unique=True,
        description="字典编码",
        source_field="dict_code",
    )
    """
    字典编码
    """
    status = fields.IntField(
        null=False, default=1, description="状态（1启用，0禁用）", source_field="status"
    )
    """
    状态（1启用，0禁用）
    """
    sort = fields.IntField(
        null=False, default=0, description="排序（数字越小越靠前）", source_field="sort"
    )
    """
    排序（数字越小越靠前）
    """
    remark = fields.TextField(null=True, description="备注", source_field="remark")
    """
    备注
    """

    class Meta:
        app = "system"
        table = "system_dictionary"
        table_description = "数据字典表"
        ordering = ["sort", "-created_at"]
