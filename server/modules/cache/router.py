# _*_ coding : UTF-8 _*_

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse
from modules.cache.schema import (
    GetCacheInfoResponse, GetCacheMonitorResponse, GetCacheKeysPageResponse,
    UpdateCacheValueParams,
)
from modules.cache.service import CacheService
from utils.response import ResponseUtil

cacheAPI = APIRouter(
    prefix="/cache",
    dependencies=[Depends(AuthController.get_current_user)],
)


@cacheAPI.get("/monitor", response_class=JSONResponse, response_model=GetCacheMonitorResponse,
              summary="获取缓存监控信息")
@Log(title="获取缓存监控信息", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:infoList'])
async def get_cache_info(request: Request):
    cache_info = await CacheService.get_monitor_info(request.app.state.redis)
    return ResponseUtil.success(data=cache_info)


@cacheAPI.get("/names", response_class=JSONResponse, response_model=GetCacheInfoResponse,
              summary="获取缓存名称列表")
@Log(title="获取缓存名称列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:list'])
async def get_cache_names(request: Request):
    name_list = CacheService.get_cache_names()
    return ResponseUtil.success(data=name_list)


@cacheAPI.get("/keys/{cacheName}", response_class=JSONResponse, response_model=GetCacheKeysPageResponse,
              summary="获取缓存键名分页列表")
@Log(title="获取缓存键名列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:list'])
async def get_cache_keys(
    request: Request,
    cacheName: str = Path(description="缓存名称"),
    page: int = 1,
    size: int = 10,
    search: str = None,
):
    result, total = await CacheService.get_cache_keys(request.app.state.redis, cacheName, page, size, search)
    return ResponseUtil.success(data={"result": result, "total": total, "page": page, "size": size})


@cacheAPI.get("/info/{cacheName}/{cacheKey}", response_class=JSONResponse, response_model=GetCacheInfoResponse,
              summary="获取缓存信息")
@Log(title="获取缓存信息", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:info'])
async def get_cache_info_detail(request: Request, cacheName: str = Path(description="缓存名称"),
                                cacheKey: str = Path(description="缓存键名")):
    cache_info = await CacheService.get_cache_info(request.app.state.redis, cacheName, cacheKey)
    return ResponseUtil.success(data=cache_info)


@cacheAPI.put("/info/{cacheName}/{cacheKey}", response_class=JSONResponse, response_model=BaseResponse,
              summary="更新缓存值")
@Log(title="更新缓存值", operation_type=OperationType.UPDATE)
@Auth(permission_list=['cache:btn:update'])
async def update_cache_value(
    request: Request,
    params: UpdateCacheValueParams,
    cacheName: str = Path(description="缓存名称"),
    cacheKey: str = Path(description="缓存键名"),
):
    try:
        await CacheService.update_cache_value(request.app.state.redis, cacheName, cacheKey, params.cache_value)
        return ResponseUtil.success(msg="更新缓存值成功")
    except Exception as e:
        return ResponseUtil.error(msg=f"更新缓存值失败: {str(e)}")


@cacheAPI.delete("/cacheName/{name}", response_class=JSONResponse, response_model=BaseResponse,
                 summary="通过键名删除缓存")
@cacheAPI.post("/cacheName/{name}", response_class=JSONResponse, response_model=BaseResponse,
               summary="通过键名删除缓存")
@Log(title="通过键名删除缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=['cache:btn:delete'])
async def delete_cache(request: Request, name: str = Path(description="缓存名称")):
    await CacheService.delete_by_name(request.app.state.redis, name)
    return ResponseUtil.success(msg=f"删除{name}缓存成功！")


@cacheAPI.delete("/cacheKey/{key}", response_class=JSONResponse, response_model=BaseResponse,
                 summary="通过键值删除缓存")
@cacheAPI.post("/cacheKey/{key}", response_class=JSONResponse, response_model=BaseResponse,
               summary="通过键值删除缓存")
@Log(title="通过键值删除缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=['cache:btn:delete'])
async def delete_cache_key(request: Request, key: str = Path(description="缓存键名")):
    await CacheService.delete_by_key(request.app.state.redis, key)
    return ResponseUtil.success(msg=f"删除{key}缓存成功！")


@cacheAPI.delete("/clearAll", response_class=JSONResponse, response_model=BaseResponse, summary="删除所有缓存")
@cacheAPI.post("/clearAll", response_class=JSONResponse, response_model=BaseResponse, summary="删除所有缓存")
@Log(title="删除所有缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=['cache:btn:delete'])
async def delete_all_cache(request: Request):
    await CacheService.clear_all(request.app.state.redis)
    return ResponseUtil.success(msg="删除所有缓存成功！")
