<template>
  <ElDrawer
    v-model="visible"
    :title="$t('user.assignRoles', '分配角色') + (userData ? ` - ${userData.nickname}` : '')"
    size="500px"
    :destroy-on-close="false"
    class="role-drawer"
    @close="handleClose"
  >
    <div v-if="userData" class="h-full flex flex-col">
      <!-- 用户信息 -->
      <div class="user-info-card">
        <ElAvatar :size="48" :src="getAvatarUrl(userData.avatar)">
          <ElIcon><User /></ElIcon>
        </ElAvatar>
        <div class="user-info">
          <div class="user-name">{{ userData.nickname }}</div>
          <div class="user-meta">@{{ userData.username }} · {{ userData.department_name || '无部门' }}</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <ElButton size="small" round @click="selectAllRoles">
          <ElIcon class="mr-1"><Select /></ElIcon>
          {{ $t('buttons.selectAll', '全选') }}
        </ElButton>
        <ElButton size="small" round @click="deselectAllRoles">
          <ElIcon class="mr-1"><CloseBold /></ElIcon>
          {{ $t('buttons.deselectAll', '取消') }}
        </ElButton>
        <ElButton size="small" round type="info" @click="resetToOriginal">
          <ElIcon class="mr-1"><RefreshRight /></ElIcon>
          {{ $t('buttons.reset', '重置') }}
        </ElButton>
      </div>

      <!-- 角色列表 -->
      <div class="role-list-container">
        <ElScrollbar>
          <div v-if="loading" class="loading-state">
            <ElIcon class="is-loading"><Loading /></ElIcon>
            <span>加载中...</span>
          </div>
          <div v-else-if="allRoles.length > 0" class="role-list">
            <ElCheckboxGroup v-model="selectedRoleIds">
              <div
                v-for="role in allRoles"
                :key="role.id"
                class="role-item"
                :class="{ 'is-selected': selectedRoleIds.includes(role.id) }"
                @click="toggleRole(role.id)"
              >
                <ElCheckbox :value="role.id" @click.stop />
                <div class="role-content">
                  <div class="role-name">
                    <span class="role-name-text">{{ role.name }}</span>
                    <ElTag v-if="originalRoleIds.includes(role.id)" type="success" size="small" round>
                      已分配
                    </ElTag>
                  </div>
                  <div class="role-desc">{{ role.description || '暂无描述' }}</div>
                </div>
              </div>
            </ElCheckboxGroup>
          </div>
          <div v-else class="empty-state">
            <ElIcon :size="40" class="text-gray-300"><User /></ElIcon>
            <p>{{ $t('user.noAvailableRoles', '暂无可分配角色') }}</p>
          </div>
        </ElScrollbar>
      </div>

      <!-- 选择统计 -->
      <div class="selection-info">
        <span>已选择 {{ selectedRoleIds.length }} 个角色</span>
        <span v-if="hasChanges" class="has-changes">（有修改）</span>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <ElButton round @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" round :loading="submitting" :disabled="!hasChanges" @click="handleSubmit">
          {{ $t('buttons.confirm', '确认') }}
        </ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Select, CloseBold, RefreshRight, Loading } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { fetchRoleList, type RoleInfo } from '@/api/system/role'
import { fetchUserRoleList, assignUserRoles, type UserInfo, type UserRoleInfo } from '@/api/system/user'
import { getAvatarUrl } from '@/utils'

const { t: $t } = useI18n()

interface Props {
  modelValue: boolean
  userData?: UserInfo
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  userData: undefined
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const allRoles = ref<RoleInfo[]>([])
const assignedRoles = ref<UserRoleInfo[]>([])
const selectedRoleIds = ref<string[]>([])
const originalRoleIds = ref<string[]>([])

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

watch(visible, (newVisible) => {
  if (newVisible && props.userData) {
    refreshData()
  }
})

const handleClose = () => {
  visible.value = false
}

const selectAllRoles = () => {
  selectedRoleIds.value = allRoles.value.map((role) => role.id)
}

const deselectAllRoles = () => {
  selectedRoleIds.value = []
}

const resetToOriginal = () => {
  selectedRoleIds.value = [...originalRoleIds.value]
}

const toggleRole = (roleId: string) => {
  const index = selectedRoleIds.value.indexOf(roleId)
  if (index > -1) {
    selectedRoleIds.value.splice(index, 1)
  } else {
    selectedRoleIds.value.push(roleId)
  }
}

const handleSubmit = async () => {
  if (!props.userData || !hasChanges.value) return

  try {
    submitting.value = true
    await assignUserRoles({
      user_id: props.userData.id,
      role_ids: selectedRoleIds.value
    })
    ElMessage.success($t('user.assignRoleSuccess', '角色分配成功'))
    emit('success')
    handleClose()
  } catch (error) {
    console.error('分配角色失败:', error)
    ElMessage.error($t('user.assignRoleFailed', '角色分配失败'))
  } finally {
    submitting.value = false
  }
}

const loadAllRoles = async () => {
  try {
    const response = await fetchRoleList({
      page: 1,
      pageSize: 1000,
      department_ids: props.userData?.department_id
    })
    if (response.success && response.data) {
      allRoles.value = response.data.result || []
    }
  } catch (error) {
    console.error('加载角色列表失败:', error)
  }
}

const loadUserRoles = async () => {
  if (!props.userData) return
  try {
    const response = await fetchUserRoleList(props.userData.id)
    if (response.success && response.data) {
      assignedRoles.value = response.data.result || []
      const roleIds = assignedRoles.value.map((role) => role.role_id)
      selectedRoleIds.value = [...roleIds]
      originalRoleIds.value = [...roleIds]
    }
  } catch (error) {
    console.error('加载用户角色失败:', error)
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([loadAllRoles(), loadUserRoles()])
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.role-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
  
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  :deep(.el-drawer__body) {
    padding: 0;
    display: flex;
    flex-direction: column;
  }
  
  :deep(.el-drawer__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

.user-info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.user-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.action-bar {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.role-list-container {
  flex: 1;
  min-height: 0;
  padding: 12px 20px;
  
  :deep(.el-scrollbar) {
    height: 100%;
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--el-text-color-secondary);
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    border-color: var(--el-color-primary-light-5);
    background: var(--el-color-primary-light-9);
  }
  
  &.is-selected {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }
}

.role-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.role-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  
  .role-name-text {
    word-break: break-word;
    line-height: 1.4;
  }
}

.role-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--el-text-color-secondary);
  
  p {
    margin-top: 12px;
  }
}

.selection-info {
  padding: 12px 20px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
  
  .has-changes {
    color: var(--el-color-warning);
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
