import { App, Directive, DirectiveBinding } from 'vue'
import { usePermission } from '@/composables/usePermission'

/**
 * 角色权限指令（基于 Casbin 角色）
 * 
 * 用法：
 * 1. 单个角色：<ElButton v-roles="'admin'">按钮</ElButton>
 * 2. 多个角色（满足任一）：<ElButton v-roles="['admin', 'super_admin']">按钮</ElButton>
 * 
 * 权限检查逻辑：
 * 检查用户的 casbin_roles 是否包含指定的角色编码
 */

interface RolesBinding extends DirectiveBinding {
  value: string | string[]
}

function checkRolePermission(el: HTMLElement, binding: RolesBinding): void {
  const { hasRole, casbinRoles } = usePermission()

  // 如果用户角色为空或未定义，移除元素
  if (!casbinRoles.value?.length) {
    removeElement(el)
    return
  }

  // 检查用户是否具有所需角色之一
  const hasPermission = hasRole(binding.value)

  // 如果没有权限，安全地移除元素
  if (!hasPermission) {
    removeElement(el)
  }
}

function removeElement(el: HTMLElement): void {
  if (el.parentNode) {
    el.parentNode.removeChild(el)
  }
}

const rolesDirective: Directive = {
  mounted: checkRolePermission,
  updated: checkRolePermission
}

export function setupRolesDirective(app: App): void {
  app.directive('roles', rolesDirective)
}
