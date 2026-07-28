import { App, Directive, DirectiveBinding } from 'vue'
import { usePermission } from '@/composables/usePermission'

/**
 * Role directive based on role codes.
 *
 * Usage:
 * 1. Single role: <ElButton v-roles="'admin'">Button</ElButton>
 * 2. Multiple roles: <ElButton v-roles="['admin', 'super_admin']">Button</ElButton>
 */

interface RolesBinding extends DirectiveBinding {
  value: string | string[]
}

function checkRolePermission(el: HTMLElement, binding: RolesBinding): void {
  const { hasRole, roles } = usePermission()

  if (!roles.value?.length) {
    removeElement(el)
    return
  }

  if (!hasRole(binding.value)) {
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
