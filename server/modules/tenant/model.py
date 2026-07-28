# _*_ coding : UTF-8 _*_
# @Time : 2026/07/02 21:45
# @UpdateTime : 2026/07/02 21:45
# @Author : SonderZhong
# @File : model.py
# @Software : VSCode
# @Comment : 本程序用于租户数据表模型


import secrets
from tortoise import fields

from core.common import DbBaseModel


class SystemTenant(DbBaseModel):
    """租户表"""

    name = fields.CharField(
        max_length=100, description="租户名称", source_field="tenant_name"
    )
    code = fields.CharField(
        max_length=100, unique=True, description="租户编码", source_field="tenant_code"
    )
    status = fields.SmallIntField(
        default=1, description="租户状态（1启用，0禁用）", source_field="status"
    )
    invite_code = fields.CharField(
        max_length=32,
        null=True,
        unique=True,
        description="邀请码",
        source_field="invite_code",
    )
    allow_register = fields.BooleanField(
        default=False,
        description="是否允许通过邀请码注册",
        source_field="allow_register",
    )
    remark = fields.CharField(
        max_length=255, null=True, description="备注", source_field="remark"
    )

    @classmethod
    def generate_invite_code(cls) -> str:
        return secrets.token_hex(8).upper()

    class Meta:
        app = "system"
        table = "system_tenant"
        table_description = "系统租户表"
        ordering = ["-created_at"]
