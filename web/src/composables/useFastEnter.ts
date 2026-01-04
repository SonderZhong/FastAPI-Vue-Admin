/**
 * 快速入口 composable
 * 用于获取和管理快速入口配置
 * 支持根据用户身份过滤快捷入口
 */

import { computed } from 'vue'
import appConfig from '@/config'
import type { FastEnterApplication, FastEnterQuickLink } from '@/types/config'
import { useUserStore } from '@/store/modules/user'
import { canAccessRoute } from '@/utils/permission'

export function useFastEnter() {
  const userStore = useUserStore()

  // 获取快速入口配置
  const fastEnterConfig = computed(() => appConfig.fastEnter)

  // 获取当前用户身份
  const currentUserType = computed(() => userStore.info?.user_type ?? 3)

  // 获取启用的应用列表（按排序权重排序，根据用户身份过滤）
  const enabledApplications = computed<FastEnterApplication[]>(() => {
    if (!fastEnterConfig.value?.applications) return []

    return fastEnterConfig.value.applications
      .filter((app) => {
        // 检查是否启用
        if (app.enabled === false) return false

        // 检查用户身份是否满足要求
        const minRequired = app.minUserType ?? 3
        return canAccessRoute(currentUserType.value, minRequired)
      })
      .sort((a, b) => (a.order || 0) - (b.order || 0))
  })

  // 获取启用的快速链接（按排序权重排序，根据用户身份过滤）
  const enabledQuickLinks = computed<FastEnterQuickLink[]>(() => {
    if (!fastEnterConfig.value?.quickLinks) return []

    return fastEnterConfig.value.quickLinks
      .filter((link) => {
        // 检查是否启用
        if (link.enabled === false) return false

        // 检查用户身份是否满足要求
        const minRequired = link.minUserType ?? 3
        return canAccessRoute(currentUserType.value, minRequired)
      })
      .sort((a, b) => (a.order || 0) - (b.order || 0))
  })

  // 获取最小显示宽度
  const minWidth = computed(() => {
    return fastEnterConfig.value?.minWidth || 1200
  })

  return {
    fastEnterConfig,
    enabledApplications,
    enabledQuickLinks,
    minWidth,
    currentUserType
  }
}
