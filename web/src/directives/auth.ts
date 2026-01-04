import { router } from '@/router'
import { App, Directive, DirectiveBinding } from 'vue'
import { usePermission } from '@/composables/usePermission'

/**
 * 权限指令（后端控制模式）
 * 
 * 用法：
 * 1. 基于权限标记：<ElButton v-auth="'code:btn:add'">添加</ElButton>
 * 2. 多个权限（满足任一）：<ElButton v-auth="['code:btn:add', 'code:btn:update']">操作</ElButton>
 * 3. 多个权限（全部满足）：<ElButton v-auth="{marks: ['code:btn:add', 'code:btn:update'], requireAll: true}">操作</ElButton>
 * 
 * 权限检查逻辑：
 * 1. 检查用户是否拥有对应的权限标记（permission_marks）
 * 2. 检查用户身份是否满足权限要求（minUserType）
 * 3. 如果用户没有权限，则移除DOM元素
 */

interface AuthValue {
  marks: string | string[]
  requireAll?: boolean
}

interface AuthBinding extends DirectiveBinding {
  value: string | string[] | AuthValue
}

function checkAuthPermission(el: HTMLElement, binding: AuthBinding): void {
  const { hasPermission } = usePermission()
  
  let marks: string | string[]
  let requireAll = false

  // 解析指令值
  if (typeof binding.value === 'string') {
    marks = binding.value
  } else if (Array.isArray(binding.value)) {
    marks = binding.value
  } else if (binding.value && typeof binding.value === 'object') {
    marks = binding.value.marks
    requireAll = binding.value.requireAll || false
  } else {
    console.warn('[v-auth] Invalid directive value:', binding.value)
    removeElement(el)
    return
  }

  // 检查权限
  const hasAuth = hasPermission(marks, requireAll)
  
  if (!hasAuth) {
    removeElement(el)
  }
}

function removeElement(el: HTMLElement): void {
  if (el.parentNode) {
    el.parentNode.removeChild(el)
  }
}

const authDirective: Directive = {
  mounted: checkAuthPermission,
  updated: checkAuthPermission
}

export function setupAuthDirective(app: App): void {
  app.directive('auth', authDirective)
}
