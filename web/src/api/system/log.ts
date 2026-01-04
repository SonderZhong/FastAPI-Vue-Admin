import request from '@/utils/http'

// 登录日志搜索参数
export interface LoginLogSearchParams {
  page?: number
  pageSize?: number
  username?: string
  nickname?: string
  department_id?: string
  startTime?: string
  endTime?: string
  status?: number
}

// 登录日志信息
export interface LoginLogInfo {
  online: boolean
  id: string
  user_id: string
  username: string
  user_nickname: string
  department_id: string
  department_name: string
  login_ip: string
  login_location: string
  browser: string
  os: string
  status: number
  session_id: string
  created_at: string
  updated_at: string
}

// 登录日志列表响应
export interface LoginLogListResponse {
  total: number
  page: number
  pageSize: number
  result: LoginLogInfo[]
}

// 批量删除参数
export interface DeleteListParams {
  ids: string[]
}

// 操作日志搜索参数
export interface OperationLogSearchParams {
  page?: number
  pageSize?: number
  operation_name?: string
  operation_type?: string
  operator_name?: string
  operator_nickname?: string
  department_id?: string
  startTime?: string
  endTime?: string
  status?: number
}

// 操作日志信息
export interface OperationLogInfo {
  id: string
  operation_name: string
  operation_type: string
  operator_id: string
  operator_name: string
  operator_nickname: string
  department_id: string
  department_name: string
  request_method: string
  request_path: string
  request_params: string
  response_result: string
  host: string
  location: string
  browser: string
  os: string
  user_agent: string
  status: number
  cost_time: number
  created_at: string
  updated_at: string
}

// 操作日志列表响应
export interface OperationLogListResponse {
  total: number
  page: number
  pageSize: number
  result: OperationLogInfo[]
  todayCount?: number
}

/**
 * 获取登录日志列表
 * @param params 搜索参数
 * @returns 登录日志列表数据
 */
export const fetchLoginLogList = (params: LoginLogSearchParams) =>
  request.get<LoginLogListResponse>({
    url: '/api/log/login',
    params
  })

/**
 * 强制注销用户
 * @param sessionId 会话ID
 * @returns 注销结果
 */
export const fetchLogoutUser = (sessionId: string) =>
  request.post<null>({
    url: `/api/log/logout/${sessionId}`,
    showSuccessMessage: true
  })

/**
 * 批量强制注销用户
 * @param params 批量参数
 * @returns 注销结果
 */
export const fetchLogoutUserList = (params: DeleteListParams) =>
  request.post<null>({
    url: '/api/log/logoutList',
    data: params,
    showSuccessMessage: true
  })

/**
 * 删除登录日志
 * @param id 日志ID
 * @returns 删除结果
 */
export const fetchDeleteLoginLog = (id: string) =>
  request.post<null>({
    url: `/api/log/delete/login/${id}`,
    showSuccessMessage: true
  })

/**
 * 批量删除登录日志
 * @param params 批量参数
 * @returns 删除结果
 */
export const fetchDeleteLoginLogList = (params: DeleteListParams) =>
  request.post<null>({
    url: '/api/log/deleteList/login',
    data: params,
    showSuccessMessage: true
  })

/**
 * 获取操作日志列表
 * @param params 搜索参数
 * @returns 操作日志列表数据
 */
export const fetchOperationLogList = (params: OperationLogSearchParams) =>
  request.get<OperationLogListResponse>({
    url: '/api/log/operation',
    params
  })

/**
 * 删除操作日志
 * @param id 日志ID
 * @returns 删除结果
 */
export const fetchDeleteOperationLog = (id: string) =>
  request.post<null>({
    url: `/api/log/delete/operation/${id}`,
    showSuccessMessage: true
  })

// 个人登录日志搜索参数
export interface PersonalLoginLogSearchParams {
  page?: number
  pageSize?: number
  startTime?: string
  endTime?: string
  status?: number
}

/**
 * 获取个人登录日志列表
 * @param params 搜索参数
 * @returns 个人登录日志列表数据
 */
export const fetchPersonalLoginLogList = (params: PersonalLoginLogSearchParams) =>
  request.get<LoginLogListResponse>({
    url: '/api/log/personal/login',
    params
  })

/**
 * 个人强制退出
 * @param sessionId 会话ID
 * @returns 退出结果
 */
export const fetchPersonalLogout = (sessionId: string) =>
  request.post<null>({
    url: `/api/log/personal/logout/${sessionId}`,
    showSuccessMessage: true
  })

// 个人操作日志搜索参数
export interface PersonalOperationLogSearchParams {
  page?: number
  pageSize?: number
  name?: string
  type?: string
  startTime?: string
  endTime?: string
  status?: number
}

/**
 * 获取个人操作日志列表
 * @param params 搜索参数
 * @returns 个人操作日志列表数据
 */
export const fetchPersonalOperationLogList = (params: PersonalOperationLogSearchParams) =>
  request.get<OperationLogListResponse>({
    url: '/api/log/personal/operation',
    params
  })
