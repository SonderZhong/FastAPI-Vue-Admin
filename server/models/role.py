# _*_ coding : UTF-8 _*_
# @Time : 2025/08/17 19:10
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : role.py
# @Software : PyCharm
# @Comment : 角色模型 - 权限管理已迁移至 Casbin
from tortoise import fields

from models.common import BaseModel


class SystemRole(BaseModel):
    """
    角色表模型。
    
    权限管理说明（Casbin 方案C）：
    - 角色权限完全由 Casbin 管理，不再使用中间表
    - 菜单/按钮权限: p, role_code, permission_id, menu|button
    - API权限: p, role_code, /api/path/*, GET|POST|...
    - 用户-角色关联: g, user_id, role_code
    """

    name = fields.CharField(
        max_length=255,
        description="角色名称",
        source_field="role_name"
    )
    """
    角色名称。
    - 允许重复，因为不同部门可能有相同的角色名称。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 role_name。
    """

    code = fields.CharField(
        max_length=255,
        unique=True,
        description="角色编码",
        source_field="role_code"
    )
    """
    角色编码。
    - 用于系统内部识别角色。
    - 必须唯一。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 role_code。
    """

    description = fields.CharField(
        max_length=255,
        null=True,
        description="角色描述",
        source_field="role_description"
    )
    """
    角色描述。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 role_description。
    """

    status = fields.SmallIntField(
        default=1,
        description="角色状态",
        source_field="status"
    )
    """
    角色状态。
    - 1: 正常
    - 0: 禁用
    - 映射到数据库字段 status。
    """

    department = fields.ForeignKeyField(
        "system.SystemDepartment",
        related_name="roles",
        null=True,
        description="所属部门",
        source_field="department_id"
    )
    """
    所属部门。
    - 表示角色所属的部门。
    - 如果为 null，则表示角色是全局角色。
    - 映射到数据库字段 department_id。
    """

    class Meta:
        table = "system_role"
        table_description = "系统角色表"
        ordering = ["-created_at"]
