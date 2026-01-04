import request from '@/utils/http'

/** 用户信息接口 */
export interface UserInfo {
  /** 用户ID */
  id: string
  /** 用户名 */
  username: string
  /** 昵称 */
  nickname?: string
  /** 邮箱 */
  email?: string | null
  /** 手机号 */
  phone?: string | null
  /** 头像 */
  avatar?: string | null
  /** 性别：0-未知，1-男，2-女 */
  gender?: number
  /** 状态：0-禁用，1-启用 */
  status?: number
  /** 用户身份标识：0-超级管理员，1-管理员，2-部门管理员，3-普通用户 */
  user_type?: number
  /** 部门ID */
  department_id?: string
  /** 部门名称 */
  department_name?: string
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

/** 用户角色信息接口 */
export interface UserRoleInfo {
  /** ID */
  id: string
  /** 用户ID */
  user_id: string
  /** 角色ID */
  role_id: string
  /** 角色名称 */
  role_name: string
  /** 角色编码 */
  role_code: string
  /** 角色描述 */
  role_description: string
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

/** 用户权限信息接口 */
export interface UserPermissionInfo {
  /** 权限ID */
  permission_id: string
  /** 权限名称 */
  permission_name: string
  /** 权限标识 */
  permission_auth: string
  /** 权限类型：0-菜单，1-按钮，2-API */
  permission_type: number
  /** 父权限ID */
  parent_id?: string | null
  /** 角色ID */
  role_id: string
  /** 角色名称 */
  role_name: string
  /** API路径（仅API权限） */
  api_path?: string
  /** API方法（仅API权限） */
  api_method?: string
  /** 创建时间 */
  created_at: string
  /** 子权限列表（用于树形结构） */
  children?: UserPermissionInfo[]
}

/** 用户查询参数接口 */
export interface UserQueryParams {
  /** 当前页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
  /** 用户名（模糊查询） */
  username?: string
  /** 昵称（模糊查询） */
  nickname?: string
  /** 手机号（模糊查询） */
  phone?: string
  /** 邮箱（模糊查询） */
  email?: string
  /** 性别 */
  gender?: number
  /** 用户状态：0-禁用，1-启用 */
  status?: number
  /** 所属部门ID */
  department_id?: string
  /** 多个部门ID，逗号分隔 */
  department_ids?: string
}

/** 添加用户参数接口 */
export interface AddUserParams {
  /** 用户名 */
  username: string
  /** 密码 */
  password: string
  /** 昵称 */
  nickname: string
  /** 邮箱 */
  email?: string
  /** 手机号 */
  phone?: string
  /** 性别：0-女，1-男 */
  gender?: number
  /** 状态：0-禁用，1-启用 */
  status?: number
  /** 用户身份标识：0-超级管理员，1-管理员，2-部门管理员，3-普通用户 */
  user_type: number
  /** 所属部门ID */
  department_id: string
}

/** 更新用户参数接口 */
export interface UpdateUserParams {
  /** 用户名 */
  username: string
  /** 昵称 */
  nickname?: string
  /** 邮箱 */
  email?: string
  /** 手机号 */
  phone?: string
  /** 头像 */
  avatar?: string
  /** 性别：0-未知，1-男，2-女 */
  gender?: number
  /** 状态：0-禁用，1-启用 */
  status?: number
  /** 用户身份标识：0-超级管理员，1-管理员，2-部门管理员，3-普通用户 */
  user_type: number
  /** 所属部门ID */
  department_id?: string
}

/** 重置密码参数接口 */
export interface ResetPasswordParams {
  /** 新密码 */
  password: string
}

/** 用户角色分配参数接口 */
export interface UserRoleParams {
  /** 用户ID */
  user_id: string
  /** 角色ID列表 */
  role_ids: string[]
}

// API响应数据类型（不包含code,msg,success等通用字段）
export interface UserListData {
  result: UserInfo[]
  total: number
  page: number
  pageSize: number
}

export interface UserRoleListData {
  result: UserRoleInfo[]
}

export interface UserPermissionListData {
  result: UserPermissionInfo[]
}

/** 删除用户列表参数接口 */
export interface DeleteUserListParams {
  /** 用户ID列表 */
  ids: string[]
}

/**
 * 获取用户列表
 * @param params 查询参数
 * @returns 用户列表数据
 */
export const fetchUserList = (params: UserQueryParams) => {
  return request.get<UserListData>({
    url: '/api/user/list',
    params
  })
}

/**
 * 获取用户详情
 * @param id 用户ID
 * @returns 用户详情数据
 */
export const fetchUserInfo = (id: string) => {
  return request.get<UserInfo>({
    url: `/api/user/info/${id}`
  })
}

/**
 * 添加用户
 * @param params 用户信息
 * @returns 操作结果
 */
export const addUser = (params: AddUserParams) => {
  return request.post<null>({
    url: '/api/user/add',
    data: params
  })
}

/**
 * 更新用户
 * @param id 用户ID
 * @param params 更新参数
 * @returns 操作结果
 */
export const updateUser = (id: string, params: UpdateUserParams) => {
  return request.put<null>({
    url: `/api/user/update/${id}`,
    data: params
  })
}

/**
 * 删除用户
 * @param id 用户ID
 * @returns 操作结果
 */
export const deleteUser = (id: string) => {
  return request.delete<null>({
    url: `/api/user/delete/${id}`
  })
}

/**
 * 批量删除用户
 * @param params 删除参数
 * @returns 操作结果
 */
export const deleteUserList = (params: DeleteUserListParams) => {
  return request.post<null>({
    url: '/api/user/deleteUserList',
    data: params
  })
}

/**
 * 重置用户密码
 * @param id 用户ID
 * @param params 重置密码参数
 * @returns 操作结果
 */
export const resetUserPassword = (id: string, params: ResetPasswordParams) => {
  return request.put<null>({
    url: `/api/user/resetPassword/${id}`,
    data: params
  })
}

/**
 * 获取用户角色列表
 * @param id 用户ID
 * @returns 用户角色列表
 */
export const fetchUserRoleList = (id: string) => {
  return request.get<UserRoleListData>({
    url: `/api/user/roleList/${id}`
  })
}

/**
 * 获取用户权限列表
 * @param id 用户ID
 * @returns 用户权限列表
 */
export const fetchUserPermissionList = (id: string) => {
  return request.get<UserPermissionListData>({
    url: `/api/user/permissionList/${id}`
  })
}

/**
 * 分配用户角色
 * @param params 角色分配参数
 * @returns 操作结果
 */
export const assignUserRoles = (params: UserRoleParams) => {
  return request.post<null>({
    url: '/api/user/addRole',
    data: params
  })
}
