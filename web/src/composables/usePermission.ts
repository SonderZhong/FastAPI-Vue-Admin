import { computed } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { canAccessRoute } from '@/utils/permission'

/**
 * 数据权限范围枚举
 */
export enum DataScope {
  /** 全部数据 */
  ALL = 1,
  /** 本部门及下属部门 */
  DEPT_AND_CHILD = 2,
  /** 仅本部门 */
  DEPT_ONLY = 3,
  /** 仅本人 */
  SELF_ONLY = 4
}

/**
 * 权限检查组合式函数
 * 完全基于后端 Casbin 返回的权限数据进行判断
 * 
 * 权限结构（Casbin 方案C）：
 * - casbin_roles: 用户的角色编码列表
 * - menus: 菜单权限ID列表
 * - buttons: 按钮权限ID列表
 * - apis: API权限列表
 * - permission_marks: 按钮权限的 authMark 列表（用于 v-auth 指令）
 * - data_scope: 数据权限范围
 */
export function usePermission() {
  const userStore = useUserStore()

  /**
   * 当前用户的权限标记列表（按钮权限的 authMark）
   */
  const permissionMarks = computed(() => {
    return (userStore.info?.permission_marks as string[]) || []
  })

  /**
   * 当前用户的 Casbin 角色列表
   */
  const casbinRoles = computed(() => {
    return (userStore.info?.casbin_roles as string[]) || []
  })

  /**
   * 当前用户的菜单权限ID列表
   */
  const menuIds = computed(() => {
    return (userStore.info?.menus as string[]) || []
  })

  /**
   * 当前用户的按钮权限ID列表
   */
  const buttonIds = computed(() => {
    return (userStore.info?.buttons as string[]) || []
  })

  /**
   * 当前用户的 API 权限列表
   */
  const apiPermissions = computed(() => {
    return (userStore.info?.apis as Auth.ApiPermission[]) || []
  })

  /**
   * 当前用户身份类型
   */
  const userType = computed(() => {
    return userStore.info?.user_type ?? 3
  })

  /**
   * 当前用户的数据权限范围
   */
  const dataScope = computed(() => {
    return (userStore.info?.data_scope as number) ?? DataScope.SELF_ONLY
  })

  /**
   * 当前用户可访问的部门ID列表
   */
  const accessibleDeptIds = computed(() => {
    return (userStore.info?.sub_departments as string[]) || []
  })

  /**
   * 检查是否拥有指定的权限标记（按钮权限）
   * @param mark 权限标记，可以是单个标记或多个标记数组
   * @param requireAll 是否要求拥有所有权限（仅当 mark 为数组时有效）
   * @returns 是否拥有权限
   */
  const hasPermission = (mark: string | string[], requireAll = false): boolean => {
    // 如果用户信息未加载，默认无权限
    if (!userStore.info || !permissionMarks.value) {
      return false
    }

    // 单个权限标记检查
    if (typeof mark === 'string') {
      return permissionMarks.value.includes(mark)
    }

    // 多个权限标记检查
    if (requireAll) {
      return mark.every((m) => permissionMarks.value.includes(m))
    } else {
      return mark.some((m) => permissionMarks.value.includes(m))
    }
  }

  /**
   * 检查是否拥有指定的 Casbin 角色
   * @param roleCode 角色编码
   * @returns 是否拥有该角色
   */
  const hasRole = (roleCode: string | string[]): boolean => {
    if (!userStore.info || !casbinRoles.value) {
      return false
    }

    if (typeof roleCode === 'string') {
      return casbinRoles.value.includes(roleCode)
    }

    return roleCode.some((code) => casbinRoles.value.includes(code))
  }

  /**
   * 检查是否拥有任意一个权限
   * @param marks 权限标记数组
   * @returns 是否拥有任意一个权限
   */
  const hasAnyPermission = (...marks: string[]): boolean => {
    return hasPermission(marks, false)
  }

  /**
   * 检查是否拥有所有权限
   * @param marks 权限标记数组
   * @returns 是否拥有所有权限
   */
  const hasAllPermissions = (...marks: string[]): boolean => {
    return hasPermission(marks, true)
  }

  /**
   * 检查是否是超级管理员
   */
  const isSuperAdmin = computed(() => {
    return userType.value === 0
  })

  /**
   * 检查是否是管理员（包括超级管理员）
   */
  const isAdmin = computed(() => {
    return userType.value <= 1
  })

  /**
   * 检查是否是部门管理员（包括管理员和超级管理员）
   */
  const isDeptAdmin = computed(() => {
    return userType.value <= 2
  })

  /**
   * 检查是否是普通用户
   */
  const isNormalUser = computed(() => {
    return userType.value === 3
  })

  /**
   * 检查用户身份是否满足最低要求
   * @param minRequired 最低要求的用户身份
   * @returns 是否满足要求
   */
  const meetUserTypeRequirement = (minRequired: number): boolean => {
    return canAccessRoute(userType.value, minRequired)
  }

  /**
   * 获取用户身份名称
   */
  const userTypeName = computed(() => {
    const typeNames: Record<number, string> = {
      0: '超级管理员',
      1: '管理员',
      2: '部门管理员',
      3: '普通用户'
    }
    return typeNames[userType.value] || '未知'
  })

  /**
   * 获取数据权限范围名称
   */
  const dataScopeName = computed(() => {
    const scopeNames: Record<number, string> = {
      [DataScope.ALL]: '全部数据',
      [DataScope.DEPT_AND_CHILD]: '本部门及下属部门',
      [DataScope.DEPT_ONLY]: '仅本部门',
      [DataScope.SELF_ONLY]: '仅本人'
    }
    return scopeNames[dataScope.value] || '仅本人'
  })

  /**
   * 检查是否可以访问指定部门的数据
   * @param deptId 部门ID
   * @returns 是否可以访问
   */
  const canAccessDepartment = (deptId: string): boolean => {
    // 全部数据权限
    if (dataScope.value === DataScope.ALL) {
      return true
    }

    // 检查部门是否在可访问列表中
    return accessibleDeptIds.value.includes(deptId)
  }

  /**
   * 检查是否可以访问某个路由
   * @param route 路由对象
   * @returns 是否可以访问
   */
  const canAccessRouteByMeta = (route: any): boolean => {
    // 检查路由的 minUserType 要求
    if (route.meta?.minUserType !== undefined) {
      if (!meetUserTypeRequirement(route.meta.minUserType)) {
        return false
      }
    }

    // 检查路由的权限要求
    if (route.meta?.authList && Array.isArray(route.meta.authList)) {
      const authMarks = route.meta.authList.map((auth: any) => auth.authMark)
      if (authMarks.length > 0) {
        return hasAnyPermission(...authMarks)
      }
    }

    return true
  }

  return {
    // 权限数据
    permissionMarks,
    casbinRoles,
    menuIds,
    buttonIds,
    apiPermissions,
    userType,
    userTypeName,
    dataScope,
    dataScopeName,
    accessibleDeptIds,

    // 权限检查方法
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,

    // 用户身份检查
    isSuperAdmin,
    isAdmin,
    isDeptAdmin,
    isNormalUser,
    meetUserTypeRequirement,

    // 数据权限检查
    canAccessDepartment,

    // 路由权限检查
    canAccessRouteByMeta
  }
}
