<template>
  <ElDialog
    v-model="dialogVisible"
    :title="$t('user.assignRoles', '分配角色')"
    width="800px"
    :before-close="handleClose"
  >
    <div v-if="userData">
      <div class="mb-4">
        <ElAlert
          :title="$t('user.assignRolesTo', '为用户 {name} 分配角色', { name: userData.nickname })"
          type="info"
          :closable="false"
        />
      </div>

      <div class="mb-4">
        <h3 class="text-base font-medium text-gray-900 mb-3">
          {{ $t('user.selectRoles', '选择角色') }}
        </h3>

        <!-- 角色选择区域 -->
        <div class="border rounded-lg p-4 max-h-96 overflow-auto">
          <div v-if="allRoles.length > 0" class="space-y-2">
            <ElCheckboxGroup v-model="selectedRoleIds">
              <div
                v-for="role in allRoles"
                :key="role.id"
                class="flex items-center p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <ElCheckbox :value="role.id" class="mr-3" @change="handleRoleChange" />
                <div class="flex-1 cursor-pointer" @click="toggleRole(role.id)">
                  <div class="font-medium text-gray-900">{{ role.name }}</div>
                  <div class="text-xs text-gray-400 mt-1">
                    {{ role.description || $t('common.noDescription', '暂无描述') }}
                  </div>
                </div>
                <ElTag
                  v-if="originalRoleIds.includes(role.id)"
                  type="success"
                  size="small"
                  class="ml-2"
                >
                  {{ $t('common.assigned', '已分配') }}
                </ElTag>
              </div>
            </ElCheckboxGroup>
          </div>
          <div v-else class="p-8 text-center text-gray-500">
            {{ $t('user.noAvailableRoles', '暂无可分配角色') }}
          </div>
        </div>
      </div>

      <!-- 操作按钮区域 -->
      <div class="mb-4 flex gap-2">
        <ElButton size="small" @click="selectAllRoles">
          {{ $t('buttons.selectAll', '全选') }}
        </ElButton>
        <ElButton size="small" @click="deselectAllRoles">
          {{ $t('buttons.deselectAll', '取消全选') }}
        </ElButton>
        <ElButton size="small" type="info" @click="resetToOriginal">
          {{ $t('buttons.reset', '重置') }}
        </ElButton>
      </div>

      <!-- 选择统计 -->
      <div class="text-sm text-gray-600 mb-4">
        {{
          $t('user.selectedRolesCount', '已选择 {count} 个角色', {
            count: selectedRoleIds.length
          })
        }}
        <span v-if="hasChanges" class="text-orange-600 ml-2">
          {{ $t('common.hasChanges', '(有修改)') }}
        </span>
      </div>

      <div class="mt-6">
        <ElAlert
          :title="$t('user.roleAssignmentTip', '提示：分配角色后，用户将获得角色对应的权限')"
          type="warning"
          :closable="false"
          class="mb-4"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" :loading="loading" :disabled="!hasChanges" @click="handleSubmit">
          {{ $t('buttons.confirm', '确认') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  import { ElMessage, ElCheckbox, ElCheckboxGroup } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { fetchRoleList, type RoleInfo } from '@/api/system/role'
  import {
    fetchUserRoleList,
    assignUserRoles,
    type UserInfo,
    type UserRoleInfo
  } from '@/api/system/user'

  const { t: $t } = useI18n()

  interface Props {
    visible: boolean
    userData?: UserInfo
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'submit'): void
  }

  const props = withDefaults(defineProps<Props>(), {
    visible: false
  })

  const emit = defineEmits<Emits>()

  // 响应式数据
  const loading = ref(false)
  const allRoles = ref<RoleInfo[]>([])
  const assignedRoles = ref<UserRoleInfo[]>([])
  const selectedRoleIds = ref<string[]>([])
  const originalRoleIds = ref<string[]>([])

  // 弹窗显示状态
  const dialogVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  // 是否有变更
  const hasChanges = computed(() => {
    const current = new Set(selectedRoleIds.value)
    const original = new Set(originalRoleIds.value)

    if (current.size !== original.size) return true

    for (const id of current) {
      if (!original.has(id)) return true
    }

    return false
  })

  /**
   * 监听弹窗显示状态
   */
  watch(
    () => props.visible,
    (newVal) => {
      if (newVal && props.userData) {
        refreshData()
      }
    }
  )

  /**
   * 关闭弹窗
   */
  const handleClose = () => {
    dialogVisible.value = false
  }

  /**
   * 角色变更处理
   */
  const handleRoleChange = () => {
    // 当前逻辑由 v-model 自动处理
  }

  /**
   * 全选角色
   */
  const selectAllRoles = () => {
    selectedRoleIds.value = allRoles.value.map((role) => role.id)
  }

  /**
   * 取消全选
   */
  const deselectAllRoles = () => {
    selectedRoleIds.value = []
  }

  /**
   * 重置为原始状态
   */
  const resetToOriginal = () => {
    selectedRoleIds.value = [...originalRoleIds.value]
  }

  /**
   * 切换角色选择状态
   */
  const toggleRole = (roleId: string) => {
    const index = selectedRoleIds.value.indexOf(roleId)
    if (index > -1) {
      selectedRoleIds.value.splice(index, 1)
    } else {
      selectedRoleIds.value.push(roleId)
    }
  }

  /**
   * 提交角色分配
   */
  const handleSubmit = async () => {
    if (!props.userData || !hasChanges.value) return

    try {
      loading.value = true

      await assignUserRoles({
        user_id: props.userData.id,
        role_ids: selectedRoleIds.value
      })

      ElMessage.success($t('user.assignRoleSuccess', '角色分配成功'))
      emit('submit')
      handleClose()
    } catch (error) {
      console.error('分配角色失败:', error)
      ElMessage.error($t('user.assignRoleFailed', '角色分配失败'))
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载所有角色
   */
  const loadAllRoles = async () => {
    try {
      // 获取用户所在部门及其下级部门的所有角色
      const response = await fetchRoleList({
        page: 1,
        pageSize: 1000, // 获取所有角色
        department_ids: props.userData?.department_id // 使用department_ids来获取该部门及下级部门的角色
      })

      if (response.success && response.data) {
        allRoles.value = response.data.result || []
      }
    } catch (error) {
      console.error('加载角色列表失败:', error)
    }
  }

  /**
   * 加载用户已分配角色
   */
  const loadUserRoles = async () => {
    if (!props.userData) return

    try {
      const response = await fetchUserRoleList(props.userData.id)
      if (response.success && response.data) {
        assignedRoles.value = response.data.result || []
        // 提取角色ID
        const roleIds = assignedRoles.value.map((role) => role.role_id)
        selectedRoleIds.value = [...roleIds]
        originalRoleIds.value = [...roleIds]
      }
    } catch (error) {
      console.error('加载用户角色失败:', error)
    }
  }

  /**
   * 刷新数据
   */
  const refreshData = async () => {
    await Promise.all([loadAllRoles(), loadUserRoles()])
  }
</script>

<style scoped>
  .dialog-footer {
    text-align: right;
  }
</style>
