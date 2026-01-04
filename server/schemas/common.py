# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:55
# @UpdateTime : 2025/08/04 01:55
# @Author : sonder
# @File : common.py
# @Software : PyCharm
# @Comment : 本程序
from typing import List

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_snake


class BaseResponse(BaseModel):
    """
    基础响应模型
    """
    model_config = ConfigDict(alias_generator=to_snake)
    code: int = Field(default=200, description="响应码")
    msg: str = Field(default="操作成功！", description="响应信息")
    data: dict = Field(default=None, description="响应数据")
    success: bool = Field(default=True, description="操作是否成功")
    time: str = Field(default="", description="响应时间")


class ListQueryResult(BaseModel):
    """
    列表查询结果
    """
    model_config = ConfigDict(alias_generator=to_snake)
    result: List = Field(default=[], description="列表数据")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页码")
    pageSize: int = Field(default=10, description="每页数量")


class DeleteListParams(BaseModel):
    """
    批量删除参数
    """
    model_config = ConfigDict(alias_generator=to_snake)
    ids: List[str] = Field(default=[], description="删除ID列表")


class DataBaseModel(BaseModel):
    """
    数据库模型
    """
    model_config = ConfigDict()
    id: str = Field(default="", description="主键")
    is_del: bool = Field(default=False, description="删除标志")
    created_at: str = Field(default="", description="创建时间")
    updated_at: str = Field(default="", description="更新时间")
