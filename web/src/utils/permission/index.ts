/**
 * 权限控制工具
 * 基于用户身份标识（user_type）进行权限判断
 */

/**
 * 用户身份类型枚举
 */
export enum UserType {
  /** 超级管理员 */
  SUPER_ADMIN = 0,
  /** 管理员 */
  ADMIN = 1,
  /** 部门管理员 */
  DEPT_ADMIN = 2,
  /** 普通用户 */
  NORMAL_USER = 3
}

/**
 * 用户身份权限配置
 */
export interface UserTypePermission {
  /** 身份名称 */
  name: string
  /** 可以管理所有资源 */
  canManageAll: boolean
  /** 可以管理系统配置 */
  canManageSystem: boolean
  /** 可以管理部门 */
  canManageDepartments: boolean
  /** 可以管理用户 */
  canManageUsers: boolean
  /** 可以分配角色 */
  canAssignRoles: boolean
  /** 可以查看所有数据 */
  canViewAllData: boolean
  /** 描述 */
  description: string
}

/**
 * 获取用户身份对应的权限配置
 */
export function getUserTypePermission(userType: number): UserTypePermission {
  const permissions: Record<number, UserTypePermission> = {
    [UserType.SUPER_ADMIN]: {
      name: '超级管理员',
      canManageAll: true,
      canManageSystem: true,
      canManageDepartments: true,
      canManageUsers: true,
      canAssignRoles: true,
      canViewAllData: true,
      description: '拥有系统最高权限，可管理所有资源和配置'
    },
    [UserType.ADMIN]: {
      name: '管理员',
      canManageAll: false,
      canManageSystem: true,
      canManageDepartments: true,
      canManageUsers: true,
      canAssignRoles: true,
      canViewAllData: true,
      description: '可管理系统配置、部门和用户，但无法修改超级管理员'
    },
    [UserType.DEPT_ADMIN]: {
      name: '部门管理员',
      canManageAll: false,
      canManageSystem: false,
      canManageDepartments: false,
      canManageUsers: true,
      canAssignRoles: false,
      canViewAllData: false,
      description: '可管理所属部门及下属部门的用户和数据'
    },
    [UserType.NORMAL_USER]: {
      name: '普通用户',
      canManageAll: false,
      canManageSystem: false,
      canManageDepartments: false,
      canManageUsers: false,
      canAssignRoles: false,
      canViewAllData: false,
      description: '只能查看和操作自己的数据'
    }
  }

  return permissions[userType] || permissions[UserType.NORMAL_USER]
}

/**
 * 获取用户身份名称
 */
export function getUserTypeName(userType: number): string {
  return getUserTypePermission(userType).name
}

/**
 * 判断用户是否有系统管理权限
 */
export function hasSystemPermission(userType: number): boolean {
  return getUserTypePermission(userType).canManageSystem
}

/**
 * 判断用户是否有部门管理权限
 */
export function hasDepartmentPermission(userType: number): boolean {
  return getUserTypePermission(userType).canManageDepartments
}

/**
 * 判断用户是否有用户管理权限
 */
export function hasUserPermission(userType: number): boolean {
  return getUserTypePermission(userType).canManageUsers
}

/**
 * 判断用户是否可以查看所有数据
 */
export function canViewAllData(userType: number): boolean {
  return getUserTypePermission(userType).canViewAllData
}

/**
 * 判断是否为超级管理员
 */
export function isSuperAdmin(userType: number): boolean {
  return userType === UserType.SUPER_ADMIN
}

/**
 * 判断是否为管理员（包括超级管理员）
 */
export function isAdmin(userType: number): boolean {
  return userType === UserType.SUPER_ADMIN || userType === UserType.ADMIN
}

/**
 * 判断是否为部门管理员（包括管理员和超级管理员）
 */
export function isDeptAdmin(userType: number): boolean {
  return userType <= UserType.DEPT_ADMIN
}

/**
 * 获取用户身份选项列表（用于表单选择）
 */
export function getUserTypeOptions() {
  return [
    { label: '超级管理员', value: UserType.SUPER_ADMIN },
    { label: '管理员', value: UserType.ADMIN },
    { label: '部门管理员', value: UserType.DEPT_ADMIN },
    { label: '普通用户', value: UserType.NORMAL_USER }
  ]
}

/**
 * 根据当前用户身份过滤可分配的用户身份选项
 * @param currentUserType 当前用户的身份标识
 * @returns 可分配的用户身份选项列表
 */
export function getAssignableUserTypes(currentUserType: number) {
  const allOptions = getUserTypeOptions()

  // 超级管理员可以分配所有身份
  if (currentUserType === UserType.SUPER_ADMIN) {
    return allOptions
  }

  // 管理员可以分配管理员及以下身份
  if (currentUserType === UserType.ADMIN) {
    return allOptions.filter((option) => option.value >= UserType.ADMIN)
  }

  // 部门管理员可以分配部门管理员及普通用户
  if (currentUserType === UserType.DEPT_ADMIN) {
    return allOptions.filter((option) => option.value >= UserType.DEPT_ADMIN)
  }

  // 普通用户不能分配任何身份
  return []
}

/**
 * 判断当前用户是否可以管理目标用户
 * @param currentUserType 当前用户身份
 * @param targetUserType 目标用户身份
 * @returns 是否有权限
 */
export function canManageUser(currentUserType: number, targetUserType: number): boolean {
  // 超级管理员可以管理所有用户
  if (currentUserType === UserType.SUPER_ADMIN) {
    return true
  }

  // 管理员可以管理除超级管理员外的所有用户
  if (currentUserType === UserType.ADMIN) {
    return targetUserType !== UserType.SUPER_ADMIN
  }

  // 部门管理员只能管理部门管理员和普通用户
  if (currentUserType === UserType.DEPT_ADMIN) {
    return targetUserType >= UserType.DEPT_ADMIN
  }

  // 普通用户不能管理其他用户
  return false
}

/**
 * 检查用户身份是否满足路由权限要求
 * @param userType 用户身份
 * @param minRequiredType 路由要求的最低身份
 * @returns 是否有权限访问
 */
export function canAccessRoute(userType: number, minRequiredType: number = 3): boolean {
  // 用户身份等级越低，权限越高
  // 0=超级管理员，1=管理员，2=部门管理员，3=普通用户
  return userType <= minRequiredType
}

/**
 * 过滤路由列表，只保留用户有权限访问的路由
 * @param routes 路由列表
 * @param userType 用户身份
 * @returns 过滤后的路由列表
 */
export function filterRoutesByUserType(routes: any[], userType: number): any[] {
  return routes
    .filter((route) => {
      const minRequired = route.meta?.minUserType ?? 3
      return canAccessRoute(userType, minRequired)
    })
    .map((route) => {
      if (route.children && route.children.length > 0) {
        return {
          ...route,
          children: filterRoutesByUserType(route.children, userType)
        }
      }
      return route
    })
    .filter((route) => {
      // 过滤掉没有子路由且自身被过滤的父路由
      if (route.children && route.children.length === 0) {
        const minRequired = route.meta?.minUserType ?? 3
        return canAccessRoute(userType, minRequired)
      }
      return true
    })
}
