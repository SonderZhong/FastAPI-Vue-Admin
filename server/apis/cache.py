# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 03:02
# @UpdateTime : 2025/08/25 03:02
# @Author : sonder
# @File : cache.py
# @Software : PyCharm
# @Comment : 本程序
from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from schemas.common import BaseResponse
from schemas.cache import (
    CacheMonitor, GetCacheInfoResponse, CacheInfo, GetCacheMonitorResponse, GetCacheKeysPageResponse,
    UpdateCacheValueParams
)
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil

cacheAPI = APIRouter(
    prefix="/cache",
    dependencies=[Depends(AuthController.get_current_user)],
)


@cacheAPI.get("/monitor", response_class=JSONResponse, response_model=GetCacheMonitorResponse,
              summary="获取缓存监控信息")
@Log(title="获取缓存监控信息", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:infoList', 'GET:/cache/monitor'])
async def get_cache_info(request: Request):
    info = await request.app.state.redis.info()
    db_size = await request.app.state.redis.dbsize()
    command_stats_dict = await request.app.state.redis.info('commandstats')
    
    # 命令统计
    command_stats = [
        dict(name=key.split('_')[1], value=int(value.get('calls', 0)), 
             usec=int(value.get('usec', 0)), usec_per_call=float(value.get('usec_per_call', 0)))
        for key, value in command_stats_dict.items()
    ]
    
    # 内存统计
    memory_stats = {
        'used_memory': int(info.get('used_memory', 0)),
        'used_memory_human': info.get('used_memory_human', '0B'),
        'used_memory_rss': int(info.get('used_memory_rss', 0)),
        'used_memory_peak': int(info.get('used_memory_peak', 0)),
        'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
        'maxmemory': int(info.get('maxmemory', 0)),
        'maxmemory_human': info.get('maxmemory_human', 'unlimited'),
        'mem_fragmentation_ratio': float(info.get('mem_fragmentation_ratio', 0))
    }
    
    # 连接统计
    connection_stats = {
        'connected_clients': int(info.get('connected_clients', 0)),
        'client_recent_max_input_buffer': int(info.get('client_recent_max_input_buffer', 0)),
        'client_recent_max_output_buffer': int(info.get('client_recent_max_output_buffer', 0)),
        'blocked_clients': int(info.get('blocked_clients', 0)),
        'total_connections_received': int(info.get('total_connections_received', 0))
    }
    
    # 性能统计
    performance_stats = {
        'total_commands_processed': int(info.get('total_commands_processed', 0)),
        'instantaneous_ops_per_sec': int(info.get('instantaneous_ops_per_sec', 0)),
        'total_net_input_bytes': int(info.get('total_net_input_bytes', 0)),
        'total_net_output_bytes': int(info.get('total_net_output_bytes', 0)),
        'keyspace_hits': int(info.get('keyspace_hits', 0)),
        'keyspace_misses': int(info.get('keyspace_misses', 0)),
        'hit_rate': round(int(info.get('keyspace_hits', 0)) / max(int(info.get('keyspace_hits', 0)) + int(info.get('keyspace_misses', 0)), 1) * 100, 2)
    }
    
    # 键空间统计
    key_space_stats = []
    for key, value in info.items():
        if key.startswith('db'):
            db_info = {}
            # 检查value是否已经是字典类型
            if isinstance(value, dict):
                db_info = value
            elif isinstance(value, str):
                # 如果是字符串，则按原来的方式解析
                for item in value.split(','):
                    k, v = item.split('=')
                    db_info[k] = int(v)
            else:
                # 其他类型，跳过
                continue
                
            key_space_stats.append({
                'db': key,
                'keys': db_info.get('keys', 0),
                'expires': db_info.get('expires', 0),
                'avg_ttl': db_info.get('avg_ttl', 0)
            })
    
    cache_info = CacheMonitor(
        info=info,
        db_size=db_size,
        command_stats=command_stats,
        memory_stats=memory_stats,
        connection_stats=connection_stats,
        performance_stats=performance_stats,
        key_space_stats=key_space_stats
    )
    return ResponseUtil.success(data=cache_info)


@cacheAPI.get("/names", response_class=JSONResponse, response_model=GetCacheInfoResponse,
              summary="获取缓存名称列表")
@Log(title="获取缓存名称列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:list', 'GET:/cache/names'])
async def get_cache_names(request: Request):
    name_list = []
    for key_config in RedisKeyConfig:
        name_list.append(
            CacheInfo(
                cache_key='',
                cache_name=key_config.key,
                cache_value='',
                remark=key_config.remark,
            )
        )
    return ResponseUtil.success(data=name_list)


@cacheAPI.get("/keys/{cacheName}", response_class=JSONResponse, response_model=GetCacheKeysPageResponse,
              summary="获取缓存键名分页列表")
@Log(title="获取缓存键名列表", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:list', 'GET:/cache/keys/*'])
async def get_cache_keys(
    request: Request, 
    cacheName: str = Path(description="缓存名称"),
    page: int = 1,
    size: int = 10,
    search: str = None
):
    cache_keys = await request.app.state.redis.keys(f'{cacheName}*')
    cache_key_list = [key.split(':', 1)[1] for key in cache_keys if key.startswith(f'{cacheName}:')]
    
    # 搜索过滤
    if search:
        cache_key_list = [key for key in cache_key_list if search.lower() in key.lower()]
    
    # 分页处理
    total = len(cache_key_list)
    start = (page - 1) * size
    end = start + size
    paginated_keys = cache_key_list[start:end]
    
    # 构造返回数据
    result = [{"key": key} for key in paginated_keys]
    
    return ResponseUtil.success(data={
        "result": result,
        "total": total,
        "page": page,
        "size": size
    })


@cacheAPI.get("/info/{cacheName}/{cacheKey}", response_class=JSONResponse, response_model=GetCacheInfoResponse,
              summary="获取缓存信息")
@Log(title="获取缓存信息", operation_type=OperationType.SELECT)
@Auth(permission_list=['cache:btn:info', 'GET:/cache/info/*'])
async def get_cache_info_detail(request: Request, cacheName: str = Path(description="缓存名称"),
                                cacheKey: str = Path(description="缓存键名")):
    redis_key = f'{cacheName}:{cacheKey}'
    cache_value = await request.app.state.redis.get(redis_key)
    
    # 获取TTL（生存时间）
    ttl = await request.app.state.redis.ttl(redis_key)
    expire_time = None
    
    # 如果TTL大于0，计算过期时间
    if ttl > 0:
        from datetime import datetime, timedelta
        expire_time = (datetime.now() + timedelta(seconds=ttl)).strftime('%Y-%m-%d %H:%M:%S')
    
    cache_info = CacheInfo(
        cache_key=cacheKey,
        cache_name=cacheName,
        cache_value=cache_value,
        remark="",
        ttl=ttl if ttl > 0 else None,
        expire_time=expire_time
    )
    return ResponseUtil.success(data=cache_info)


@cacheAPI.put("/info/{cacheName}/{cacheKey}", response_class=JSONResponse, response_model=BaseResponse,
              summary="更新缓存值")
@Log(title="更新缓存值", operation_type=OperationType.UPDATE)
@Auth(permission_list=['cache:btn:update', 'PUT:/cache/info/*'])
async def update_cache_value(
    request: Request, 
    params: UpdateCacheValueParams,
    cacheName: str = Path(description="缓存名称"),
    cacheKey: str = Path(description="缓存键名"),
    
):
    try:
        await request.app.state.redis.set(f'{cacheName}:{cacheKey}', params.cache_value)
        return ResponseUtil.success(msg="更新缓存值成功")
    except Exception as e:
        return ResponseUtil.error(msg=f"更新缓存值失败: {str(e)}")


@cacheAPI.delete("/cacheName/{name}", response_class=JSONResponse, response_model=BaseResponse,
                 summary="通过键名删除缓存")
@cacheAPI.post("/cacheName/{name}", response_class=JSONResponse, response_model=BaseResponse,
               summary="通过键名删除缓存")
@Log(title="通过键名删除缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=['cache:btn:delete', 'DELETE,POST:/cache/cacheName/*'])
async def delete_cache(request: Request, name: str = Path(description="缓存名称")):
    cache_keys = await request.app.state.redis.keys(f'{name}*')
    if cache_keys:
        await request.app.state.redis.delete(*cache_keys)
    return ResponseUtil.success(msg=f"删除{name}缓存成功！")


@cacheAPI.delete("/cacheKey/{key}", response_class=JSONResponse, response_model=BaseResponse,
                 summary="通过键值删除缓存")
@cacheAPI.post("/cacheKey/{key}", response_class=JSONResponse, response_model=BaseResponse, summary="通过键值删除缓存")
@Log(title="通过键值删除缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=['cache:btn:delete', 'DELETE,POST:/cache/cacheKey/*'])
async def delete_cache_key(request: Request, key: str = Path(description="缓存键名")):
    cache_keys = await request.app.state.redis.keys(f'*{key}')
    if cache_keys:
        await request.app.state.redis.delete(*cache_keys)
    return ResponseUtil.success(msg=f"删除{key}缓存成功！")


@cacheAPI.delete("/clearAll", response_class=JSONResponse, response_model=BaseResponse, summary="删除所有缓存")
@cacheAPI.post("/clearAll", response_class=JSONResponse, response_model=BaseResponse, summary="删除所有缓存")
@Log(title="删除所有缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=['cache:btn:delete', 'DELETE,POST:/cache/clearAll'])
async def delete_all_cache(request: Request):
    cache_keys = await request.app.state.redis.keys()
    if cache_keys:
        await request.app.state.redis.delete(*cache_keys)
    return ResponseUtil.success(msg="删除所有缓存成功！")
