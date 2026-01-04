/**
 * 权限管理 API
 */

import request from '@/utils/http'

export interface PermissionInfo {
  /** 权限ID */
  id?: string
  /** 菜单类型：0-菜单，1-按钮，2-API */
  menu_type: number
  /** 父权限ID */
  parent_id?: string
  /** 权限名称（英文标识） */
  name?: string
  /** 权限标题（显示名称） */
  title?: string
  /** 路由路径 */
  path?: string
  /** 组件路径 */
  component?: string
  /** 图标代码 */
  icon?: string
  /** 是否显示徽章 */
  showBadge?: boolean
  /** 徽章文本 */
  showTextBadge?: string
  /** 是否隐藏 */
  isHide?: boolean
  /** 是否隐藏标签页 */
  isHideTab?: boolean
  /** 外部链接 */
  link?: string
  /** 是否内嵌iframe */
  isIframe?: boolean
  /** 是否缓存 */
  keepAlive?: boolean
  /** 是否一级菜单 */
  isFirstLevel?: boolean
  /** 是否固定标签页 */
  fixedTab?: boolean
  /** 激活路径 */
  activePath?: string
  /** 是否全屏页面 */
  isFullPage?: boolean
  /** 排序权重 */
  order?: number
  /** 最低用户身份要求：0-超级管理员，1-管理员，2-部门管理员，3-所有用户 */
  min_user_type?: number
  /** 权限标题（按钮类型使用） */
  authTitle?: string
  /** 权限标识（按钮类型使用） */
  authMark?: string
  /** API路径（API类型使用） */
  api_path?: string
  /** API方法列表（API类型使用）：['GET', 'POST', 'PUT', 'DELETE'] */
  api_method?: string | string[]
  /** 数据权限范围：1-全部，2-本部门及下属，3-仅本部门，4-仅本人 */
  data_scope?: number
  /** 备注说明 */
  remark?: string
  /** 创建时间 */
  created_at?: string
  /** 更新时间 */
  updated_at?: string
  /** 子权限列表 */
  children?: PermissionInfo[]
}

export interface PermissionTree extends PermissionInfo {
  /** 子权限树 */
  children?: PermissionTree[]
}

/** 权限列表响应数据 */
export interface PermissionListResponse {
  /** 权限列表 */
  result: PermissionInfo[]
  /** 总数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页大小 */
  pageSize: number
}

/** 权限树响应数据 */
export interface PermissionTreeResponse {
  /** 权限树列表 */
  result: PermissionTree[]
  /** 总数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页大小 */
  pageSize: number
}

/** 按钮权限响应数据 */
export interface ButtonPermissionResponse {
  /** 按钮权限列表 */
  result: PermissionInfo[]
  /** 总数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页大小 */
  pageSize: number
}

/** 基础响应结构 */
export interface BaseResponse<T = any> {
  /** 响应码 */
  code: number
  /** 响应消息 */
  msg: string
  /** 是否成功 */
  success: boolean
  /** 响应时间 */
  time: string
  /** 响应数据 */
  data?: T
}

/**
 * 获取权限树形结构
 * @returns 权限树数据
 */
export const fetchPermissionTree = () => {
  return request.get<PermissionTreeResponse>({
    url: '/api/permission/tree'
  })
}

/**
 * 获取权限列表
 * @param params 查询参数
 * @returns 权限列表数据
 */
export const fetchPermissionList = (params: {
  /** 当前页码 */
  page?: number
  /** 每页大小 */
  pageSize?: number
  /** 菜单类型：0-菜单，1-按钮 */
  menu_type?: number
  /** 父权限ID */
  parent_id?: string
  /** 权限名称 */
  name?: string
  /** 权限标题 */
  title?: string
}) => {
  return request.get<PermissionListResponse>({
    url: '/api/permission/list',
    params
  })
}

/**
 * 获取权限详情
 * @param id 权限ID
 * @returns 权限详情数据
 */
export const fetchPermissionInfo = (id: string) => {
  return request.get<PermissionInfo>({
    url: `/api/permission/info/${id}`
  })
}

/**
 * 添加权限
 * @param data 权限数据
 * @returns 操作结果
 */
export const addPermission = (data: Partial<PermissionInfo>) => {
  return request.post<null>({
    url: '/api/permission/add',
    data
  })
}

/**
 * 更新权限
 * @param id 权限ID
 * @param data 权限数据
 * @returns 操作结果
 */
export const updatePermission = (id: string, data: Partial<PermissionInfo>) => {
  return request.put<null>({
    url: `/api/permission/update/${id}`,
    data
  })
}

/**
 * 删除权限
 * @param id 权限ID
 * @returns 操作结果
 */
export const deletePermission = (id: string) => {
  return request.delete<null>({
    url: `/api/permission/delete/${id}`
  })
}

/**
 * 获取指定菜单的按钮权限列表
 * @param parentId 父菜单ID
 * @returns 按钮权限列表
 */
export const fetchMenuButtons = (parentId: string) => {
  return request.get<ButtonPermissionResponse>({
    url: `/api/permission/buttons/${parentId}`
  })
}

/**
 * 添加按钮权限
 * @param data 按钮权限数据
 * @returns 操作结果
 */
export const addButtonPermission = (data: Partial<PermissionInfo>) => {
  return request.post<null>({
    url: '/api/permission/button/add',
    data
  })
}

/**
 * 更新按钮权限
 * @param id 按钮权限ID
 * @param data 按钮权限数据
 * @returns 操作结果
 */
export const updateButtonPermission = (id: string, data: Partial<PermissionInfo>) => {
  return request.put<null>({
    url: `/api/permission/button/update/${id}`,
    data
  })
}

/**
 * 删除按钮权限
 * @param id 按钮权限ID
 * @returns 操作结果
 */
export const deleteButtonPermission = (id: string) => {
  return request.delete<null>({
    url: `/api/permission/button/delete/${id}`
  })
}

/**
 * 获取API权限列表
 * @param params 查询参数
 * @returns API权限列表
 */
export const fetchApiPermissions = (params?: {
  page?: number
  pageSize?: number
  api_path?: string
  api_method?: string
}) => {
  return request.get<PermissionListResponse>({
    url: '/api/permission/api/list',
    params
  })
}

/**
 * 添加API权限
 * @param data API权限数据
 * @returns 操作结果
 */
export const addApiPermission = (data: {
  parent_id?: string
  title: string
  api_path: string
  api_method: string[]
  data_scope?: number
  min_user_type?: number
  remark?: string
}) => {
  return request.post<null>({
    url: '/api/permission/api/add',
    data
  })
}

/**
 * 更新API权限
 * @param id API权限ID
 * @param data API权限数据
 * @returns 操作结果
 */
export const updateApiPermission = (id: string, data: {
  parent_id?: string
  title: string
  api_path: string
  api_method: string[]
  data_scope?: number
  min_user_type?: number
  remark?: string
}) => {
  return request.put<null>({
    url: `/api/permission/api/update/${id}`,
    data
  })
}

/**
 * 删除API权限
 * @param id API权限ID
 * @returns 操作结果
 */
export const deleteApiPermission = (id: string) => {
  return request.delete<null>({
    url: `/api/permission/api/delete/${id}`
  })
}
