export interface DepartmentInfo {
  id: string
  tenant_id: string | null
  code: string | null
  ancestor_path: string | null
  name: string
  parent_id: string | null
  sort: number
  phone: string | null
  principal: string | null
  email: string | null
  remark: string | null
  status: number
  created_at: string
  updated_at: string
  children?: DepartmentInfo[]
}

export interface DepartmentTree extends Omit<DepartmentInfo, 'children'> {
  children?: DepartmentTree[]
}

export interface DepartmentListResponse {
  result: DepartmentInfo[]
  total: number
  page: number
  pageSize: number
}

export interface AddDepartmentParams {
  tenant_id?: string
  name: string
  code?: string | null
  parent_id: string | null
  sort: number
  phone?: string | null
  principal?: string | null
  email?: string | null
  remark?: string | null
  status: number
}
