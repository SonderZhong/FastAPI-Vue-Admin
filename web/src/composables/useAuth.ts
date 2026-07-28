import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store/modules/user'
import { useCommon } from '@/composables/useCommon'
import { usePermission } from '@/composables/usePermission'
import type { AppRouteRecord } from '@/types/router'

type AuthItem = NonNullable<AppRouteRecord['meta']['authList']>[number]

export const useAuth = () => {
  const route = useRoute()
  const { isFrontendMode } = useCommon()
  const userStore = useUserStore()
  const { info } = storeToRefs(userStore)
  const { hasPermission } = usePermission()

  const frontendAuthList = info.value?.buttons ?? []
  const userPermissionMarks = info.value?.permission_marks ?? []
  const backendAuthList: AuthItem[] = Array.isArray(route.meta.authList)
    ? (route.meta.authList as AuthItem[])
    : []
  const routeAuthMarks = Array.isArray(route.meta.auth) ? route.meta.auth : []

  const hasAuth = (auth: string): boolean => {
    if (!auth) {
      return false
    }

    if (auth.includes(':')) {
      return userPermissionMarks.includes(auth)
    }

    if (isFrontendMode.value) {
      return frontendAuthList.includes(auth)
    }

    const metaMarks = [
      ...backendAuthList.map((item) => item?.authMark).filter(Boolean),
      ...routeAuthMarks
    ]

    if (metaMarks.some((item) => item === auth || item.endsWith(`:${auth}`))) {
      return true
    }

    if (userPermissionMarks.some((item) => item.endsWith(`:${auth}`))) {
      return true
    }

    return hasPermission(auth)
  }

  const hasAnyAuth = (auths: string[]): boolean => auths.some((auth) => hasAuth(auth))
  const hasAllAuth = (auths: string[]): boolean => auths.every((auth) => hasAuth(auth))

  return {
    hasAuth,
    hasAnyAuth,
    hasAllAuth
  }
}
