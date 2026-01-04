// 部门信息接口
export interface DepartmentInfo {
  /** 部门ID */
  id: string
  /** 部门名称 */
  name: string
  /** 父部门ID */
  parent_id: string | null
  /** 排序权重（0最高） */
  sort: number
  /** 部门电话 */
  phone: string | null
  /** 部门负责人 */
  principal: string
  /** 部门邮箱 */
  email: string | null
  /** 备注信息 */
  remark: string | null
  /** 状态（0正常 1停用） */
  status: number | null
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

// 部门树形结构接口
export interface DepartmentTree extends DepartmentInfo {
  /** 子部门 */
  children?: DepartmentTree[]
}

// 部门列表响应接口
export interface DepartmentListResponse {
  result: DepartmentInfo[]
  total: number
  page: number
  pageSize: number
}

// 添加/修改部门参数接口
export interface AddDepartmentParams {
  /** 部门名称 */
  name: string
  /** 父部门ID */
  parent_id: string | null
  /** 排序权重 */
  sort: number
  /** 部门电话 */
  phone: string | null
  /** 部门负责人 */
  principal: string
  /** 部门邮箱 */
  email: string | null
  /** 备注信息 */
  remark: string | null
  /** 状态 */
  status: number | null
}
