<template>
  <ElDrawer
    v-model="visible"
    :title="roleData?.name || $t('role.roleDetail', '角色详情')"
    size="400px"
    :destroy-on-close="false"
  >
    <template v-if="roleData">
      <!-- 基本信息 -->
      <div class="mb-6">
        <h4 class="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
          <ElIcon><InfoFilled /></ElIcon>
          {{ $t('common.basicInfo', '基本信息') }}
        </h4>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('role.roleName', '角色名称')">
            {{ roleData.name }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('role.roleCode', '角色编码')">
            <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{{ roleData.code }}</code>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('common.status', '状态')">
            <ElTag :type="roleData.status === 1 ? 'success' : 'danger'" size="small">
              {{ roleData.status === 1 ? $t('common.enabled', '启用') : $t('common.disabled', '禁用') }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('common.department', '所属部门')">
            {{ roleData.department_name || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('common.description', '描述')">
            {{ roleData.description || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('common.createTime', '创建时间')">
            {{ dayjs(roleData.created_at).format('YYYY-MM-DD HH:mm:ss') }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('common.updateTime', '更新时间')">
            {{ dayjs(roleData.updated_at).format('YYYY-MM-DD HH:mm:ss') }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </div>

      <!-- 权限统计 -->
      <div class="mb-6">
        <h4 class="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
          <ElIcon><Key /></ElIcon>
          {{ $t('role.permissionStats', '权限统计') }}
        </h4>
        <div v-loading="permissionLoading" class="grid grid-cols-2 gap-3">
          <div class="bg-blue-50 p-3 rounded-lg text-center">
            <div class="text-xl font-bold text-blue-600">{{ menuCount }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ $t('common.menu', '菜单') }}</div>
          </div>
          <div class="bg-orange-50 p-3 rounded-lg text-center">
            <div class="text-xl font-bold text-orange-600">{{ buttonCount }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ $t('common.button', '按钮') }}</div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="space-y-2">
        <ElButton
          v-auth="'role:btn:addPermission'"
          type="warning"
          class="w-full"
          @click="$emit('permission')"
        >
          <ElIcon class="mr-1"><Setting /></ElIcon>
          {{ $t('role.assignPermissions', '分配权限') }}
        </ElButton>
        <ElButton
          v-auth="'role:btn:update'"
          type="primary"
          class="w-full"
          @click="$emit('edit')"
        >
          <ElIcon class="mr-1"><Edit /></ElIcon>
          {{ $t('buttons.edit', '编辑角色') }}
        </ElButton>
        <ElButton
          v-auth="'role:btn:delete'"
          type="danger"
          plain
          class="w-full"
          @click="$emit('delete')"
        >
          <ElIcon class="mr-1"><Delete /></ElIcon>
          {{ $t('buttons.delete', '删除角色') }}
        </ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { dayjs } from 'element-plus'
import { InfoFilled, Key, Setting, Edit, Delete } from '@element-plus/icons-vue'
import { fetchRolePermissionList, type RoleInfo } from '@/api/system/role'

interface Props {
  modelValue: boolean
  roleData?: RoleInfo | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'edit'): void
  (e: 'permission'): void
  (e: 'delete'): void
  (e: 'refresh'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  roleData: null
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const permissionLoading = ref(false)
const menuCount = ref(0)
const buttonCount = ref(0)

/**
 * 加载权限统计
 */
const loadPermissionStats = async () => {
  if (!props.roleData?.id) return

  try {
    permissionLoading.value = true
    const response = await fetchRolePermissionList(props.roleData.id)
    
    if (response.success && response.data) {
      const permissions = response.data.result || []
      menuCount.value = permissions.filter(p => p.permission_type === 0).length
      buttonCount.value = permissions.filter(p => p.permission_type === 1).length
    }
  } catch (error) {
    console.error('加载权限统计失败:', error)
  } finally {
    permissionLoading.value = false
  }
}

// 监听抽屉打开
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && props.roleData) {
      loadPermissionStats()
    }
  }
)

// 监听角色数据变化
watch(
  () => props.roleData?.id,
  () => {
    if (props.modelValue && props.roleData) {
      loadPermissionStats()
    }
  }
)
</script>
