/**
 * 缓存管理相关API接口
 */
import request from '@/utils/http'

/** 缓存监控信息 */
export interface CacheMonitor {
  /** 命令统计 */
  command_stats?: Array<{
    name: string
    value: number
    usec: number
    usec_per_call: number
  }>
  /** Key数量 */
  db_size?: number
  /** Redis信息 */
  info?: Record<string, any>
  /** 内存统计 */
  memory_stats?: {
    used_memory: number
    used_memory_human: string
    used_memory_rss: number
    used_memory_peak: number
    used_memory_peak_human: string
    maxmemory: number
    maxmemory_human: string
    mem_fragmentation_ratio: number
  }
  /** 连接统计 */
  connection_stats?: {
    connected_clients: number
    client_recent_max_input_buffer: number
    client_recent_max_output_buffer: number
    blocked_clients: number
    total_connections_received: number
  }
  /** 性能统计 */
  performance_stats?: {
    total_commands_processed: number
    instantaneous_ops_per_sec: number
    total_net_input_bytes: number
    total_net_output_bytes: number
    keyspace_hits: number
    keyspace_misses: number
    hit_rate: number
  }
  /** 键空间统计 */
  key_space_stats?: Array<{
    db: string
    keys: number
    expires: number
    avg_ttl: number
  }>
}

/** 缓存信息 */
export interface CacheInfo {
  /** 缓存键名 */
  cache_key?: string
  /** 缓存名称 */
  cache_name?: string
  /** 缓存内容 */
  cache_value?: any
  /** 备注 */
  remark?: string
  /** 生存时间（秒） */
  ttl?: number
  /** 过期时间 */
  expire_time?: string
}

/** 缓存监控响应 */
export interface CacheMonitorResponse {
  data: CacheMonitor
}

/** 缓存信息列表响应 */
export interface CacheInfoListResponse {
  data: CacheInfo[]
}

/** 缓存键名列表响应 */
export interface CacheKeysListResponse {
  data: string[]
}

/** 缓存键搜索参数 */
export interface CacheKeySearchParams {
  page?: number
  size?: number
  search?: string
}

/** 缓存键分页响应 */
export interface CacheKeysPageResponse {
  result: Array<{ key: string }>
  total: number
  page: number
  size: number
}

/** 更新缓存值参数 */
export interface UpdateCacheValueParams {
  cache_value: string
}

/**
 * 获取缓存监控信息
 */
export const fetchCacheMonitor = () =>
  request.get<CacheMonitor>({
    url: '/api/cache/monitor'
  })

/**
 * 获取缓存名称列表
 */
export const fetchCacheNames = () =>
  request.get<CacheInfo[]>({
    url: '/api/cache/names'
  })

/**
 * 获取缓存键名列表（分页）
 */
export const fetchCacheKeys = (cacheName: string, params?: CacheKeySearchParams) =>
  request.get<CacheKeysPageResponse>({
    url: `/api/cache/keys/${cacheName}`,
    params
  })

/**
 * 获取缓存详细信息
 */
export const fetchCacheDetail = (cacheName: string, cacheKey: string) =>
  request.get<CacheInfo>({
    url: `/api/cache/info/${cacheName}/${cacheKey}`
  })

/**
 * 通过键名删除缓存
 */
export const deleteCacheByName = (name: string) =>
  request.delete<null>({
    url: `/api/cache/cacheName/${name}`
  })

/**
 * 通过键值删除缓存
 */
export const deleteCacheByKey = (key: string) =>
  request.delete<null>({
    url: `/api/cache/cacheKey/${key}`
  })

/**
 * 更新缓存值
 */
export const updateCacheValue = (
  cacheName: string,
  cacheKey: string,
  params: UpdateCacheValueParams
) =>
  request.put<null>({
    url: `/api/cache/info/${cacheName}/${cacheKey}`,
    data: params
  })

/**
 * 删除所有缓存
 */
export const deleteAllCache = () =>
  request.delete<null>({
    url: '/api/cache/clearAll'
  })
