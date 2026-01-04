/**
 * 配置管理 API
 */

import request from '@/utils/http'

/** 配置类型常量 */
export const ConfigType = {
  /** 用户自定义 */
  USER_DEFINED: false,
  /** 系统内置 */
  SYSTEM_BUILT_IN: true
} as const

/** 配置类型 */
export type ConfigTypeValue = (typeof ConfigType)[keyof typeof ConfigType]

/** 配置分组常量 */
export const ConfigGroup = {
  SYSTEM: 'system',
  EMAIL: 'email',
  MAP: 'map',
  UPLOAD: 'upload',
  SECURITY: 'security',
  ACCOUNT: 'account'
} as const

/** 配置分组标签 */
export const ConfigGroupLabels: Record<string, string> = {
  system: '系统配置',
  email: '邮件配置',
  map: '地图配置',
  upload: '上传配置',
  security: '安全配置',
  account: '账户配置'
}

/** 配置信息接口 */
export interface ConfigInfo {
  /** 配置ID */
  id: string
  /** 配置名称 */
  name: string
  /** 配置键名 */
  key: string
  /** 配置值 */
  value: string
  /** 配置分组 */
  group?: string
  /** 配置类型：true-系统内置，false-用户自定义 */
  type: boolean
  /** 备注信息 */
  remark?: string | null
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

/** 配置搜索参数接口 */
export interface ConfigSearchParams {
  /** 当前页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 配置名称（模糊搜索） */
  name?: string
  /** 配置键名（模糊搜索） */
  key?: string
  /** 配置分组 */
  group?: string
  /** 配置类型筛选 */
  type?: boolean
}

/** 添加/编辑配置参数接口 */
export interface ConfigFormParams {
  /** 配置名称 */
  name: string
  /** 配置键名 */
  key: string
  /** 配置值 */
  value: string
  /** 配置分组 */
  group?: string
  /** 配置类型：true-系统内置，false-用户自定义 */
  type?: boolean
  /** 备注信息 */
  remark?: string
}

/** 配置列表响应数据接口 */
export interface ConfigListResponse {
  /** 总条目数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页数量 */
  pageSize: number
  /** 配置列表 */
  result: ConfigInfo[]
}

/** 配置分组数据接口 */
export interface ConfigGroupData {
  /** 分组标识 */
  group: string
  /** 分组显示名称 */
  label: string
  /** 分组下的配置列表 */
  configs: ConfigInfo[]
}

/**
 * 获取配置列表
 * @param params 搜索参数
 * @returns 配置列表数据
 */
export const fetchConfigList = (params: ConfigSearchParams) =>
  request.get<ConfigListResponse>({
    url: '/api/config/list',
    params
  })

/**
 * 获取配置详情
 * @param id 配置ID
 * @returns 配置详情数据
 */
export const fetchConfigInfo = (id: string) =>
  request.get<ConfigInfo>({
    url: `/api/config/info/${id}`
  })

/**
 * 添加配置
 * @param params 配置信息
 * @returns 操作结果
 */
export const fetchAddConfig = (params: ConfigFormParams) =>
  request.post<null>({
    url: '/api/config/add',
    data: params
  })

/**
 * 更新配置
 * @param id 配置ID
 * @param params 配置信息
 * @returns 操作结果
 */
export const fetchUpdateConfig = (id: string, params: ConfigFormParams) =>
  request.put<null>({
    url: `/api/config/update/${id}`,
    data: params
  })

/**
 * 删除配置
 * @param id 配置ID
 * @returns 操作结果
 */
export const fetchDeleteConfig = (id: string) =>
  request.delete<null>({
    url: `/api/config/delete/${id}`
  })

/**
 * 批量删除配置
 * @param ids 配置ID列表
 * @returns 操作结果
 */
export const fetchDeleteConfigList = (ids: string[]) =>
  request.post<null>({
    url: '/api/config/deleteList',
    data: { ids }
  })

/**
 * 获取所有配置分组
 * @returns 配置分组数据
 */
export const fetchConfigGroups = () =>
  request.get<ConfigGroupData[]>({
    url: '/api/config/groups'
  })

/**
 * 获取指定分组的配置
 * @param group 分组标识
 * @returns 配置列表
 */
export const fetchGroupConfigs = (group: string) =>
  request.get<ConfigInfo[]>({
    url: `/api/config/group/${group}`
  })

/**
 * 批量更新分组配置
 * @param group 分组标识
 * @param configs 配置列表
 * @returns 操作结果
 */
export const fetchUpdateGroupConfigs = (group: string, configs: Array<{ key: string; value: string }>) =>
  request.put<null>({
    url: `/api/config/group/${group}`,
    data: { configs }
  })

/**
 * 刷新配置缓存
 * @returns 操作结果
 */
export const fetchRefreshConfigCache = () =>
  request.post<null>({
    url: '/api/config/refresh'
  })
