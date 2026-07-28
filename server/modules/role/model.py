# _*_ coding : UTF-8 _*_
# @Time : 2025/08/17 19:10
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : role.py
# @Software : PyCharm
# @Comment : 角色模型 - 数据库 RBAC + 数据权限
from tortoise import fields

from core.common import DbBaseModel


class SystemRole(DbBaseModel):
    """
    角色表模型。

    权限管理说明：
    - 功能权限通过 SystemRolePermission 维护。
    - 数据权限通过 data_scope 和 SystemRoleDepartment 维护。
    """

    tenant = fields.ForeignKeyField(
        "system.SystemTenant",
        related_name="roles",
        null=True,
        description="所属租户",
        source_field="tenant_id",
    )

    department = fields.ForeignKeyField(
        "system.SystemDepartment",
        related_name="roles",
        null=True,
        description="所属部门",
        source_field="department_id",
    )
    """
    所属部门。
    - 表示角色所属的部门。
    - 如果为 null，则表示角色是全局角色。
    - 映射到数据库字段 department_id。
    """

    name = fields.CharField(
        max_length=255, description="角色名称", source_field="role_name"
    )
    """
    角色名称。
    - 允许重复，因为不同部门可能有相同的角色名称。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 role_name。
    """

    code = fields.CharField(
        max_length=255, description="角色编码", index=True, source_field="role_code"
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
        source_field="role_description",
    )
    """
    角色描述。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 role_description。
    """

    status = fields.SmallIntField(
        default=1, description="角色状态", Index=True, source_field="status"
    )
    """
    角色状态。
    - 1: 正常
    - 0: 禁用
    - 映射到数据库字段 status。
    """

    class Meta:
        app = "system"
        table = "system_role"
        table_description = "系统角色表"
        ordering = ["-updated_at"]


class SystemRolePermission(DbBaseModel):
    """
    角色权限关系表。

    菜单、按钮和接口权限通过该表维护。
    """

    role = fields.ForeignKeyField(
        "system.SystemRole",
        related_name="role_permissions",
        source_field="role_id",
        description="角色ID",
        on_delete=fields.CASCADE,
    )

    permission = fields.ForeignKeyField(
        "system.SystemPermission",
        related_name="role_permissions",
        source_field="permission_id",
        description="权限ID",
        on_delete=fields.CASCADE,
    )

    class Meta:
        app = "system"
        table = "system_role_permission"
        table_description = "角色权限关系表"
        ordering = ["-updated_at"]
        unique_together = (("role", "permission"),)


class SystemRoleDepartment(DbBaseModel):
    """角色自定义数据部门关系表。"""

    role = fields.ForeignKeyField(
        "system.SystemRole",
        related_name="role_departments",
        source_field="role_id",
        description="角色ID",
        on_delete=fields.CASCADE,
    )

    department = fields.ForeignKeyField(
        "system.SystemDepartment",
        related_name="role_departments",
        source_field="department_id",
        description="部门ID",
        on_delete=fields.CASCADE,
    )

    class Meta:
        app = "system"
        table = "system_role_department"
        table_description = "角色自定义数据部门关系表"
        ordering = ["-updated_at"]
        unique_together = (("role", "department"),)
