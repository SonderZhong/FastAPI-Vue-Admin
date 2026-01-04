# _*_ coding : UTF-8 _*_
# @Time : 2026/01/03 01:25
# @Author : sonder
# @File : role.py
# @Comment : 角色表模型

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class RoleInfo(DataBaseModel):
    """
    角色表模型信息模型
    """
    model_config = ConfigDict()
    name: str = Field(..., max_length=255, description="角色名称")
    code: str = Field(..., max_length=255, description="角色编码")
    description: Optional[str] = Field(default=None, max_length=255, description="角色描述")
    status: int = Field(default=1, description="角色状态")
    department: Optional[str] = Field(default=None, description="所属部门")


class AddRoleParams(BaseModel):
    """
    添加角色表模型参数模型
    """
    model_config = ConfigDict()
    name: str = Field(..., max_length=255, description="角色名称")
    code: str = Field(..., max_length=255, description="角色编码")
    description: Optional[str] = Field(default=None, max_length=255, description="角色描述")
    status: int = Field(default=1, description="角色状态")
    department: Optional[str] = Field(default=None, description="所属部门")


class UpdateRoleParams(BaseModel):
    """
    更新角色表模型参数模型
    """
    model_config = ConfigDict()
    name: Optional[str] = Field(default=None, max_length=255, description="角色名称")
    code: Optional[str] = Field(default=None, max_length=255, description="角色编码")
    description: Optional[str] = Field(default=None, max_length=255, description="角色描述")
    status: Optional[int] = Field(default=None, description="角色状态")
    department: Optional[str] = Field(default=None, description="所属部门")


class UpdateRoleResponse(BaseResponse):
    """
    更新角色响应模型
    """
    data: Optional[RoleInfo] = Field(default=None, description="更新后的角色信息")


class GetRoleInfoResponse(BaseResponse):
    """
    获取角色信息响应模型
    """
    data: RoleInfo = Field(default=None, description="角色信息")


class GetRoleListResult(ListQueryResult):
    """
    获取角色列表结果模型
    """
    result: List[RoleInfo] = Field(default=[], description="角色列表")


class GetRoleListResponse(BaseResponse):
    """
    获取角色列表响应模型
    """
    data: GetRoleListResult = Field(default=None, description="角色列表结果")


class AddRolePermissionParams(BaseModel):
    """
    添加角色权限请求参数模型
    """
    model_config = ConfigDict()
    permission_ids: List[str] = Field(..., description="权限ID列表")


class RolePermissionInfo(DataBaseModel):
    """
    角色权限信息模型
    """
    model_config = ConfigDict()
    role_id: str = Field(..., max_length=36, description="角色ID")
    role_code: str = Field(..., max_length=255, description="角色编码")
    role_name: str = Field(..., max_length=255, description="角色名称")
    permission_id: str = Field(..., max_length=36, description="权限ID")
    permission__parent_id: str = Field(default="", max_length=36, description="父级权限ID")
    permission_name: str = Field(..., max_length=255, description="权限名称")
    permission_code: str = Field(..., max_length=255, description="权限编码")
    permission_type: str = Field(..., max_length=255, description="权限类型")


class GetRolePermissionInfoResponse(BaseResponse):
    """
    获取角色权限信息响应模型
    """
    data: RolePermissionInfo = Field(default=None, description="角色权限信息")


class GetRolePermissionListResult(ListQueryResult):
    """
    获取角色权限列表结果模型
    """
    result: List[RolePermissionInfo] = Field(default=[], description="角色权限列表")


class GetRolePermissionListResponse(BaseResponse):
    """
    获取角色权限列表响应模型
    """
    data: GetRolePermissionListResult = Field(default=None, description="角色权限列表结果")