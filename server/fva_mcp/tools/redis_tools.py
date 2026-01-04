# _*_ coding : UTF-8 _*_
# @Time : 2025/01/02
# @Author : sonder
# @File : redis_tools.py
# @Comment : Redis 操作工具

import json
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path


def get_redis_config() -> dict:
    """获取 Redis 配置"""
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError("配置文件不存在，请先完成系统初始化")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config.get("redis", {})


@asynccontextmanager
async def get_redis_connection():
    """获取 Redis 连接上下文"""
    from redis.asyncio import Redis as AsyncRedis
    
    redis_cfg = get_redis_config()
    
    conn_params = {
        "decode_responses": True,
        "socket_timeout": redis_cfg.get("socket_timeout", 5),
        "retry_on_timeout": redis_cfg.get("retry_on_timeout", True),
        "max_connections": redis_cfg.get("max_connections", 10),
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
    """注册 Redis 工具到 MCP 服务器"""
    
    # ==================== 基础操作 ====================
    
    @mcp.tool()
    async def redis_get(key: str) -> str:
        """
        获取 Redis 键值
        
        Args:
            key: Redis 键名
        
        Returns:
            键值（字符串）或错误信息
        """
        async with get_redis_connection() as redis:
            try:
                value = await redis.get(key)
                if value is None:
                    return json.dumps({"exists": False, "value": None}, ensure_ascii=False)
                return json.dumps({"exists": True, "value": value}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_set(key: str, value: str, expire_seconds: Optional[int] = None) -> str:
        """
        设置 Redis 键值
        
        Args:
            key: Redis 键名
            value: 键值
            expire_seconds: 过期时间（秒），不传则永不过期
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                if expire_seconds:
                    await redis.setex(key, expire_seconds, value)
                else:
                    await redis.set(key, value)
                return json.dumps({"success": True, "msg": f"键 {key} 设置成功"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_delete(key: str) -> str:
        """
        删除 Redis 键
        
        Args:
            key: Redis 键名
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                deleted = await redis.delete(key)
                return json.dumps({
                    "success": True,
                    "deleted": deleted,
                    "msg": f"删除了 {deleted} 个键"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_keys(pattern: str = "*") -> str:
        """
        查找匹配的 Redis 键
        
        Args:
            pattern: 匹配模式，支持通配符 * 和 ?
        
        Returns:
            匹配的键列表
        """
        async with get_redis_connection() as redis:
            try:
                keys = await redis.keys(pattern)
                return json.dumps({
                    "count": len(keys),
                    "keys": keys[:100]  # 限制返回数量
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_exists(key: str) -> str:
        """
        检查 Redis 键是否存在
        
        Args:
            key: Redis 键名
        
        Returns:
            是否存在
        """
        async with get_redis_connection() as redis:
            try:
                exists = await redis.exists(key)
                return json.dumps({"exists": bool(exists)}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_ttl(key: str) -> str:
        """
        获取 Redis 键的剩余过期时间
        
        Args:
            key: Redis 键名
        
        Returns:
            剩余秒数（-1 表示永不过期，-2 表示键不存在）
        """
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
    
    @mcp.tool()
    async def redis_expire(key: str, seconds: int) -> str:
        """
        设置 Redis 键的过期时间
        
        Args:
            key: Redis 键名
            seconds: 过期时间（秒）
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                result = await redis.expire(key, seconds)
                if result:
                    return json.dumps({"success": True, "msg": f"键 {key} 将在 {seconds} 秒后过期"}, ensure_ascii=False)
                else:
                    return json.dumps({"success": False, "msg": "键不存在"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    # ==================== Hash 操作 ====================
    
    @mcp.tool()
    async def redis_hget(key: str, field: str) -> str:
        """
        获取 Hash 字段值
        
        Args:
            key: Redis 键名
            field: Hash 字段名
        
        Returns:
            字段值
        """
        async with get_redis_connection() as redis:
            try:
                value = await redis.hget(key, field)
                if value is None:
                    return json.dumps({"exists": False, "value": None}, ensure_ascii=False)
                return json.dumps({"exists": True, "value": value}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_hset(key: str, field: str, value: str) -> str:
        """
        设置 Hash 字段值
        
        Args:
            key: Redis 键名
            field: Hash 字段名
            value: 字段值
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                await redis.hset(key, field, value)
                return json.dumps({"success": True, "msg": f"Hash {key}.{field} 设置成功"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_hgetall(key: str) -> str:
        """
        获取 Hash 所有字段和值
        
        Args:
            key: Redis 键名
        
        Returns:
            所有字段和值
        """
        async with get_redis_connection() as redis:
            try:
                data = await redis.hgetall(key)
                return json.dumps({
                    "count": len(data),
                    "data": data
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_hdel(key: str, field: str) -> str:
        """
        删除 Hash 字段
        
        Args:
            key: Redis 键名
            field: Hash 字段名
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                deleted = await redis.hdel(key, field)
                return json.dumps({
                    "success": True,
                    "deleted": deleted,
                    "msg": f"删除了 {deleted} 个字段"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    # ==================== List 操作 ====================
    
    @mcp.tool()
    async def redis_lrange(key: str, start: int = 0, end: int = -1) -> str:
        """
        获取 List 范围内的元素
        
        Args:
            key: Redis 键名
            start: 起始索引（默认 0）
            end: 结束索引（默认 -1 表示最后一个）
        
        Returns:
            元素列表
        """
        async with get_redis_connection() as redis:
            try:
                items = await redis.lrange(key, start, end)
                return json.dumps({
                    "count": len(items),
                    "items": items
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_lpush(key: str, value: str) -> str:
        """
        从左侧插入 List 元素
        
        Args:
            key: Redis 键名
            value: 要插入的值
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                length = await redis.lpush(key, value)
                return json.dumps({
                    "success": True,
                    "length": length,
                    "msg": f"插入成功，列表长度: {length}"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_rpush(key: str, value: str) -> str:
        """
        从右侧插入 List 元素
        
        Args:
            key: Redis 键名
            value: 要插入的值
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                length = await redis.rpush(key, value)
                return json.dumps({
                    "success": True,
                    "length": length,
                    "msg": f"插入成功，列表长度: {length}"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_llen(key: str) -> str:
        """
        获取 List 长度
        
        Args:
            key: Redis 键名
        
        Returns:
            列表长度
        """
        async with get_redis_connection() as redis:
            try:
                length = await redis.llen(key)
                return json.dumps({"length": length}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    # ==================== Set 操作 ====================
    
    @mcp.tool()
    async def redis_smembers(key: str) -> str:
        """
        获取 Set 所有成员
        
        Args:
            key: Redis 键名
        
        Returns:
            成员列表
        """
        async with get_redis_connection() as redis:
            try:
                members = await redis.smembers(key)
                return json.dumps({
                    "count": len(members),
                    "members": list(members)
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_sadd(key: str, member: str) -> str:
        """
        添加 Set 成员
        
        Args:
            key: Redis 键名
            member: 要添加的成员
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                added = await redis.sadd(key, member)
                return json.dumps({
                    "success": True,
                    "added": added,
                    "msg": f"添加了 {added} 个成员"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_srem(key: str, member: str) -> str:
        """
        删除 Set 成员
        
        Args:
            key: Redis 键名
            member: 要删除的成员
        
        Returns:
            操作结果
        """
        async with get_redis_connection() as redis:
            try:
                removed = await redis.srem(key, member)
                return json.dumps({
                    "success": True,
                    "removed": removed,
                    "msg": f"删除了 {removed} 个成员"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    # ==================== 服务器信息 ====================
    
    @mcp.tool()
    async def redis_info(section: Optional[str] = None) -> str:
        """
        获取 Redis 服务器信息
        
        Args:
            section: 信息分类（server/clients/memory/stats/replication/cpu/keyspace），不传则返回全部
        
        Returns:
            服务器信息
        """
        async with get_redis_connection() as redis:
            try:
                if section:
                    info = await redis.info(section)
                else:
                    info = await redis.info()
                return json.dumps(info, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    async def redis_dbsize() -> str:
        """
        获取当前数据库的键数量
        
        Returns:
            键数量
        """
        async with get_redis_connection() as redis:
            try:
                size = await redis.dbsize()
                return json.dumps({"dbsize": size}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)
