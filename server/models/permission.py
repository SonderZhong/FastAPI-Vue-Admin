# _*_ coding : UTF-8 _*_
# @Time : 2025/08/17 19:13
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : permission.py
# @Software : PyCharm
# @Comment : 权限模型 - 支持菜单、按钮、接口三种类型
from tortoise import fields

from models.common import BaseModel


class PermissionType:
    """权限类型常量"""
    MENU = 0      # 菜单
    BUTTON = 1    # 按钮
    API = 2       # 接口


class SystemPermission(BaseModel):
    """
    权限模型
    支持三种类型：菜单(0)、按钮(1)、接口(2)
    """
    menu_type = fields.SmallIntField(
        default=0,
        description="权限类型（0菜单、1按钮、2接口）",
        source_field="menu_type"
    )
    """
    权限类型。
    - 0：菜单 - 前端路由菜单
    - 1：按钮 - 前端按钮权限
    - 2：接口 - 后端API权限（与Casbin集成）
    """
    
    parent_id = fields.UUIDField(
        default=None,
        null=True,
        description="父权限ID",
        source_field="parent_id"
    )
    
    name = fields.CharField(
        max_length=255,
        null=True,
        description="权限名称/路由名称",
        source_field="name"
    )
    
    path = fields.CharField(
        max_length=255,
        description="路由路径/接口路径",
        null=True,
        source_field="path"
    )
    
    component = fields.CharField(
        max_length=255,
        description="前端组件路径",
        null=True,
        source_field="component"
    )
    
    title = fields.CharField(
        max_length=255,
        description="菜单标题/权限名称",
        null=True,
        source_field="title"
    )

    icon = fields.CharField(
        max_length=255,
        description="图标",
        null=True,
        source_field="icon"
    )

    # ==================== 接口权限字段 ====================
    
    api_path = fields.CharField(
        max_length=255,
        description="API接口路径（支持通配符，如 /api/user/*）",
        null=True,
        source_field="api_path"
    )
    """
    API接口路径。
    - 仅当 menu_type=2 时使用
    - 支持通配符：/api/user/* 匹配 /api/user/1, /api/user/list 等
    - 映射到数据库字段 api_path
    """
    
    api_method = fields.JSONField(
        description="HTTP请求方法列表（如 ['GET', 'POST', 'PUT', 'DELETE']）",
        null=True,
        default=None,
        source_field="api_method"
    )
    """
    HTTP请求方法列表。
    - 仅当 menu_type=2 时使用
    - 存储为JSON数组：["GET", "POST", "PUT", "DELETE"]
    - 支持多选
    """
    
    data_scope = fields.SmallIntField(
        default=4,
        description="数据权限范围（1全部、2本部门及下属、3仅本部门、4仅本人）",
        null=True,
        source_field="data_scope"
    )
    """
    数据权限范围。
    - 1：全部数据
    - 2：本部门及下属部门
    - 3：仅本部门
    - 4：仅本人（默认）
    - 仅当 menu_type=2 时使用
    """

    # ==================== 前端菜单字段 ====================

    showBadge = fields.BooleanField(
        description="是否显示角标",
        null=True,
        source_field="showBadge"
    )
    
    showTextBadge = fields.CharField(
        max_length=255,
        description="显示的角标文本",
        null=True,
        source_field="showTextBadge"
    )
    
    isHide = fields.BooleanField(
        description="是否隐藏",
        null=True,
        source_field="isHide"
    )
    
    isHideTab = fields.BooleanField(
        description="是否隐藏标签",
        null=True,
        source_field="isHideTab"
    )

    link = fields.CharField(
        max_length=255,
        description="外部链接",
        null=True,
        source_field="link"
    )
    
    isIframe = fields.BooleanField(
        description="是否内嵌iframe",
        null=True,
        source_field="isIframe"
    )

    keepAlive = fields.BooleanField(
        description="是否缓存",
        null=True,
        source_field="keepAlive"
    )
    
    isFirstLevel = fields.BooleanField(
        description="是否一级菜单",
        null=True,
        source_field="isFirstLevel"
    )
    
    fixedTab = fields.BooleanField(
        description="是否固定标签",
        null=True,
        source_field="fixedTab"
    )
    
    activePath = fields.CharField(
        max_length=255,
        description="激活路径",
        null=True,
        source_field="activePath"
    )
    
    isFullPage = fields.BooleanField(
        description="是否全屏",
        null=True,
        source_field="isFullPage"
    )
    
    order = fields.IntField(
        default=999,
        description="排序",
        null=True,
        source_field="order"
    )

    # ==================== 按钮权限字段 ====================
    
    authTitle = fields.CharField(
        max_length=255,
        description="权限标题（按钮显示名称）",
        null=True,
        source_field="authTitle"
    )
    
    authMark = fields.CharField(
        max_length=255,
        description="权限标识（如 user:btn:add）",
        null=True,
        source_field="authMark"
    )

    # ==================== 通用字段 ====================

    min_user_type = fields.SmallIntField(
        default=3,
        description="最低用户身份要求（0超级管理员，1管理员，2部门管理员，3普通用户）",
        source_field="min_user_type"
    )
    """
    最低用户身份要求。
    - 0：需要超级管理员权限
    - 1：需要管理员及以上权限
    - 2：需要部门管理员及以上权限
    - 3：所有用户可见（默认）
    """
    
    remark = fields.CharField(
        max_length=500,
        description="备注说明",
        null=True,
        source_field="remark"
    )

    class Meta:
        table = "system_permission"
        table_description = "系统权限表"
