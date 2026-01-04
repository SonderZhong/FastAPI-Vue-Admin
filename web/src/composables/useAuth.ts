import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store/modules/user'
import { useCommon } from '@/composables/useCommon'
import type { AppRouteRecord } from '@/types/router'

type AuthItem = NonNullable<AppRouteRecord['meta']['authList']>[number]

/**
 * 权限检查 Hook
 * 基于用户的权限标识列表进行权限验证
 */
export const usePermission = () => {
  const userStore = useUserStore()
  const { info } = storeToRefs(userStore)

  /**
   * 检查是否拥有指定权限
   * @param permission 权限标识 (如: 'user:btn:add')
   * @returns 是否有权限
   */
  const hasPermission = (permission: string): boolean => {
    const userPermissionMarks = info.value?.permission_marks ?? []
    return userPermissionMarks.includes(permission)
  }

  /**
   * 检查是否拥有任一权限
   * @param permissions 权限标识数组
   * @returns 是否有任一权限
   */
  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some((permission) => hasPermission(permission))
  }

  /**
   * 检查是否拥有所有权限
   * @param permissions 权限标识数组
   * @returns 是否拥有所有权限
   */
  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every((permission) => hasPermission(permission))
  }

  /**
   * 检查菜单权限
   * @param path 路由路径
   * @returns 是否有菜单权限
   */
  const hasMenuPermission = (path: string): boolean => {
    // 简单的路径权限映射示例
    const pathPermissionMap: Record<string, string> = {
      '/system/user': 'user:menu:list',
      '/system/role': 'role:menu:list',
      '/system/permission': 'permission:menu:list',
      '/system/department': 'department:menu:list'
    }

    const requiredPermission = pathPermissionMap[path]
    return requiredPermission ? hasPermission(requiredPermission) : true
  }

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasMenuPermission
  }
}

/**
 * 按钮权限（前后端模式通用）
 * 用法：
 * const { hasAuth } = useAuth()
 * hasAuth('user:btn:add') // 检查是否拥有新增权限
 * hasAuth('add') // 兼容旧版本简单权限标识
 */
export const useAuth = () => {
  const route = useRoute()
  const { isFrontendMode } = useCommon()
  const userStore = useUserStore()
  const { info } = storeToRefs(userStore)
  const { hasPermission } = usePermission()

  // 前端按钮权限（例如：['add', 'edit']）
  const frontendAuthList = info.value?.buttons ?? []

  // 用户权限标识列表（从后端个人信息接口获取）
  const userPermissionMarks = info.value?.permission_marks ?? []

  // 后端路由 meta 配置的权限列表（例如：[{ authMark: 'user:btn:add' }]）
  const backendAuthList: AuthItem[] = Array.isArray(route.meta.authList)
    ? (route.meta.authList as AuthItem[])
    : []

  /**
   * 检查是否拥有某权限标识（前后端模式通用）
   * @param auth 权限标识 (如: 'user:btn:add' 或兼容旧版本的 'add')
   * @returns 是否有权限
   */
  const hasAuth = (auth: string): boolean => {
    // 优先检查用户权限标识列表（从后端个人信息接口获取）
    if (auth.includes(':')) {
      // 完整权限标识，直接检查用户权限标识列表
      return userPermissionMarks.includes(auth)
    }

    // 兼容旧版本逻辑
    // 前端模式
    if (isFrontendMode.value) {
      return frontendAuthList.includes(auth)
    }

    // 后端模式 - 多层级权限检查
    // 1. 检查路由meta中的权限
    const hasMetaAuth = backendAuthList.some((item) => item?.authMark === auth)
    if (hasMetaAuth) return true

    // 2. 检查用户权限标识列表中的完整权限标识
    const hasFullAuth = userPermissionMarks.some((mark) => mark.endsWith(`:${auth}`))
    if (hasFullAuth) return true

    // 3. 检查路由meta中的完整权限标识
    const hasFullMetaAuth = backendAuthList.some((item) => item?.authMark.endsWith(`:${auth}`))
    if (hasFullMetaAuth) return true

    // 4. 最后尝试直接权限检查
    return hasPermission(auth)
  }

  /**
   * 检查是否拥有任一权限
   * @param auths 权限标识数组
   * @returns 是否有任一权限
   */
  const hasAnyAuth = (auths: string[]): boolean => {
    return auths.some((auth) => hasAuth(auth))
  }

  /**
   * 检查是否拥有所有权限
   * @param auths 权限标识数组
   * @returns 是否拥有所有权限
   */
  const hasAllAuth = (auths: string[]): boolean => {
    return auths.every((auth) => hasAuth(auth))
  }

  return {
    hasAuth,
    hasAnyAuth,
    hasAllAuth
  }
}
