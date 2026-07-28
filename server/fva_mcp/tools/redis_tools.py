# _*_ coding : UTF-8 _*_
"""
Redis 操作工具

提供 Redis 键值操作、Hash、List、Set 等数据结构操作
"""
import json
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path


def get_redis_config() -> dict:
    """获取 Redis 配置"""
    import yaml
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    nodes = config.get("redis", {}).get("nodes", [])
    return nodes[0] if nodes else {}


@asynccontextmanager
async def get_redis_connection():
    """获取 Redis 连接上下文"""
    redis_cfg = get_redis_config()
    if redis_cfg.get("mode") == "memory":
        from utils.memory_redis import MemoryRedis
        yield MemoryRedis()
        return

    from redis.asyncio import Redis as AsyncRedis
    conn_params = {
        "decode_responses": True,
        "socket_timeout": redis_cfg.get("socket_timeout", 5),
        "retry_on_timeout": redis_cfg.get("retry_on_timeout", True),
    }
    password = redis_cfg.get("password", "")
    if password and str(password).strip():
        conn_params["password"] = str(password).strip()

    conn = AsyncRedis.from_url(
        f"redis://{redis_cfg.get('host', '127.0.0.1')}:{redis_cfg.get('port', 6379)}",
        db=redis_cfg.get("database", 0),
        **conn_params,
    )
    try:
        yield conn
    finally:
        await conn.aclose()


def register(mcp):
    """注册 Redis 工具"""

    # ==================== 基础操作 ====================

    @mcp.tool()
    async def redis_get(key: str) -> str:
        """获取 Redis 键值"""
        async with get_redis_connection() as redis:
            try:
                value = await redis.get(key)
                return json.dumps({"exists": value is not None, "value": value}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_set(key: str, value: str, expire_seconds: Optional[int] = None) -> str:
        """设置 Redis 键值"""
        async with get_redis_connection() as redis:
            try:
                if expire_seconds:
                    await redis.setex(key, expire_seconds, value)
                else:
                    await redis.set(key, value)
                return json.dumps({"success": True, "msg": f"键 {key} 设置成功"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_delete(key: str) -> str:
        """删除 Redis 键"""
        async with get_redis_connection() as redis:
            try:
                deleted = await redis.delete(key)
                return json.dumps({"success": True, "deleted": deleted}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_keys(pattern: str = "*") -> str:
        """查找匹配的 Redis 键"""
        async with get_redis_connection() as redis:
            try:
                keys = await redis.keys(pattern)
                return json.dumps({"count": len(keys), "keys": keys[:100]}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_exists(key: str) -> str:
        """检查 Redis 键是否存在"""
        async with get_redis_connection() as redis:
            try:
                exists = await redis.exists(key)
                return json.dumps({"exists": bool(exists)}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_ttl(key: str) -> str:
        """获取 Redis 键的剩余过期时间"""
        async with get_redis_connection() as redis:
            try:
                ttl = await redis.ttl(key)
                if ttl == -2:
                    return json.dumps({"ttl": -2, "msg": "键不存在"}, ensure_ascii=False)
                elif ttl == -1:
                    return json.dumps({"ttl": -1, "msg": "永不过期"}, ensure_ascii=False)
                else:
                    return json.dumps({"ttl": ttl, "msg": f"剩余 {ttl} 秒"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    # ==================== Hash 操作 ====================

    @mcp.tool()
    async def redis_hget(key: str, field: str) -> str:
        """获取 Hash 字段值"""
        async with get_redis_connection() as redis:
            try:
                value = await redis.hget(key, field)
                return json.dumps({"exists": value is not None, "value": value}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_hset(key: str, field: str, value: str) -> str:
        """设置 Hash 字段值"""
        async with get_redis_connection() as redis:
            try:
                await redis.hset(key, field, value)
                return json.dumps({"success": True, "msg": f"Hash {key}.{field} 设置成功"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_hgetall(key: str) -> str:
        """获取 Hash 所有字段和值"""
        async with get_redis_connection() as redis:
            try:
                data = await redis.hgetall(key)
                return json.dumps({"count": len(data), "data": data}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_hdel(key: str, field: str) -> str:
        """删除 Hash 字段"""
        async with get_redis_connection() as redis:
            try:
                deleted = await redis.hdel(key, field)
                return json.dumps({"success": True, "deleted": deleted}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    # ==================== List 操作 ====================

    @mcp.tool()
    async def redis_lrange(key: str, start: int = 0, end: int = -1) -> str:
        """获取 List 范围内的元素"""
        async with get_redis_connection() as redis:
            try:
                items = await redis.lrange(key, start, end)
                return json.dumps({"count": len(items), "items": items}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_lpush(key: str, value: str) -> str:
        """从左侧插入 List 元素"""
        async with get_redis_connection() as redis:
            try:
                length = await redis.lpush(key, value)
                return json.dumps({"success": True, "length": length}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_rpush(key: str, value: str) -> str:
        """从右侧插入 List 元素"""
        async with get_redis_connection() as redis:
            try:
                length = await redis.rpush(key, value)
                return json.dumps({"success": True, "length": length}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    # ==================== Set 操作 ====================

    @mcp.tool()
    async def redis_smembers(key: str) -> str:
        """获取 Set 所有成员"""
        async with get_redis_connection() as redis:
            try:
                members = await redis.smembers(key)
                return json.dumps({"count": len(members), "members": list(members)}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_sadd(key: str, member: str) -> str:
        """添加 Set 成员"""
        async with get_redis_connection() as redis:
            try:
                added = await redis.sadd(key, member)
                return json.dumps({"success": True, "added": added}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_srem(key: str, member: str) -> str:
        """删除 Set 成员"""
        async with get_redis_connection() as redis:
            try:
                removed = await redis.srem(key, member)
                return json.dumps({"success": True, "removed": removed}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    # ==================== 服务器信息 ====================

    @mcp.tool()
    async def redis_info(section: Optional[str] = None) -> str:
        """获取 Redis 服务器信息"""
        async with get_redis_connection() as redis:
            try:
                info = await redis.info(section) if section else await redis.info()
                return json.dumps(info, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    async def redis_dbsize() -> str:
        """获取当前数据库的键数量"""
        async with get_redis_connection() as redis:
            try:
                size = await redis.dbsize()
                return json.dumps({"dbsize": size}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
