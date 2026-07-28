import { computed } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { canAccessRoute, UserType } from '@/utils/permission'

export enum DataScope {
  ALL = 1,
  DEPT_AND_CHILD = 2,
  DEPT_ONLY = 3,
  SELF_ONLY = 4
}

export function usePermission() {
  const userStore = useUserStore()
  const permissionVerifyEnabled = import.meta.env.VITE_PERMISSION_VERIFY_ENABLED !== 'false'

  const permissionMarks = computed(() => userStore.info?.permission_marks ?? [])
  const roleCodes = computed(() => userStore.info?.roles ?? [])
  const menuIds = computed(() => userStore.info?.menus ?? [])
  const buttonIds = computed(() => userStore.info?.buttons ?? [])
  const apiIds = computed(() => userStore.info?.apis ?? [])
  const userType = computed(() => userStore.info?.user_type ?? UserType.NORMAL_USER)
  const dataScope = computed(() => userStore.info?.data_scope ?? DataScope.SELF_ONLY)
  const accessibleDeptIds = computed(() => userStore.info?.sub_departments ?? [])

  const hasPermission = (mark: string | string[], requireAll = false): boolean => {
    if (!permissionVerifyEnabled) return true
    if (!permissionMarks.value.length) return false
    if (typeof mark === 'string') return permissionMarks.value.includes(mark)
    return requireAll
      ? mark.every((item) => permissionMarks.value.includes(item))
      : mark.some((item) => permissionMarks.value.includes(item))
  }

  const hasRole = (roleCode: string | string[]): boolean => {
    if (!permissionVerifyEnabled) return true
    if (!roleCodes.value.length) return false
    if (typeof roleCode === 'string') return roleCodes.value.includes(roleCode)
    return roleCode.some((item) => roleCodes.value.includes(item))
  }

  const hasAnyPermission = (...marks: string[]) => hasPermission(marks, false)
  const hasAllPermissions = (...marks: string[]) => hasPermission(marks, true)

  const isSuperAdmin = computed(() => userType.value === UserType.SUPER_ADMIN)
  const isAdmin = computed(() => userType.value <= UserType.TENANT_ADMIN)
  const isDeptAdmin = computed(() => userType.value <= UserType.DEPT_ADMIN)
  const isNormalUser = computed(() => userType.value === UserType.NORMAL_USER)

  const meetUserTypeRequirement = (minRequired: number): boolean =>
    canAccessRoute(userType.value, minRequired)

  const userTypeName = computed(() => {
    const typeNames: Record<number, string> = {
      [UserType.SUPER_ADMIN]: '超级管理员',
      [UserType.TENANT_ADMIN]: '租户管理员',
      [UserType.DEPT_ADMIN]: '部门管理员',
      [UserType.NORMAL_USER]: '普通用户'
    }
    return typeNames[userType.value] || '未知'
  })

  const dataScopeName = computed(() => {
    const scopeNames: Record<number, string> = {
      [DataScope.ALL]: '全部数据',
      [DataScope.DEPT_AND_CHILD]: '本部门及下属部门',
      [DataScope.DEPT_ONLY]: '仅本部门',
      [DataScope.SELF_ONLY]: '仅本人'
    }
    return scopeNames[dataScope.value] || '仅本人'
  })

  const canAccessDepartment = (deptId: string): boolean => {
    if (dataScope.value === DataScope.ALL) return true
    return accessibleDeptIds.value.includes(deptId)
  }

  const canAccessRouteByMeta = (route: any): boolean => {
    if (!permissionVerifyEnabled) return true
    if (route.meta?.minUserType !== undefined && !meetUserTypeRequirement(route.meta.minUserType))
      return false

    const authList = Array.isArray(route.meta?.authList)
      ? route.meta.authList.map((item: any) => item?.authMark).filter(Boolean)
      : []
    const authMarks = Array.isArray(route.meta?.auth) ? route.meta.auth : []
    const requiredMarks = [...authList, ...authMarks]
    return requiredMarks.length === 0 || hasPermission(requiredMarks)
  }

  return {
    permissionMarks,
    roles: roleCodes,
    menuIds,
    buttonIds,
    apiIds,
    permissionVerifyEnabled,
    userType,
    userTypeName,
    dataScope,
    dataScopeName,
    accessibleDeptIds,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    isSuperAdmin,
    isAdmin,
    isDeptAdmin,
    isNormalUser,
    meetUserTypeRequirement,
    canAccessDepartment,
    canAccessRouteByMeta
  }
}
