import request from '@/utils/http'

export interface DepartmentInfo {
  id: string
  tenant_id: string | null
  code: string | null
  ancestor_path: string | null
  name: string
  parent_id: string | null
  principal: string | null
  phone: string | null
  email: string | null
  remark: string | null
  sort: number
  status: number
  created_at: string
  updated_at: string
  children?: DepartmentInfo[]
}

export interface DepartmentListResponse {
  result: DepartmentInfo[]
  total: number
  page: number
  pageSize: number
}

/** 获取部门列表 */
export function fetchDepartmentList(params?: {
  page?: number
  pageSize?: number
  tenant_id?: string
  name?: string
  principal?: string
  status?: number
}) {
  return request.get<DepartmentListResponse>({
    url: '/api/department/list',
    params
  })
}

/** 获取部门详情 */
export function fetchDepartmentInfo(id: string) {
  return request.get<DepartmentInfo>({
    url: `/api/department/info/${id}`
  })
}

/** 获取部门树形结构 */
export function fetchDepartmentTree() {
  return request.get<DepartmentListResponse>({
    url: '/api/department/tree'
  })
}

/** 新增部门 */
export function addDepartment(data: {
  tenant_id?: string
  name: string
  code?: string | null
  parent_id?: string | null
  principal?: string | null
  phone?: string | null
  email?: string | null
  sort?: number
  status?: number
  remark?: string | null
}) {
  return request.post<null>({
    url: '/api/department/add',
    data
  })
}

/** 修改部门 */
export function updateDepartment(
  id: string,
  data: {
    name?: string
    code?: string | null
    parent_id?: string | null
    principal?: string | null
    phone?: string | null
    email?: string | null
    sort?: number
    status?: number
    remark?: string | null
  }
) {
  return request.put<null>({
    url: `/api/department/update/${id}`,
    data
  })
}

/** 删除部门 */
export function deleteDepartment(id: string) {
  return request.post<null>({
    url: `/api/department/delete/${id}`
  })
}

/** 批量删除部门 */
export function deleteDepartmentList(ids: string[]) {
  return request.post<null>({
    url: '/api/department/deleteList',
    data: { ids }
  })
}
