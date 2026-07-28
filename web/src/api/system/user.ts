import request from '@/utils/http'

export interface UserInfo {
  id: string
  username: string
  nickname?: string
  email?: string | null
  phone?: string | null
  avatar?: string | null
  gender?: number
  status?: number
  user_type?: number
  department_id?: string
  department_name?: string
  created_at: string
  updated_at: string
}

export interface UserRoleInfo {
  id: string
  user_id: string
  role_id: string
  role_name: string
  role_code: string
  role_description: string
  created_at: string
  updated_at: string
}

export interface UserPermissionInfo {
  permission_id: string
  permission_name: string
  permission_auth?: string
  permission_code?: string
  permission_type: 'menu' | 'button'
  parent_id?: string | null
  role_name?: string
  roles: Array<{
    id: string | null
    name: string
  }>
  children?: UserPermissionInfo[]
}

export interface UserQueryParams {
  page?: number
  pageSize?: number
  username?: string
  nickname?: string
  phone?: string
  email?: string
  gender?: number
  status?: number
  department_id?: string
  department_ids?: string
}

export interface AddUserParams {
  username: string
  password: string
  nickname: string
  email?: string
  phone?: string
  gender?: number
  status?: number
  user_type: number
  department_id: string
}

export interface UpdateUserParams {
  username: string
  nickname?: string
  email?: string
  phone?: string
  avatar?: string
  gender?: number
  status?: number
  user_type: number
  department_id?: string
}

export interface ResetPasswordParams {
  password: string
}

export interface UserRoleParams {
  user_id: string
  role_ids: string[]
}

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
  roles?: string[]
  menus?: string[]
  buttons?: string[]
}

export interface DeleteUserListParams {
  ids: string[]
}

export const fetchUserList = (params: UserQueryParams) => {
  return request.get<UserListData>({
    url: '/api/user/list',
    params
  })
}

export const fetchUserInfo = (id: string) => {
  return request.get<UserInfo>({
    url: `/api/user/info/${id}`
  })
}

export const addUser = (params: AddUserParams) => {
  return request.post<null>({
    url: '/api/user/add',
    data: params
  })
}

export const updateUser = (id: string, params: UpdateUserParams) => {
  return request.put<null>({
    url: `/api/user/update/${id}`,
    data: params
  })
}

export const deleteUser = (id: string) => {
  return request.delete<null>({
    url: `/api/user/delete/${id}`
  })
}

export const deleteUserList = (params: DeleteUserListParams) => {
  return request.post<null>({
    url: '/api/user/deleteUserList',
    data: params
  })
}

export const resetUserPassword = (id: string, params: ResetPasswordParams) => {
  return request.put<null>({
    url: `/api/user/resetPassword/${id}`,
    data: params
  })
}

export const fetchUserRoleList = (id: string) => {
  return request.get<UserRoleListData>({
    url: `/api/user/roleList/${id}`
  })
}

export const fetchUserPermissionList = (id: string) => {
  return request.get<UserPermissionListData>({
    url: `/api/user/permissionList/${id}`
  })
}

export const assignUserRoles = (params: UserRoleParams) => {
  return request.post<null>({
    url: '/api/user/addRole',
    data: params
  })
}
