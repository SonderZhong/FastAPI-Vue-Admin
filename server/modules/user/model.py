# _*_ coding : UTF-8 _*_
from tortoise import fields

from core.common import DbBaseModel


class SystemUser(DbBaseModel):
    """用户表 - 只存基础信息，不绑定租户/部门"""

    username = fields.CharField(
        max_length=255, description="用户名", source_field="username"
    )
    password = fields.CharField(
        max_length=255, description="密码", source_field="password"
    )
    email = fields.CharField(
        max_length=255, null=True, description="邮箱", source_field="email"
    )
    phone = fields.CharField(
        max_length=30, null=True, description="手机号", source_field="phone"
    )
    nickname = fields.CharField(
        max_length=255, null=True, description="昵称", source_field="nickname"
    )
    avatar = fields.CharField(
        max_length=512, null=True, description="头像", source_field="avatar"
    )
    gender = fields.SmallIntField(
        default=0, description="性别（0未知，1男，2女）", source_field="gender"
    )
    status = fields.SmallIntField(
        default=1, description="用户状态（1启用，0禁用）", source_field="status"
    )

    class Meta:
        app = "system"
        table = "system_user"
        table_description = "用户表"
        ordering = ["-updated_at"]


class SystemTenantUser(DbBaseModel):
    """租户-用户中间表 - 关联用户、租户、部门"""

    tenant = fields.ForeignKeyField(
        "system.SystemTenant",
        related_name="tenant_users",
        source_field="tenant_id",
        on_delete=fields.CASCADE,
        description="租户ID",
    )
    user = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="tenant_users",
        source_field="user_id",
        on_delete=fields.CASCADE,
        description="用户ID",
    )
    department = fields.ForeignKeyField(
        "system.SystemDepartment",
        related_name="tenant_users",
        source_field="department_id",
        on_delete=fields.SET_NULL,
        null=True,
        description="部门ID",
    )
    user_type = fields.SmallIntField(
        default=3,
        description="该租户下的角色类型（0租户超管，1管理员，2部门管理员，3普通用户）",
        source_field="user_type",
    )
    status = fields.SmallIntField(
        default=1, description="状态（1启用，0禁用）", source_field="status"
    )

    class Meta:
        app = "system"
        table = "system_tenant_user"
        table_description = "租户用户中间表"
        unique_together = (("tenant", "user"),)


class SystemUserRole(DbBaseModel):
    """用户角色中间表 - 租户维度"""

    tenant = fields.ForeignKeyField(
        "system.SystemTenant",
        related_name="tenant_user_roles",
        source_field="tenant_id",
        on_delete=fields.CASCADE,
        null=True,
        description="租户ID",
    )
    user = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="user_roles",
        source_field="user_id",
        on_delete=fields.CASCADE,
        null=True,
        description="用户ID",
    )
    role = fields.ForeignKeyField(
        "system.SystemRole",
        related_name="user_roles",
        source_field="role_id",
        on_delete=fields.CASCADE,
        null=True,
        description="角色ID",
    )

    class Meta:
        app = "system"
        table = "system_user_role"
        table_description = "用户角色中间表"
