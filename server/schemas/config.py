# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:52
# @UpdateTime : 2025/08/25 02:52
# @Author : sonder
# @File : config.py
# @Software : PyCharm
# @Comment : 本程序
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class ConfigInfo(DataBaseModel):
    """
    配置信息模型
    """
    model_config = ConfigDict()
    name: str = Field(default="", description="配置名称")
    key: str = Field(default="", description="配置键名")
    value: str = Field(default="", description="配置值")
    type: bool = Field(default=False, description="系统内置")
    remark: str = Field(default="", description="备注")


class AddConfigParams(BaseModel):
    """
    添加配置参数模型
    """
    name: str = Field(..., max_length=100, description="配置名称")
    key: str = Field(..., max_length=100, description="配置键名")
    value: str = Field(..., max_length=100, description="配置值")
    type: bool = Field(default=False, description="系统内置")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注信息")


class GetConfigInfoResponse(BaseResponse):
    """
    获取配置模型信息响应
    """
    data: ConfigInfo = Field(default=None, description="响应数据")


class GetConfigInfoResult(ListQueryResult):
    """
    获取配置模型信息结果
    """
    result: List[ConfigInfo] = Field(default=[], description="列表数据")


class GetConfigListResponse(BaseResponse):
    """
    获取配置列表响应
    """
    data: GetConfigInfoResult = Field(default=None, description="响应数据")
