# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 03:02
# @UpdateTime : 2025/08/25 03:02
# @Author : sonder
# @File : cache.py
# @Software : PyCharm
# @Comment : 本程序
from typing import Optional, Any, List

from pydantic import BaseModel, ConfigDict, Field

from schemas.common import BaseResponse,ListQueryResult


class CacheMonitor(BaseModel):
    """
    缓存监控信息
    """
    model_config = ConfigDict()

    command_stats: Optional[List] = Field(default=[], description='命令统计')
    db_size: Optional[int] = Field(default=None, description='Key数量')
    info: Optional[dict] = Field(default={}, description='Redis信息')
    memory_stats: Optional[dict] = Field(default={}, description='内存统计')
    connection_stats: Optional[dict] = Field(default={}, description='连接统计')
    performance_stats: Optional[dict] = Field(default={}, description='性能统计')
    key_space_stats: Optional[List] = Field(default=[], description='键空间统计')


class CacheInfo(BaseModel):
    """
    缓存信息
    """
    model_config = ConfigDict()

    cache_key: Optional[str] = Field(default=None, description='缓存键名')
    cache_name: Optional[str] = Field(default=None, description='缓存名称')
    cache_value: Optional[Any] = Field(default=None, description='缓存内容')
    remark: Optional[str] = Field(default=None, description='备注')
    ttl: Optional[int] = Field(default=None, description='生存时间（秒）')
    expire_time: Optional[str] = Field(default=None, description='过期时间')


class GetCacheMonitorResponse(BaseResponse):
    """
    获取缓存监控信息响应
    """
    data: CacheMonitor = Field(default={}, description="缓存监控信息查询结果")


class GetCacheInfoResponse(BaseResponse):
    """
    获取缓存信息响应
    """
    data: List[CacheInfo] = Field(default=[], description="缓存信息查询结果")


class GetCacheKeysListResponse(BaseResponse):
    """
    获取缓存键名列表
    """
    data: List[str] = Field(default=[], description="缓存键名列表")


class CacheKeySearchParams(BaseModel):
    """
    缓存键搜索参数
    """
    model_config = ConfigDict()

    page: int = Field(default=1, description="页码")
    size: int = Field(default=10, description="每页数量")
    search: Optional[str] = Field(default=None, description="搜索关键词")


class UpdateCacheValueParams(BaseModel):
    """
    更新缓存值参数
    """
    model_config = ConfigDict()

    cache_value: str = Field(description="缓存值")


class GetCacheKeysPageResponse(ListQueryResult):
    """
    获取缓存键分页列表响应
    """
    result: List[dict] = Field(default=[], description="缓存键列表")
