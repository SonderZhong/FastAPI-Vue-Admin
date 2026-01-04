<template>
  <div class="p-6">
    <ElCard class="mb-4">
      <template #header>
        <div class="font-medium">权限系统使用示例</div>
      </template>

      <!-- 用户权限信息展示 -->
      <div class="mb-6">
        <h3 class="text-lg font-medium mb-3">当前用户权限信息</h3>
        <div class="bg-gray-50 p-4 rounded">
          <div class="mb-2"> <strong>用户名：</strong>{{ userInfo?.username }} </div>
          <div class="mb-2"> <strong>部门：</strong>{{ userInfo?.department_name }} </div>
          <div class="mb-2">
            <strong>权限标识列表：</strong>
            <div class="mt-1">
              <ElTag
                v-for="mark in userInfo?.permission_marks"
                :key="mark"
                type="info"
                size="small"
                class="mr-2 mb-1"
              >
                {{ mark }}
              </ElTag>
            </div>
          </div>
        </div>
      </div>

      <!-- 权限检查示例 -->
      <div class="mb-6">
        <h3 class="text-lg font-medium mb-3">权限检查示例</h3>

        <!-- 方式1: usePermission Hook -->
        <div class="mb-4">
          <h4 class="text-base font-medium mb-2">1. usePermission Hook</h4>
          <div class="space-x-2">
            <ElButton
              v-if="hasPermission('user:btn:add')"
              type="primary"
              @click="handleAction('新增用户')"
            >
              新增用户
            </ElButton>
            <ElButton
              v-if="hasPermission('user:btn:edit')"
              type="warning"
              @click="handleAction('编辑用户')"
            >
              编辑用户
            </ElButton>
            <ElButton
              v-if="hasPermission('user:btn:delete')"
              type="danger"
              @click="handleAction('删除用户')"
            >
              删除用户
            </ElButton>
          </div>
        </div>

        <!-- 方式2: useAuth Hook (兼容旧版本) -->
        <div class="mb-4">
          <h4 class="text-base font-medium mb-2">2. useAuth Hook (兼容)</h4>
          <div class="space-x-2">
            <ElButton
              v-if="hasAuth('department:btn:add')"
              type="success"
              @click="handleAction('新增部门')"
            >
              新增部门
            </ElButton>
            <ElButton v-if="hasAuth('add')" type="info" @click="handleAction('兼容旧版本新增')">
              兼容新增
            </ElButton>
          </div>
        </div>

        <!-- 方式3: v-auth 指令 -->
        <div class="mb-4">
          <h4 class="text-base font-medium mb-2">3. v-auth 指令</h4>
          <div class="space-x-2">
            <ElButton v-auth="'role:btn:add'" type="primary" @click="handleAction('新增角色')">
              新增角色
            </ElButton>
            <ElButton
              v-auth="['role:btn:edit', 'role:btn:delete']"
              type="warning"
              @click="handleAction('角色管理')"
            >
              角色管理
            </ElButton>
          </div>
        </div>

        <!-- 方式4: v-permission 指令 -->
        <div class="mb-4">
          <h4 class="text-base font-medium mb-2">4. v-permission 指令</h4>
          <div class="space-x-2">
            <ElButton
              v-permission="'permission:btn:add'"
              type="success"
              @click="handleAction('新增权限')"
            >
              新增权限
            </ElButton>
            <ElButton
              v-permission="['permission:btn:edit', 'permission:btn:delete']"
              type="danger"
              @click="handleAction('权限管理')"
            >
              权限管理
            </ElButton>
          </div>
        </div>

        <!-- 方式5: 条件渲染组合 -->
        <div class="mb-4">
          <h4 class="text-base font-medium mb-2">5. 条件渲染组合</h4>
          <div class="space-x-2">
            <ElButton
              v-if="hasPermission('user:btn:export')"
              type="info"
              @click="handleAction('导出用户')"
            >
              导出用户
            </ElButton>
            <ElButton
              v-if="hasAllPermissions(['user:btn:import', 'user:btn:add'])"
              type="warning"
              @click="handleAction('批量导入')"
            >
              批量导入 (需要所有权限)
            </ElButton>
            <ElButton
              v-if="hasAnyPermission(['user:btn:reset', 'user:btn:edit'])"
              type="danger"
              @click="handleAction('用户操作')"
            >
              用户操作 (任一权限)
            </ElButton>
          </div>
        </div>
      </div>

      <!-- 权限检查结果展示 -->
      <div class="mb-6">
        <h3 class="text-lg font-medium mb-3">权限检查结果</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(result, permission) in permissionResults"
            :key="permission"
            class="flex items-center justify-between p-3 border rounded"
          >
            <span class="font-mono text-sm">{{ permission }}</span>
            <ElTag :type="result ? 'success' : 'danger'" size="small">
              {{ result ? '有权限' : '无权限' }}
            </ElTag>
          </div>
        </div>
      </div>

      <!-- 多权限检查示例 -->
      <div class="mb-6">
        <h3 class="text-lg font-medium mb-3">多权限检查示例</h3>
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <span>用户管理权限 (任一):</span>
            <ElTag :type="hasAnyUserPermission ? 'success' : 'danger'" size="small">
              {{ hasAnyUserPermission ? '有权限' : '无权限' }}
            </ElTag>
          </div>
          <div class="flex items-center space-x-2">
            <span>用户完整权限 (全部):</span>
            <ElTag :type="hasAllUserPermissions ? 'success' : 'danger'" size="small">
              {{ hasAllUserPermissions ? '有权限' : '无权限' }}
            </ElTag>
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import { usePermission } from '@/composables/useAuth'
  import { useAuth } from '@/composables/useAuth'
  import { useUserStore } from '@/store/modules/user'
  import { storeToRefs } from 'pinia'

  // 用户信息
  const userStore = useUserStore()
  const { info: userInfo } = storeToRefs(userStore)

  // 权限检查 Hooks
  const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermission()
  const { hasAuth } = useAuth()

  // 权限检查结果
  const permissionResults = computed(() => {
    const permissions = [
      'user:btn:add',
      'user:btn:edit',
      'user:btn:delete',
      'user:btn:list',
      'role:btn:add',
      'role:btn:edit',
      'department:btn:add',
      'permission:btn:list'
    ]

    const results: Record<string, boolean> = {}
    permissions.forEach((permission) => {
      results[permission] = hasPermission(permission)
    })

    return results
  })

  // 多权限检查示例
  const userPermissions = ['user:btn:add', 'user:btn:edit', 'user:btn:delete', 'user:btn:list']
  const hasAnyUserPermission = computed(() => hasAnyPermission(userPermissions))
  const hasAllUserPermissions = computed(() => hasAllPermissions(userPermissions))

  // 处理操作
  const handleAction = (action: string) => {
    ElMessage.success(`执行操作: ${action}`)
  }
</script>

<style scoped>
  /* 组件样式 */
  .space-x-2 > * + * {
    margin-left: 0.5rem;
  }

  .space-y-2 > * + * {
    margin-top: 0.5rem;
  }
</style>
