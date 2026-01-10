# _*_ coding : UTF-8 _*_
# @Time : 2026/01/03 01:36
# @Author : sonder
# @File : user.py
# @Comment : 用户表模型。

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class UserInfo(DataBaseModel):
    """
    用户表模型。信息模型
    """
    model_config = ConfigDict()
    username: str = Field(..., max_length=255, description="用户名")
    password: str = Field(..., max_length=255, description="密码")
    email: Optional[str] = Field(default=None, max_length=255, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=30, description="手机号")
    nickname: Optional[str] = Field(default=None, max_length=255, description="昵称")
    avatar: Optional[str] = Field(default=None, max_length=512, description="头像")
    gender: int = Field(default=0, description="性别（0未知，1男，2女）")
    status: int = Field(default=1, description="用户状态（1启用，0禁用）")
    user_type: int = Field(default=3, description="用户身份标识（0超级管理员，1管理员，2部门管理员，3普通用户）")
    department_id: Optional[str] = Field(default=None, description="所属部门ID")


class AddUserParams(BaseModel):
    """
    添加用户表模型。参数模型
    """
    model_config = ConfigDict()
    username: str = Field(..., max_length=255, description="用户名")
    password: str = Field(..., max_length=255, description="密码")
    email: Optional[str] = Field(default=None, max_length=255, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=30, description="手机号")
    nickname: Optional[str] = Field(default=None, max_length=255, description="昵称")
    avatar: Optional[str] = Field(default=None, max_length=512, description="头像")
    gender: int = Field(default=0, description="性别（0未知，1男，2女）")
    status: int = Field(default=1, description="用户状态（1启用，0禁用）")
    user_type: int = Field(default=3, description="用户身份标识（0超级管理员，1管理员，2部门管理员，3普通用户）")
    department_id: Optional[str] = Field(default=None, description="所属部门ID")


class UpdateUserParams(BaseModel):
    """
    更新用户表模型。参数模型
    """
    model_config = ConfigDict()
    username: Optional[str] = Field(default=None, max_length=255, description="用户名")
    password: Optional[str] = Field(default=None, max_length=255, description="密码")
    email: Optional[str] = Field(default=None, max_length=255, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=30, description="手机号")
    nickname: Optional[str] = Field(default=None, max_length=255, description="昵称")
    avatar: Optional[str] = Field(default=None, max_length=512, description="头像")
    gender: Optional[int] = Field(default=None, description="性别（0未知，1男，2女）")
    status: Optional[int] = Field(default=None, description="用户状态（1启用，0禁用）")
    user_type: Optional[int] = Field(default=None, description="用户身份标识（0超级管理员，1管理员，2部门管理员，3普通用户）")
    department_id: Optional[str] = Field(default=None, description="所属部门ID")


class GetUserListResult(ListQueryResult):
    """
    获取用户表模型。列表结果模型
    """
    result: List[UserInfo] = Field(default=[], description="用户表模型。列表")


class GetUserInfoResponse(BaseResponse):
    """
    获取用户表模型。详情响应模型
    """
    data: UserInfo = Field(default=None, description="用户表模型。信息")


class GetUserListResponse(BaseResponse):
    """
    获取用户表模型。列表响应模型
    """
    data: GetUserListResult = Field(default=None, description="响应数据")


class RegisterUserParams(AddUserParams):
    """
    注册用户参数模型
    """
    model_config = ConfigDict()
    code: Optional[str] = Field(default=None, max_length=10, description="验证码")


class AddUserRoleParams(BaseModel):
    """
    添加用户角色参数模型
    """
    model_config = ConfigDict()
    user_id: str = Field(..., max_length=36, description="用户ID")
    role_ids: List[str] = Field(default=[], description="角色ID列表")


class UpdateUserRoleParams(BaseModel):
    """
    更新用户角色参数模型
    """
    model_config = ConfigDict()
    user_id: str = Field(..., max_length=36, description="用户ID")
    role_ids: List[str] = Field(default=[], description="角色ID列表")


class UserRoleInfo(DataBaseModel):
    """
    用户角色信息模型
    """
    model_config = ConfigDict()
    user_id: str = Field(..., max_length=36, description="用户ID")
    user_name: str = Field(..., max_length=100, description="用户账号")
    role_name: str = Field(..., max_length=100, description="角色名称")
    role_code: str = Field(..., max_length=100, description="角色编码")
    role_id: str = Field(..., max_length=36, description="角色ID")


class GetUserRoleInfoResponse(BaseResponse):
    """
    获取用户角色信息响应模型
    """
    data: UserRoleInfo = Field(default=None, description="响应数据")


class GetUserPermissionListResponse(BaseResponse):
    """
    获取用户权限列表响应模型
    """
    data: List[str] = Field(default=[], description="响应数据")


class ResetPasswordParams(BaseModel):
    """
    重置用户密码参数模型
    """
    model_config = ConfigDict()
    password: str = Field(..., min_length=6, max_length=50, description="新密码")


class UpdateBaseUserInfoParams(BaseModel):
    """
    更新基础个人信息参数模型
    """
    model_config = ConfigDict()
    name: Optional[str] = Field(default=None, max_length=50, description="昵称")
    gender: int = Field(default=0, description="性别（0未知，1男，2女）")


class UploadFileResponse(BaseResponse):
    """
    文件上传响应模型
    """
    data: dict = Field(default=None, description="文件信息")


class GetUserRoleListResponse(BaseResponse):
    """
    获取用户角色列表响应模型
    """
    data: dict = Field(default=None, description="用户角色列表数据")