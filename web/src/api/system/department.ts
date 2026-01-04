import request from '@/utils/http'
import { DepartmentInfo, AddDepartmentParams, DepartmentListResponse } from '@/typings/department'

// 获取部门列表
export function fetchDepartmentList(params: any) {
  return request.get<DepartmentListResponse>({
    url: '/api/department/list',
    params
  })
}

// 获取部门详情
export function fetchDepartmentInfo(id: string) {
  return request.get<DepartmentInfo>({
    url: `/api/department/info/${id}`
  })
}

// 获取所有部门数据
export function fetchAllDepartments() {
  return request.get<DepartmentListResponse>({
    url: '/api/department/all'
  })
}

// 获取部门树形结构数据
export function fetchDepartmentTree() {
  return request.get<DepartmentListResponse>({
    url: '/api/department/tree'
  })
}

// 新增部门
export function addDepartment(data: AddDepartmentParams) {
  return request.post<null>({
    url: '/api/department/add',
    data
  })
}

// 修改部门
export function updateDepartment(id: string, data: AddDepartmentParams) {
  return request.put<null>({
    url: `/api/department/update/${id}`,
    data
  })
}

// 删除部门
export function deleteDepartment(id: string) {
  return request.delete<null>({
    url: `/api/department/delete/${id}`
  })
}

// 批量删除部门
export function deleteDepartmentList(ids: string[]) {
  return request.post<null>({
    url: '/api/department/deleteList',
    data: { ids }
  })
}
