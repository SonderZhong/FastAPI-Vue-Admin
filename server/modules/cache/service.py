# _*_ coding : UTF-8 _*_

from datetime import datetime, timedelta
from typing import List

from modules.cache.schema import CacheMonitor, CacheInfo
from utils.get_redis import RedisKeyConfig


class CacheService:
    """缓存管理服务 - 操作 Redis 监控和缓存数据"""

    @staticmethod
    async def get_monitor_info(redis) -> CacheMonitor:
        info = await redis.info()
        db_size = await redis.dbsize()
        command_stats_dict = await redis.info("commandstats")

        command_stats = [
            dict(
                name=key.split("_")[1],
                value=int(value.get("calls", 0)),
                usec=int(value.get("usec", 0)),
                usec_per_call=float(value.get("usec_per_call", 0)),
            )
            for key, value in command_stats_dict.items()
        ]

        memory_stats = {
            "used_memory": int(info.get("used_memory", 0)),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "used_memory_rss": int(info.get("used_memory_rss", 0)),
            "used_memory_peak": int(info.get("used_memory_peak", 0)),
            "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            "maxmemory": int(info.get("maxmemory", 0)),
            "maxmemory_human": info.get("maxmemory_human", "unlimited"),
            "mem_fragmentation_ratio": float(info.get("mem_fragmentation_ratio", 0)),
        }

        connection_stats = {
            "connected_clients": int(info.get("connected_clients", 0)),
            "client_recent_max_input_buffer": int(
                info.get("client_recent_max_input_buffer", 0)
            ),
            "client_recent_max_output_buffer": int(
                info.get("client_recent_max_output_buffer", 0)
            ),
            "blocked_clients": int(info.get("blocked_clients", 0)),
            "total_connections_received": int(
                info.get("total_connections_received", 0)
            ),
        }

        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        performance_stats = {
            "total_commands_processed": int(info.get("total_commands_processed", 0)),
            "instantaneous_ops_per_sec": int(info.get("instantaneous_ops_per_sec", 0)),
            "total_net_input_bytes": int(info.get("total_net_input_bytes", 0)),
            "total_net_output_bytes": int(info.get("total_net_output_bytes", 0)),
            "keyspace_hits": hits,
            "keyspace_misses": misses,
            "hit_rate": round(hits / max(hits + misses, 1) * 100, 2),
        }

        key_space_stats = []
        for key, value in info.items():
            if key.startswith("db"):
                db_info = {}
                if isinstance(value, dict):
                    db_info = value
                elif isinstance(value, str):
                    for item in value.split(","):
                        k, v = item.split("=")
                        db_info[k] = int(v)
                else:
                    continue
                key_space_stats.append(
                    {
                        "db": key,
                        "keys": db_info.get("keys", 0),
                        "expires": db_info.get("expires", 0),
                        "avg_ttl": db_info.get("avg_ttl", 0),
                    }
                )

        return CacheMonitor(
            info=info,
            db_size=db_size,
            command_stats=command_stats,
            memory_stats=memory_stats,
            connection_stats=connection_stats,
            performance_stats=performance_stats,
            key_space_stats=key_space_stats,
        )

    @staticmethod
    def get_cache_names() -> List[CacheInfo]:
        return [
            CacheInfo(cache_key="", cache_name=kc.key, cache_value="", remark=kc.remark)
            for kc in RedisKeyConfig
        ]

    @staticmethod
    async def get_cache_keys(
        redis, cache_name: str, page: int = 1, size: int = 10, search: str = None
    ):
        cache_keys = await redis.keys(f"{cache_name}*")
        cache_key_list = [
            key.split(":", 1)[1]
            for key in cache_keys
            if key.startswith(f"{cache_name}:")
        ]

        if search:
            cache_key_list = [
                key for key in cache_key_list if search.lower() in key.lower()
            ]

        total = len(cache_key_list)
        start = (page - 1) * size
        paginated_keys = cache_key_list[start : start + size]
        result = [{"key": key} for key in paginated_keys]

        return result, total

    @staticmethod
    async def get_cache_info(redis, cache_name: str, cache_key: str) -> CacheInfo:
        redis_key = f"{cache_name}:{cache_key}"
        cache_value = await redis.get(redis_key)
        ttl = await redis.ttl(redis_key)

        expire_time = None
        if ttl > 0:
            expire_time = (datetime.now() + timedelta(seconds=ttl)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return CacheInfo(
            cache_key=cache_key,
            cache_name=cache_name,
            cache_value=cache_value,
            remark="",
            ttl=ttl if ttl > 0 else None,
            expire_time=expire_time,
        )

    @staticmethod
    async def update_cache_value(redis, cache_name: str, cache_key: str, value: str):
        await redis.set(f"{cache_name}:{cache_key}", value)

    @staticmethod
    async def delete_by_name(redis, name: str):
        cache_keys = await redis.keys(f"{name}*")
        if cache_keys:
            await redis.delete(*cache_keys)

    @staticmethod
    async def delete_by_key(redis, key: str):
        cache_keys = await redis.keys(f"*{key}")
        if cache_keys:
            await redis.delete(*cache_keys)

    @staticmethod
    async def clear_all(redis):
        cache_keys = await redis.keys()
        if cache_keys:
            await redis.delete(*cache_keys)
