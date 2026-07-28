/**
 * 角色管理 API
 */

import request from '@/utils/http'

/** 角色基础信息接口 */
export interface RoleInfo {
  /** 角色ID */
  id: string
  /** 角色名称 */
  name: string
  /** 角色编码 */
  code: string
  /** 角色描述 */
  description: string
  /** 角色状态：0-禁用，1-启用 */
  status: number
  /** 所属部门ID */
  department_id: string
  /** 所属部门名称 */
  department_name?: string
  /** 部门负责人 */
  department_principal?: string
  /** 部门电话 */
  department_phone?: string
  /** 部门邮箱 */
  department_email?: string
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
  /** 角色关联的权限摘要 */
  permissions?: RolePermissionBinding[]
  menu_ids?: string[]
  button_ids?: string[]
  api_ids?: string[]
}

/** 角色权限绑定摘要 */
export interface RolePermissionBinding {
  /** 权限对象（权限ID） */
  obj: string
  /** 权限动作（menu/button/api） */
  act: string
}

/** API 权限项 */
export interface ApiPermission {
  /** API 路径 */
  path: string
  /** HTTP 方法 */
  method: string
}

/** 角色权限信息接口 */
export interface RolePermissionInfo {
  /** 权限ID */
  permission_id: string
  /** 父级权限ID */
  permission_parent_id: string
  /** 权限名称 */
  permission_name: string
  /** 权限标识 */
  permission_auth: string
  /** 权限类型：0-菜单，1-按钮，2-接口 */
  permission_type: number
  /** 权限类型：menu/button/api */
  perm_type: string
  /** 角色ID */
  role_id: string
  /** 角色名称 */
  role_name: string
  /** 角色编码 */
  role_code: string
}

/** 角色查询参数接口 */
export interface RoleQueryParams {
  /** 当前页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 角色名称（模糊查询） */
  name?: string
  /** 角色编码（模糊查询） */
  code?: string
  /** 角色描述（模糊查询） */
  description?: string
  /** 所属部门ID */
  department_id?: string
  /** 多个部门ID，逗号分隔 */
  department_ids?: string
  /** 角色状态：0-禁用，1-启用 */
  status?: number
}

/** 添加角色参数接口 */
export interface AddRoleParams {
  /** 角色名称 */
  name: string
  /** 角色编码 */
  code: string
  /** 角色描述 */
  description?: string
  /** 角色状态：0-禁用，1-启用 */
  status: number
  /** 所属部门ID */
  department_id: string
}

/** 更新角色参数接口 */
export interface UpdateRoleParams extends AddRoleParams {
  /** 角色ID */
  id: string
}

/** 角色权限分配参数接口 */
export interface RolePermissionParams {
  /** 权限ID列表（包含菜单、按钮、接口权限） */
  permission_ids: string[]
}

/** 批量删除参数接口 */
export interface DeleteRoleListParams {
  /** 角色ID列表 */
  ids: string[]
}

/** 角色列表响应数据 */
export interface RoleListResponse {
  /** 角色列表 */
  result: RoleInfo[]
  /** 总数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页大小 */
  pageSize: number
}

/** 角色详情响应数据 */
export interface RoleInfoResponse extends RoleInfo {
  /** 角色权限绑定摘要 */
  permissions?: RolePermissionBinding[]
  /** 菜单权限ID列表 */
  menu_ids?: string[]
  /** 按钮权限ID列表 */
  button_ids?: string[]
  /** API权限ID列表 */
  api_ids?: string[]
}

/** 角色权限列表响应数据 */
export interface RolePermissionListResponse {
  result: RolePermissionInfo[]
  actual_permission_ids?: string[]
  menu_ids?: string[]
  button_ids?: string[]
  api_ids?: string[]
  api_permission_ids?: string[]
}

/**
 * 获取角色列表
 * @param params 查询参数
 * @returns 角色列表数据
 */
export const fetchRoleList = (params: RoleQueryParams) => {
  return request.get<RoleListResponse>({
    url: '/api/role/list',
    params
  })
}

/**
 * 获取角色详情
 * @param id 角色ID
 * @returns 角色详情数据
 */
export const fetchRoleInfo = (id: string) => {
  return request.get<RoleInfoResponse>({
    url: `/api/role/info/${id}`
  })
}

/**
 * 新增角色
 * @param params 角色参数
 * @returns 操作结果
 */
export const addRole = (params: AddRoleParams) => {
  return request.post<null>({
    url: '/api/role/add',
    data: params
  })
}

/**
 * 更新角色
 * @param id 角色ID
 * @param params 角色参数
 * @returns 操作结果
 */
export const updateRole = (id: string, params: UpdateRoleParams) => {
  return request.put<null>({
    url: `/api/role/update/${id}`,
    data: params
  })
}

/**
 * 删除角色
 * @param id 角色ID
 * @returns 操作结果
 */
export const deleteRole = (id: string) => {
  return request.delete<null>({
    url: `/api/role/delete/${id}`
  })
}

/**
 * 批量删除角色
 * @param params 批量删除参数
 * @returns 操作结果
 */
export const deleteRoleList = (params: DeleteRoleListParams) => {
  return request.post<null>({
    url: '/api/role/deleteList',
    data: params
  })
}

/**
 * 获取角色权限列表
 * @param roleId 角色ID
 * @returns 角色权限列表
 */
export const fetchRolePermissionList = (roleId: string) => {
  return request.get<RolePermissionListResponse>({
    url: `/api/role/permissionList/${roleId}`
  })
}

/**
 * 获取角色权限详情
 * @param roleId 角色ID
 * @param permissionId 权限ID
 * @returns 角色权限详情
 */
export const fetchRolePermissionInfo = (roleId: string, permissionId: string) => {
  return request.get<RolePermissionInfo>({
    url: `/api/role/permissionInfo/${roleId}`,
    params: { role_id: roleId, permission_id: permissionId }
  })
}

/**
 * 分配角色权限
 * @param roleId 角色ID
 * @param params 权限参数
 * @returns 操作结果
 */
export const assignRolePermissions = (roleId: string, params: RolePermissionParams) => {
  return request.post<null>({
    url: `/api/role/updatePermission/${roleId}`,
    data: params
  })
}

/**
 * 添加角色权限
 * @param roleId 角色ID
 * @param params 权限参数
 * @returns 操作结果
 */
export const addRolePermissions = (roleId: string, params: RolePermissionParams) => {
  return request.post<null>({
    url: `/api/role/addPermission/${roleId}`,
    data: params
  })
}

/**
 * 删除角色权限
 * @param roleId 角色ID
 * @param permissionId 权限ID
 * @returns 操作结果
 */
export const deleteRolePermission = (roleId: string, permissionId: string) => {
  return request.delete<null>({
    url: `/api/role/deletePermission/${roleId}`,
    params: { role_id: roleId, permission_id: permissionId }
  })
}
