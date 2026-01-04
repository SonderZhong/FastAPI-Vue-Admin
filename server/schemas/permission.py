# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:02
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : permission.py
# @Software : PyCharm
# @Comment : 权限 Schema - 支持菜单、按钮、接口三种类型
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class PermissionInfo(DataBaseModel):
    """
    权限信息
    """
    model_config = ConfigDict(populate_by_name=True)
    menu_type: int = Field(None, description="权限类型（0菜单、1按钮、2接口）")
    parent_id: str = Field(None, description="父权限ID")
    name: str = Field(None, description="权限名称")
    path: str = Field(None, description="权限路径")
    title: str = Field(None, description="菜单标题")
    icon: str = Field(None, description="图标")
    component: str = Field(None, description="组件")
    showBadge: bool = Field(None, description="是否显示角标")
    showTextBadge: str = Field(None, description="显示的角标文本")
    isHide: bool = Field(None, description="是否隐藏")
    isHideTab: bool = Field(None, description="是否隐藏标签")
    link: str = Field(None, description="链接")
    isIframe: bool = Field(None, description="是否内嵌iframe")
    keepAlive: bool = Field(None, description="是否缓存")
    isFirstLevel: bool = Field(None, description="是否一级菜单")
    fixedTab: bool = Field(None, description="是否固定标签")
    activePath: str = Field(None, description="激活路径")
    isFullPage: bool = Field(None, description="是否全屏")
    order: int = Field(999, description="排序")
    authTitle: str = Field(None, description="权限标题")
    authMark: str = Field(None, description="权限标识")
    min_user_type: int = Field(3, description="最低用户身份要求（0超级管理员，1管理员，2部门管理员，3普通用户）")
    # 接口权限字段
    api_path: str = Field(None, description="API接口路径")
    api_method: list = Field(None, description="HTTP请求方法列表")
    data_scope: int = Field(None, description="数据权限范围（1全部、2本部门及下属、3仅本部门、4仅本人）")
    remark: str = Field(None, description="备注说明")


class GetPermissionInfoResponse(BaseResponse):
    """
    获取权限信息
    """
    data: PermissionInfo = Field(None, description="权限信息")


class AddPermissionParams(BaseModel):
    """
    新增权限参数
    """
    model_config = ConfigDict()
    menu_type: int = Field(None, description="权限类型（0菜单、1按钮、2接口）")
    parent_id: Optional[str] = Field(None, description="父权限ID")
    name: Optional[str] = Field(None, description="权限名称")
    path: Optional[str] = Field(None, description="权限路径")
    title: Optional[str] = Field(None, description="菜单标题")
    icon: Optional[str] = Field(None, description="图标")
    component: Optional[str] = Field(None, description="组件")
    showBadge: Optional[bool] = Field(None, description="是否显示角标")
    showTextBadge: Optional[str] = Field(None, description="显示的角标文本")
    isHide: Optional[bool] = Field(None, description="是否隐藏")
    isHideTab: Optional[bool] = Field(None, description="是否隐藏标签")
    link: Optional[str] = Field(None, description="链接")
    isIframe: Optional[bool] = Field(None, description="是否内嵌iframe")
    keepAlive: Optional[bool] = Field(None, description="是否缓存")
    isFirstLevel: Optional[bool] = Field(None, description="是否一级菜单")
    fixedTab: Optional[bool] = Field(None, description="是否固定标签")
    activePath: Optional[str] = Field(None, description="激活路径")
    isFullPage: Optional[bool] = Field(None, description="是否全屏")
    order: Optional[int] = Field(999, description="排序")
    authTitle: Optional[str] = Field(None, description="权限标题")
    authMark: Optional[str] = Field(None, description="权限标识")
    min_user_type: Optional[int] = Field(3, ge=0, le=3, description="最低用户身份要求（0超级管理员，1管理员，2部门管理员，3普通用户）")
    # 接口权限字段
    api_path: Optional[str] = Field(None, description="API接口路径（支持通配符，如 /api/user/*）")
    api_method: Optional[List[str]] = Field(None, description="HTTP请求方法列表（如 ['GET', 'POST', 'PUT', 'DELETE']）")
    data_scope: Optional[int] = Field(4, ge=1, le=4, description="数据权限范围（1全部、2本部门及下属、3仅本部门、4仅本人）")
    remark: Optional[str] = Field(None, description="备注说明")


class UpdatePermissionParams(BaseModel):
    """
    更新权限模型
    """
    model_config = ConfigDict()
    menu_type: int = Field(None, description="权限类型（0菜单、1按钮、2接口）")
    parent_id: Optional[str] = Field(None, description="父权限ID")
    name: Optional[str] = Field(None, description="权限名称")
    path: Optional[str] = Field(None, description="权限路径")
    title: Optional[str] = Field(None, description="菜单标题")
    icon: Optional[str] = Field(None, description="图标")
    component: Optional[str] = Field(None, description="组件")
    showBadge: Optional[bool] = Field(None, description="是否显示角标")
    showTextBadge: Optional[str] = Field(None, description="显示的角标文本")
    isHide: Optional[bool] = Field(None, description="是否隐藏")
    isHideTab: Optional[bool] = Field(None, description="是否隐藏标签")
    link: Optional[str] = Field(None, description="链接")
    isIframe: Optional[bool] = Field(None, description="是否内嵌iframe")
    keepAlive: Optional[bool] = Field(None, description="是否缓存")
    isFirstLevel: Optional[bool] = Field(None, description="是否一级菜单")
    fixedTab: Optional[bool] = Field(None, description="是否固定标签")
    activePath: Optional[str] = Field(None, description="激活路径")
    isFullPage: Optional[bool] = Field(None, description="是否全屏")
    order: Optional[int] = Field(999, description="排序")
    authTitle: Optional[str] = Field(None, description="权限标题")
    authMark: Optional[str] = Field(None, description="权限标识")
    min_user_type: Optional[int] = Field(3, ge=0, le=3, description="最低用户身份要求（0超级管理员，1管理员，2部门管理员，3普通用户）")
    # 接口权限字段
    api_path: Optional[str] = Field(None, description="API接口路径（支持通配符，如 /api/user/*）")
    api_method: Optional[List[str]] = Field(None, description="HTTP请求方法列表（如 ['GET', 'POST', 'PUT', 'DELETE']）")
    data_scope: Optional[int] = Field(None, ge=1, le=4, description="数据权限范围（1全部、2本部门及下属、3仅本部门、4仅本人）")
    remark: Optional[str] = Field(None, description="备注说明")


class GetPermissionListResult(ListQueryResult):
    """
    获取权限列表结果模型。
    """
    result: List[PermissionInfo] = Field(default=[], description="权限列表")


class GetPermissionListResponse(BaseResponse):
    """
    获取权限列表响应模型。
    """
    data: GetPermissionListResult = Field(default=None, description="响应数据")
