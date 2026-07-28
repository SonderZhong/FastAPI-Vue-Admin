# _*_ coding : UTF-8 _*_
# @Time : 2026/07/02 21:44
# @UpdateTime : 2026/07/02 21:44
# @Author : SonderZhong
# @File : schema.py
# @Software : VSCode
# @Comment : 本程序用于生成租户相关模型


from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from core.common import BaseResponse, ListQueryResult, DataBaseModel


class TenantInfo(DataBaseModel):
    model_config = ConfigDict()
    name: str = Field(..., max_length=100, description="租户名称")
    code: str = Field(..., max_length=100, description="租户编码")
    status: int = Field(default=1, description="租户状态")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注")


class AddTenantParams(BaseModel):
    model_config = ConfigDict()
    name: str = Field(..., max_length=100, description="租户名称")
    code: str = Field(..., max_length=100, description="租户编码")
    status: int = Field(default=1, description="租户状态")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注")


class UpdateTenantParams(BaseModel):
    model_config = ConfigDict()
    name: Optional[str] = Field(default=None, max_length=100, description="租户名称")
    code: Optional[str] = Field(default=None, max_length=100, description="租户编码")
    status: Optional[int] = Field(default=None, description="租户状态")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注")


class GetTenantInfoResponse(BaseResponse):
    data: TenantInfo = Field(default=None, description="租户信息")


class GetTenantListResult(ListQueryResult):
    result: list[TenantInfo] = Field(default=[], description="租户列表")


class GetTenantListResponse(BaseResponse):
    data: GetTenantListResult = Field(default=None, description="租户列表结果")


class JoinTenantParams(BaseModel):
    """已登录用户通过邀请码加入租户"""

    model_config = ConfigDict()
    invite_code: str = Field(..., max_length=32, description="租户邀请码")
