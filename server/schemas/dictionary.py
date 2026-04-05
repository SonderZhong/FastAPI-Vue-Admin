# _*_ coding : UTF-8 _*_
# @Time : 2026/04/06 01:08
# @Author : sonder
# @File : dictionary.py
# @Comment : 数据字典和字典项 Schema

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


# ==================== 数据字典 Schema ====================

class DictionaryInfo(DataBaseModel):
    """数据字典信息模型"""
    model_config = ConfigDict()
    dict_name: str = Field(..., max_length=100, description="字典名称")
    dict_code: str = Field(..., max_length=100, description="字典编码")
    dict_type: str = Field(..., max_length=50, description="字典类型")
    status: int = Field(default=1, description="状态（1启用，0禁用）")
    sort: int = Field(default=0, description="排序（数字越小越靠前）")
    remark: Optional[str] = Field(default=None, description="备注")


class AddDictionaryParams(BaseModel):
    """添加数据字典参数模型"""
    model_config = ConfigDict()
    dict_name: str = Field(..., max_length=100, description="字典名称")
    dict_code: str = Field(..., max_length=100, description="字典编码")
    dict_type: str = Field(..., max_length=50, description="字典类型")
    status: int = Field(default=1, description="状态（1启用，0禁用）")
    sort: int = Field(default=0, description="排序（数字越小越靠前）")
    remark: Optional[str] = Field(default=None, description="备注")


class UpdateDictionaryParams(BaseModel):
    """更新数据字典参数模型"""
    model_config = ConfigDict()
    dict_name: Optional[str] = Field(default=None, max_length=100, description="字典名称")
    dict_code: Optional[str] = Field(default=None, max_length=100, description="字典编码")
    dict_type: Optional[str] = Field(default=None, max_length=50, description="字典类型")
    status: Optional[int] = Field(default=None, description="状态（1启用，0禁用）")
    sort: Optional[int] = Field(default=None, description="排序（数字越小越靠前）")
    remark: Optional[str] = Field(default=None, description="备注")


class GetDictionaryListResult(ListQueryResult):
    """获取数据字典列表结果模型"""
    result: List[DictionaryInfo] = Field(default=[], description="数据字典列表")


class GetDictionaryInfoResponse(BaseResponse):
    """获取数据字典详情响应模型"""
    data: DictionaryInfo = Field(default=None, description="数据字典信息")


class GetDictionaryListResponse(BaseResponse):
    """获取数据字典列表响应模型"""
    data: GetDictionaryListResult = Field(default=None, description="响应数据")


# ==================== 数据字典项 Schema ====================

class DictionaryItemInfo(DataBaseModel):
    """数据字典项信息模型"""
    model_config = ConfigDict()
    dictionary_id: Optional[str] = Field(default=None, description="所属字典ID")
    label: str = Field(..., max_length=100, description="字典项标签")
    value: str = Field(..., max_length=100, description="字典项值")
    status: int = Field(default=1, description="状态（1启用，0禁用）")
    sort: int = Field(default=0, description="排序（数字越小越靠前）")
    tag_color: Optional[str] = Field(default=None, max_length=50, description="标签颜色")
    remark: Optional[str] = Field(default=None, description="备注")


class AddDictionaryItemParams(BaseModel):
    """添加数据字典项参数模型"""
    model_config = ConfigDict()
    dictionary_id: str = Field(..., description="所属字典ID")
    label: str = Field(..., max_length=100, description="字典项标签")
    value: str = Field(..., max_length=100, description="字典项值")
    status: int = Field(default=1, description="状态（1启用，0禁用）")
    sort: int = Field(default=0, description="排序（数字越小越靠前）")
    tag_color: Optional[str] = Field(default=None, max_length=50, description="标签颜色")
    remark: Optional[str] = Field(default=None, description="备注")


class UpdateDictionaryItemParams(BaseModel):
    """更新数据字典项参数模型"""
    model_config = ConfigDict()
    dictionary_id: Optional[str] = Field(default=None, description="所属字典ID")
    label: Optional[str] = Field(default=None, max_length=100, description="字典项标签")
    value: Optional[str] = Field(default=None, max_length=100, description="字典项值")
    status: Optional[int] = Field(default=None, description="状态（1启用，0禁用）")
    sort: Optional[int] = Field(default=None, description="排序（数字越小越靠前）")
    tag_color: Optional[str] = Field(default=None, max_length=50, description="标签颜色")
    remark: Optional[str] = Field(default=None, description="备注")


class GetDictionaryItemListResult(ListQueryResult):
    """获取数据字典项列表结果模型"""
    result: List[DictionaryItemInfo] = Field(default=[], description="数据字典项列表")


class GetDictionaryItemInfoResponse(BaseResponse):
    """获取数据字典项详情响应模型"""
    data: DictionaryItemInfo = Field(default=None, description="数据字典项信息")


class GetDictionaryItemListResponse(BaseResponse):
    """获取数据字典项列表响应模型"""
    data: GetDictionaryItemListResult = Field(default=None, description="响应数据")
