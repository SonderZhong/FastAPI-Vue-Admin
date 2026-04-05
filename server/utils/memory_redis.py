  # _*_ coding : UTF-8 _*_
# @Time : 2026/04/05
# @Author : sonder
# @File : memory_redis.py
# @Comment : 内存 Redis 模拟类，用于在没有 Redis 服务时提供基本功能

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict

from utils.log import logger


class MemoryRedis:
    """
    内存 Redis 模拟类
    
    提供基本的 Redis 操作接口，数据存储在内存中。
    适用于开发环境或不需要持久化的场景。
    
    注意：
    - 数据不持久化，重启后丢失
    - 不支持集群和主从复制
    - 性能优于真实 Redis（无网络开销）
    - 功能有限，仅实现常用操作
    """
    
    def __init__(self):
        """初始化内存存储"""
        self._data: Dict[str, Any] = {}
        self._expires: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        logger.info("使用内存模式模拟 Redis（数据不持久化）")
    
    async def ping(self) -> bool:
        """测试连接"""
        return True
    
    async def aclose(self):
        """关闭连接（清理资源）"""
        async with self._lock:
            self._data.clear()
            self._expires.clear()
        logger.info("内存 Redis 连接已关闭")
    
    def _is_expired(self, key: str) -> bool:
        """检查键是否过期"""
        if key in self._expires:
            if datetime.now() >= self._expires[key]:
                # 键已过期，删除
                del self._data[key]
                del self._expires[key]
                return True
        return False
    
    # ==================== 字符串操作 ====================
    
    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        async with self._lock:
            if self._is_expired(key):
                return None
            return self._data.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        设置键值
        
        Args:
            key: 键名
            value: 值
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置
        """
        async with self._lock:
            # 检查 nx 和 xx 条件
            exists = key in self._data and not self._is_expired(key)
            
            if nx and exists:
                return False
            if xx and not exists:
                return False
            
            # 设置值
            self._data[key] = str(value)
            
            # 设置过期时间
            if ex is not None:
                # ex 可能是秒数（int）或 timedelta 对象
                if isinstance(ex, timedelta):
                    self._expires[key] = datetime.now() + ex
                else:
                    self._expires[key] = datetime.now() + timedelta(seconds=ex)
            elif px is not None:
                # px 可能是毫秒数（int）或 timedelta 对象
                if isinstance(px, timedelta):
                    self._expires[key] = datetime.now() + px
                else:
                    self._expires[key] = datetime.now() + timedelta(milliseconds=px)
            elif key in self._expires:
                # 如果没有指定过期时间，移除旧的过期时间
                del self._expires[key]
            
            return True
    
    async def setex(self, key: str, time: Union[int, timedelta], value: str) -> bool:
        """设置键值对并指定过期时间（秒或timedelta）"""
        # setex 的参数顺序是 key, time, value
        # time 可以是秒数（int）或 timedelta 对象
        if isinstance(time, timedelta):
            return await self.set(key, value, ex=time)
        else:
            return await self.set(key, value, ex=time)
    
    async def delete(self, *keys: str) -> int:
        """删除一个或多个键"""
        async with self._lock:
            count = 0
            for key in keys:
                if key in self._data:
                    del self._data[key]
                    if key in self._expires:
                        del self._expires[key]
                    count += 1
            return count
    
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        async with self._lock:
            count = 0
            for key in keys:
                if key in self._data and not self._is_expired(key):
                    count += 1
            return count
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        async with self._lock:
            if key in self._data and not self._is_expired(key):
                self._expires[key] = datetime.now() + timedelta(seconds=seconds)
                return True
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间（秒）"""
        async with self._lock:
            if key not in self._data:
                return -2  # 键不存在
            if self._is_expired(key):
                return -2
            if key not in self._expires:
                return -1  # 永不过期
            
            remaining = (self._expires[key] - datetime.now()).total_seconds()
            return int(remaining) if remaining > 0 else -2
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        将键的值增加指定数量
        
        Args:
            key: 键名
            amount: 增加的数量，默认为 1
        
        Returns:
            增加后的值
        """
        async with self._lock:
            if self._is_expired(key):
                # 键已过期，视为不存在
                self._data[key] = str(amount)
                return amount
            
            current = self._data.get(key, "0")
            try:
                new_value = int(current) + amount
                self._data[key] = str(new_value)
                return new_value
            except ValueError:
                # 值不是整数，抛出错误
                raise ValueError(f"value is not an integer or out of range")
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """
        将键的值减少指定数量
        
        Args:
            key: 键名
            amount: 减少的数量，默认为 1
        
        Returns:
            减少后的值
        """
        return await self.incr(key, -amount)
    
    async def incrby(self, key: str, amount: int) -> int:
        """将键的值增加指定数量（incr 的别名）"""
        return await self.incr(key, amount)
    
    async def decrby(self, key: str, amount: int) -> int:
        """将键的值减少指定数量（decr 的别名）"""
        return await self.decr(key, amount)
    
    # ==================== 哈希操作 ====================
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段的值"""
        async with self._lock:
            if self._is_expired(name):
                return None
            hash_data = self._data.get(name)
            if isinstance(hash_data, dict):
                return hash_data.get(key)
            return None
    
    async def hset(self, name: str, key: str, value: Any) -> int:
        """设置哈希字段的值"""
        async with self._lock:
            if name not in self._data or not isinstance(self._data[name], dict):
                self._data[name] = {}
            
            is_new = key not in self._data[name]
            self._data[name][key] = str(value)
            return 1 if is_new else 0
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """获取哈希的所有字段和值"""
        async with self._lock:
            if self._is_expired(name):
                return {}
            hash_data = self._data.get(name)
            if isinstance(hash_data, dict):
                return hash_data.copy()
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希的一个或多个字段"""
        async with self._lock:
            if name not in self._data or not isinstance(self._data[name], dict):
                return 0
            
            count = 0
            for key in keys:
                if key in self._data[name]:
                    del self._data[name][key]
                    count += 1
            return count
    
    async def hexists(self, name: str, key: str) -> bool:
        """检查哈希字段是否存在"""
        async with self._lock:
            if self._is_expired(name):
                return False
            hash_data = self._data.get(name)
            if isinstance(hash_data, dict):
                return key in hash_data
            return False
    
    # ==================== 列表操作 ====================
    
    async def lpush(self, name: str, *values: Any) -> int:
        """从左侧插入列表元素"""
        async with self._lock:
            if name not in self._data or not isinstance(self._data[name], list):
                self._data[name] = []
            
            for value in reversed(values):
                self._data[name].insert(0, str(value))
            
            return len(self._data[name])
    
    async def rpush(self, name: str, *values: Any) -> int:
        """从右侧插入列表元素"""
        async with self._lock:
            if name not in self._data or not isinstance(self._data[name], list):
                self._data[name] = []
            
            for value in values:
                self._data[name].append(str(value))
            
            return len(self._data[name])
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """获取列表指定范围的元素"""
        async with self._lock:
            if self._is_expired(name):
                return []
            list_data = self._data.get(name)
            if isinstance(list_data, list):
                # 处理负索引
                if end == -1:
                    return list_data[start:]
                return list_data[start:end + 1]
            return []
    
    async def llen(self, name: str) -> int:
        """获取列表长度"""
        async with self._lock:
            if self._is_expired(name):
                return 0
            list_data = self._data.get(name)
            if isinstance(list_data, list):
                return len(list_data)
            return 0
    
    # ==================== 集合操作 ====================
    
    async def sadd(self, name: str, *values: Any) -> int:
        """向集合添加成员"""
        async with self._lock:
            if name not in self._data or not isinstance(self._data[name], set):
                self._data[name] = set()
            
            before_count = len(self._data[name])
            for value in values:
                self._data[name].add(str(value))
            
            return len(self._data[name]) - before_count
    
    async def srem(self, name: str, *values: Any) -> int:
        """从集合移除成员"""
        async with self._lock:
            if name not in self._data or not isinstance(self._data[name], set):
                return 0
            
            count = 0
            for value in values:
                if str(value) in self._data[name]:
                    self._data[name].remove(str(value))
                    count += 1
            
            return count
    
    async def smembers(self, name: str) -> set:
        """获取集合的所有成员"""
        async with self._lock:
            if self._is_expired(name):
                return set()
            set_data = self._data.get(name)
            if isinstance(set_data, set):
                return set_data.copy()
            return set()
    
    async def sismember(self, name: str, value: Any) -> bool:
        """检查成员是否在集合中"""
        async with self._lock:
            if self._is_expired(name):
                return False
            set_data = self._data.get(name)
            if isinstance(set_data, set):
                return str(value) in set_data
            return False
    
    # ==================== 管道操作 ====================
    
    def pipeline(self):
        """创建管道（简化实现，直接返回自身）"""
        return self
    
    async def execute(self):
        """执行管道命令（简化实现）"""
        return []
    
    # ==================== 其他操作 ====================
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        查找所有符合给定模式的键
        
        Args:
            pattern: 匹配模式，支持通配符 * 和 ?
                    * 匹配任意数量的字符
                    ? 匹配单个字符
        
        Returns:
            匹配的键列表
        """
        import re
        
        async with self._lock:
            # 清理过期键
            expired_keys = [k for k in self._data.keys() if self._is_expired(k)]
            
            # 将 Redis 模式转换为正则表达式
            # * 转换为 .*
            # ? 转换为 .
            # 转义其他特殊字符
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            regex_pattern = f"^{regex_pattern}$"
            
            try:
                compiled_pattern = re.compile(regex_pattern)
                matching_keys = [
                    key for key in self._data.keys()
                    if compiled_pattern.match(key) and not self._is_expired(key)
                ]
                return matching_keys
            except re.error:
                # 如果正则表达式无效，返回空列表
                logger.warning(f"无效的键匹配模式: {pattern}")
                return []
    
    async def dbsize(self) -> int:
        """
        返回当前数据库的键数量
        
        Returns:
            键的数量
        """
        async with self._lock:
            # 清理过期键
            expired_keys = [k for k in self._data.keys() if self._is_expired(k)]
            # 返回未过期的键数量
            return len(self._data) - len(expired_keys)
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 Redis 服务器信息（内存模式模拟）
        
        Args:
            section: 信息分类（server/memory/stats/commandstats等）
                    如果为 None，返回所有信息
        
        Returns:
            服务器信息字典
        """
        import sys
        import os
        from datetime import datetime
        
        async with self._lock:
            # 清理过期键
            expired_keys = [k for k in self._data.keys() if self._is_expired(k)]
            active_keys = len(self._data) - len(expired_keys)
            expires_count = len(self._expires)
            
            # 计算内存使用（粗略估算）
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                used_memory = memory_info.rss  # 实际物理内存
            except (ImportError, Exception):
                # 如果 psutil 不可用，使用估算值
                used_memory = len(str(self._data).encode()) + len(str(self._expires).encode())
            
            # 基础信息
            base_info = {
                # Server 信息
                'redis_version': '7.0.0-memory',
                'redis_mode': 'standalone',
                'os': sys.platform,
                'arch_bits': 64 if sys.maxsize > 2**32 else 32,
                'process_id': os.getpid(),
                'uptime_in_seconds': 0,  # 内存模式无法准确统计
                'uptime_in_days': 0,
                
                # Memory 信息
                'used_memory': used_memory,
                'used_memory_human': self._format_bytes(used_memory),
                'used_memory_rss': used_memory,
                'used_memory_peak': used_memory,
                'used_memory_peak_human': self._format_bytes(used_memory),
                'maxmemory': 0,  # 内存模式无限制
                'maxmemory_human': 'unlimited',
                'mem_fragmentation_ratio': 1.0,
                
                # Clients 信息
                'connected_clients': 1,  # 内存模式只有一个客户端
                'client_recent_max_input_buffer': 0,
                'client_recent_max_output_buffer': 0,
                'blocked_clients': 0,
                'total_connections_received': 1,
                
                # Stats 信息
                'total_commands_processed': 0,
                'instantaneous_ops_per_sec': 0,
                'total_net_input_bytes': 0,
                'total_net_output_bytes': 0,
                'keyspace_hits': 0,
                'keyspace_misses': 0,
                
                # Keyspace 信息
                'db0': {
                    'keys': active_keys,
                    'expires': expires_count,
                    'avg_ttl': 0
                }
            }
            
            # 根据 section 返回对应信息
            if section == 'server':
                return {k: v for k, v in base_info.items() 
                       if k in ['redis_version', 'redis_mode', 'os', 'arch_bits', 'process_id', 'uptime_in_seconds', 'uptime_in_days']}
            elif section == 'memory':
                return {k: v for k, v in base_info.items() 
                       if k.startswith('used_memory') or k.startswith('maxmemory') or k == 'mem_fragmentation_ratio'}
            elif section == 'clients':
                return {k: v for k, v in base_info.items() 
                       if 'client' in k or k == 'connected_clients' or k == 'blocked_clients' or k == 'total_connections_received'}
            elif section == 'stats':
                return {k: v for k, v in base_info.items() 
                       if 'commands' in k or 'ops' in k or 'net' in k or 'keyspace' in k}
            elif section == 'commandstats':
                # 返回空的命令统计（内存模式不统计）
                return {}
            elif section == 'keyspace':
                return {k: v for k, v in base_info.items() if k.startswith('db')}
            else:
                # 返回所有信息
                return base_info
    
    def _format_bytes(self, bytes_value: int) -> str:
        """格式化字节数为人类可读格式"""
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f}P"
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        pass
