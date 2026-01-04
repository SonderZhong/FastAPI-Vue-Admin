# _*_ coding : UTF-8 _*_
# @Time : 2025/08/10 16:14
# @UpdateTime : 2025/08/10 16:14
# @Author : sonder
# @File : department.py
# @Software : PyCharm
# @Comment : 本程序

from tortoise import fields

from models.common import BaseModel


class SystemDepartment(BaseModel):
    """
    部门模型
    """

    name = fields.CharField(
        max_length=50,
        description="部门名称",
        source_field="name"
    )
    """
    部门名称。
    - 最大长度为50字符
    - 映射到数据库字段name
    """
    parent_id = fields.CharField(
        max_length=50,
        description="上级部门ID",
        source_field="parent_id",
        null=True
    )
    """
    上级部门ID。
    - 映射到数据库字段parent_id
    - 允许为空
    """
    sort = fields.IntField(
        default=0,
        description="排序权重（0最高）",
        source_field="sort"
    )
    """
    排序权重。
    - 用于部门列表的排序，值越小越靠前。
    - 默认为 0。
    - 映射到数据库字段 sort。
    """

    phone = fields.CharField(
        max_length=30,
        null=True,
        description="部门电话",
        source_field="phone"
    )
    """
    部门电话。
    - 最大长度为 30 个字符。
    - 允许为空。
    - 映射到数据库字段 phone。
    """

    principal = fields.CharField(
        max_length=64,
        description="部门负责人",
        source_field="principal"
    )
    """
    部门负责人。
    - 最大长度为 64 个字符。
    - 映射到数据库字段 principal。
    """

    email = fields.CharField(
        max_length=128,
        null=True,
        description="部门邮箱",
        source_field="email"
    )
    """
    部门邮箱。
    - 最大长度为 128 个字符。
    - 允许为空。
    - 映射到数据库字段 email。
    """

    status = fields.SmallIntField(
        default=1,
        description="状态（0正常 1停用）",
        source_field="status"
    )
    """
    状态。
    - 1 表示正常，0 表示停用。
    - 默认为 1。
    - 映射到数据库字段 status。
    """

    remark = fields.CharField(
        max_length=255,
        null=True,
        description="备注信息",
        source_field="remark"
    )
    """
    备注信息。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 remark。
    """

    class Meta:
        table = "system_department"
        table_description = "系统部门表"
        ordering = ["sort", "-created_at"]
