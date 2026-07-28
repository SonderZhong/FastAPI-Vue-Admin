export enum UserType {
  SUPER_ADMIN = 0,
  TENANT_ADMIN = 1,
  DEPT_ADMIN = 2,
  NORMAL_USER = 3
}

export interface UserTypePermission {
  name: string
  canManageAll: boolean
  canManageSystem: boolean
  canManageDepartments: boolean
  canManageUsers: boolean
  canAssignRoles: boolean
  canViewAllData: boolean
  description: string
}

const USER_TYPE_OPTIONS = [
  { label: '超级管理员', value: UserType.SUPER_ADMIN },
  { label: '租户管理员', value: UserType.TENANT_ADMIN },
  { label: '部门管理员', value: UserType.DEPT_ADMIN },
  { label: '普通用户', value: UserType.NORMAL_USER }
]

const USER_TYPE_PERMISSIONS: Record<number, UserTypePermission> = {
  [UserType.SUPER_ADMIN]: {
    name: '超级管理员',
    canManageAll: true,
    canManageSystem: true,
    canManageDepartments: true,
    canManageUsers: true,
    canAssignRoles: true,
    canViewAllData: true,
    description: '拥有全部权限'
  },
  [UserType.TENANT_ADMIN]: {
    name: '租户管理员',
    canManageAll: false,
    canManageSystem: true,
    canManageDepartments: true,
    canManageUsers: true,
    canAssignRoles: true,
    canViewAllData: true,
    description: '可管理租户内系统、部门和用户'
  },
  [UserType.DEPT_ADMIN]: {
    name: '部门管理员',
    canManageAll: false,
    canManageSystem: false,
    canManageDepartments: false,
    canManageUsers: true,
    canAssignRoles: false,
    canViewAllData: false,
    description: '可管理所属部门及下属部门用户'
  },
  [UserType.NORMAL_USER]: {
    name: '普通用户',
    canManageAll: false,
    canManageSystem: false,
    canManageDepartments: false,
    canManageUsers: false,
    canAssignRoles: false,
    canViewAllData: false,
    description: '仅可查看和操作自己的数据'
  }
}

export function getUserTypePermission(userType: number): UserTypePermission {
  return USER_TYPE_PERMISSIONS[userType] || USER_TYPE_PERMISSIONS[UserType.NORMAL_USER]
}

export function getUserTypeName(userType: number): string {
  return getUserTypePermission(userType).name
}

export function hasSystemPermission(userType: number): boolean {
  return getUserTypePermission(userType).canManageSystem
}

export function hasDepartmentPermission(userType: number): boolean {
  return getUserTypePermission(userType).canManageDepartments
}

export function hasUserPermission(userType: number): boolean {
  return getUserTypePermission(userType).canManageUsers
}

export function canViewAllData(userType: number): boolean {
  return getUserTypePermission(userType).canViewAllData
}

export function isSuperAdmin(userType: number): boolean {
  return userType === UserType.SUPER_ADMIN
}

export function isAdmin(userType: number): boolean {
  return userType <= UserType.TENANT_ADMIN
}

export function isDeptAdmin(userType: number): boolean {
  return userType <= UserType.DEPT_ADMIN
}

export function getUserTypeOptions() {
  return USER_TYPE_OPTIONS
}

export function getAssignableUserTypes(currentUserType: number) {
  if (currentUserType === UserType.SUPER_ADMIN) return USER_TYPE_OPTIONS
  if (currentUserType === UserType.TENANT_ADMIN) {
    return USER_TYPE_OPTIONS.filter((option) => option.value >= UserType.TENANT_ADMIN)
  }
  if (currentUserType === UserType.DEPT_ADMIN) {
    return USER_TYPE_OPTIONS.filter((option) => option.value >= UserType.DEPT_ADMIN)
  }
  return []
}

export function canManageUser(currentUserType: number, targetUserType: number): boolean {
  if (currentUserType === UserType.SUPER_ADMIN) return true
  if (currentUserType === UserType.TENANT_ADMIN) {
    return targetUserType !== UserType.SUPER_ADMIN
  }
  if (currentUserType === UserType.DEPT_ADMIN) {
    return targetUserType >= UserType.DEPT_ADMIN
  }
  return false
}

export function canAccessRoute(userType: number, minRequiredType: number = 3): boolean {
  return userType <= minRequiredType
}

export function filterRoutesByUserType(routes: any[], userType: number): any[] {
  return routes
    .filter((route) => canAccessRoute(userType, route.meta?.minUserType ?? 3))
    .map((route) => {
      if (route.children?.length) {
        return { ...route, children: filterRoutesByUserType(route.children, userType) }
      }
      return route
    })
    .filter(
      (route) =>
        !(route.children && route.children.length === 0) ||
        canAccessRoute(userType, route.meta?.minUserType ?? 3)
    )
}
