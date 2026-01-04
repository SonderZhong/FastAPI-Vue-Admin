# _*_ coding : UTF-8 _*_
# @Time : 2025/08/17 19:00
# @UpdateTime : 2025/08/17 19:00
# @Author : sonder
# @File : user.py
# @Software : PyCharm
# @Comment : 本程序
from tortoise import fields

from models.common import BaseModel


class SystemUser(BaseModel):
    """
    用户表模型。
    """

    username = fields.CharField(
        max_length=255,
        description="用户名",
        source_field="username"
    )
    """
    用户名。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 username。
    """

    password = fields.CharField(
        max_length=255,
        description="密码",
        source_field="password"
    )
    """
    密码。
    - 存储加密后的密码。
    - 最大长度为 255 个字符。
    - 映射到数据库字段 password。
    """

    email = fields.CharField(
        max_length=255,
        null=True,
        description="邮箱",
        source_field="email"
    )
    """
    邮箱。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 email。
    """

    phone = fields.CharField(
        max_length=30,
        null=True,
        description="手机号",
        source_field="phone"
    )
    """
    手机号。
    - 最大长度为 30 个字符。
    - 允许为空。
    - 映射到数据库字段 phone。
    """

    nickname = fields.CharField(
        max_length=255,
        null=True,
        description="昵称",
        source_field="nickname"
    )
    """
    昵称。
    - 最大长度为 255 个字符。
    - 允许为空。
    - 映射到数据库字段 nickname。
    """

    avatar = fields.CharField(
        max_length=512,
        null=True,
        description="头像",
        source_field="avatar"
    )
    """
    头像。
    - 最大长度为 512 个字符。
    - 允许为空。
    - 映射到数据库字段 avatar。
    """

    gender = fields.SmallIntField(
        default=0,
        description="性别（0未知，1男，2女）",
        source_field="gender"
    )
    """
    性别。
    - 0：未知
    - 1：男
    - 2：女
    - 默认为 0。
    - 映射到数据库字段 gender。
    """

    status = fields.SmallIntField(
        default=1,
        description="用户状态（1启用，0禁用）",
        source_field="status"
    )
    """
    用户状态。
    - 1：启用
    - 0：禁用
    - 默认为 1。
    - 映射到数据库字段 status。
    """

    user_type = fields.SmallIntField(
        default=3,
        description="用户身份标识（0超级管理员，1管理员，2部门管理员，3普通用户）",
        source_field="user_type"
    )
    """
    用户身份标识。
    - 0：超级管理员（最高权限，可管理所有资源）
    - 1：管理员（可管理多个部门和系统配置）
    - 2：部门管理员（可管理所属部门及下属部门）
    - 3：普通用户（只能查看和操作自己的数据）
    - 默认为 3（普通用户）。
    - 映射到数据库字段 user_type。
    """

    department = fields.ForeignKeyField(
        "system.SystemDepartment",
        related_name="users",
        null=True,
        description="所属部门",
        source_field="department_id"
    )
    """
    所属部门。
    - 外键关联到 SystemDepartment 表。
    - 如果为 null，则表示用户未分配部门。
    - 映射到数据库字段 department_id。
    """

    class Meta:
        table = "system_user"
        table_description = "用户表"
        ordering = ["-created_at"]


class SystemUserRole(BaseModel):
    """
    用户角色中间表。
    """

    user = fields.ForeignKeyField(
        "system.SystemUser",
        related_name="user_roles",
        source_field="user_id",
        description="用户ID",
        on_delete=fields.CASCADE,
        null=True,
        default=None
    )
    role = fields.ForeignKeyField(
        "system.SystemRole",
        related_name="user_roles",
        source_field="role_id",
        on_delete=fields.CASCADE,
        null=True,
        default=None
    )

    class Meta:
        table = "system_user_role"
        table_description = "用户角色中间表"
