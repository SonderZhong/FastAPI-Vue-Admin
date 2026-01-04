# _*_ coding : UTF-8 _*_
# @Time : 2026/01/03 01:40
# @Author : sonder
# @File : department.py
# @Comment : 部门模型

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class DepartmentInfo(DataBaseModel):
    """
    部门模型信息模型
    """
    model_config = ConfigDict()
    name: str = Field(..., max_length=50, description="部门名称")
    parent_id: Optional[str] = Field(default=None, max_length=50, description="上级部门ID")
    sort: int = Field(default=0, description="排序权重（0最高）")
    phone: Optional[str] = Field(default=None, max_length=30, description="部门电话")
    principal: str = Field(..., max_length=64, description="部门负责人")
    email: Optional[str] = Field(default=None, max_length=128, description="部门邮箱")
    status: int = Field(default=1, description="状态（0正常 1停用）")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注信息")


class AddDepartmentParams(BaseModel):
    """
    添加部门模型参数模型
    """
    model_config = ConfigDict()
    name: str = Field(..., max_length=50, description="部门名称")
    parent_id: Optional[str] = Field(default=None, max_length=50, description="上级部门ID")
    sort: int = Field(default=0, description="排序权重（0最高）")
    phone: Optional[str] = Field(default=None, max_length=30, description="部门电话")
    principal: str = Field(..., max_length=64, description="部门负责人")
    email: Optional[str] = Field(default=None, max_length=128, description="部门邮箱")
    status: int = Field(default=1, description="状态（0正常 1停用）")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注信息")


class UpdateDepartmentParams(BaseModel):
    """
    更新部门模型参数模型
    """
    model_config = ConfigDict()
    name: Optional[str] = Field(default=None, max_length=50, description="部门名称")
    parent_id: Optional[str] = Field(default=None, max_length=50, description="上级部门ID")
    sort: Optional[int] = Field(default=None, description="排序权重（0最高）")
    phone: Optional[str] = Field(default=None, max_length=30, description="部门电话")
    principal: Optional[str] = Field(default=None, max_length=64, description="部门负责人")
    email: Optional[str] = Field(default=None, max_length=128, description="部门邮箱")
    status: Optional[int] = Field(default=None, description="状态（0正常 1停用）")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注信息")


class GetDepartmentListResult(ListQueryResult):
    """
    获取部门模型列表结果模型
    """
    result: List[DepartmentInfo] = Field(default=[], description="部门模型列表")


class GetDepartmentInfoResponse(BaseResponse):
    """
    获取部门模型详情响应模型
    """
    data: DepartmentInfo = Field(default=None, description="部门模型信息")


class GetDepartmentListResponse(BaseResponse):
    """
    获取部门模型列表响应模型
    """
    data: GetDepartmentListResult = Field(default=None, description="响应数据")

