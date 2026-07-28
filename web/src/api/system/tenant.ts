import request from '@/utils/http'

// ==================== 类型定义 ====================

export interface TenantInfo {
  id: string
  name: string
  code: string
  status: number
  invite_code: string | null
  allow_register: boolean
  remark: string | null
  created_at: string
  updated_at: string
}

export interface TenantListResponse {
  result: TenantInfo[]
  total: number
  page: number
  pageSize: number
}

export interface TenantMemberInfo {
  id: string
  username: string
  nickname: string
  avatar: string
  email: string
  phone: string
  status: number
  created_at: string
}

export interface TenantMemberListResponse {
  result: TenantMemberInfo[]
  total: number
  page: number
  pageSize: number
}

// ==================== 租户 CRUD ====================

/** 获取租户列表 */
export function fetchTenantList(params?: {
  page?: number
  pageSize?: number
  name?: string
  code?: string
  status?: number
}) {
  return request.get<TenantListResponse>({
    url: '/api/tenant/list',
    params
  })
}

/** 获取租户详情 */
export function fetchTenantInfo(id: string) {
  return request.get<TenantInfo>({
    url: `/api/tenant/info/${id}`
  })
}

/** 新增租户 */
export function addTenant(data: { name: string; code: string; status?: number; remark?: string }) {
  return request.post<null>({
    url: '/api/tenant/add',
    data
  })
}

/** 更新租户 */
export function updateTenant(
  id: string,
  data: {
    name?: string
    code?: string
    status?: number
    remark?: string
  }
) {
  return request.put<null>({
    url: `/api/tenant/update/${id}`,
    data
  })
}

/** 删除租户 */
export function deleteTenant(id: string) {
  return request.post<null>({
    url: `/api/tenant/delete/${id}`
  })
}

/** 批量删除租户 */
export function deleteTenantList(ids: string[]) {
  return request.post<null>({
    url: '/api/tenant/deleteList',
    data: { ids }
  })
}

// ==================== 邀请码管理 ====================

/** 生成邀请码 */
export function generateInviteCode(id: string) {
  return request.post<{
    invite_code: string
    invite_link: string
    allow_register: boolean
  }>({
    url: `/api/tenant/invite-code/generate/${id}`
  })
}

/** 切换邀请注册开关 */
export function toggleInviteRegister(id: string) {
  return request.put<{
    allow_register: boolean
  }>({
    url: `/api/tenant/invite-code/toggle/${id}`
  })
}

/** 获取邀请码信息 */
export function fetchInviteCodeInfo(id: string) {
  return request.get<{
    invite_code: string | null
    invite_link: string | null
    allow_register: boolean
  }>({
    url: `/api/tenant/invite-code/info/${id}`
  })
}

/** 验证邀请码 */
export function validateInviteCode(code: string) {
  return request.get<{
    valid: boolean
    tenant_id: string
    tenant_name: string
    tenant_code: string
    allow_register: boolean
  }>({
    url: `/api/tenant/validate-invite-code/${code}`
  })
}

/** 通过邀请码加入租户 */
export function joinTenant(invite_code: string) {
  return request.post<null>({
    url: '/api/tenant/join',
    data: { invite_code }
  })
}

// ==================== 成员管理 ====================

/** 获取租户成员列表 */
export function fetchTenantMembers(
  id: string,
  params?: {
    page?: number
    pageSize?: number
  }
) {
  return request.get<TenantMemberListResponse>({
    url: `/api/tenant/members/${id}`,
    params
  })
}
