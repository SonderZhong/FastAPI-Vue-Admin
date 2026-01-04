<template>
  <ElDrawer
    :model-value="modelValue"
    title="通知详情"
    size="550px"
    @open="handleOpen"
    @update:model-value="emit('update:modelValue', $event)"
    class="notification-detail-drawer"
  >
    <div v-if="loading" class="loading-wrapper">
      <ElSkeleton :rows="10" animated />
    </div>
    
    <div v-else-if="notification" class="detail-content">
      <!-- 基本信息 -->
      <div class="section">
        <h3 class="section-title">基本信息</h3>
        <ElDescriptions :column="1" border>
          <ElDescriptionsItem label="通知标题">{{ notification.title }}</ElDescriptionsItem>
          <ElDescriptionsItem label="通知类型">
            <ElTag :type="getTypeTagType(notification.type)" size="small">
              {{ getTypeName(notification.type) }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="通知范围">
            <ElTag :type="getScopeTagType(notification.scope)" size="small">
              {{ getScopeName(notification.scope) }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="优先级">
            <ElTag :type="getPriorityTagType(notification.priority)" size="small">
              {{ getPriorityName(notification.priority) }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="状态">
            <ElTag :type="getStatusTagType(notification.status)" size="small">
              {{ getStatusName(notification.status) }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="创建者">{{ notification.creator_name || '-' }}</ElDescriptionsItem>
          <ElDescriptionsItem label="创建时间">{{ formatDate(notification.created_at) }}</ElDescriptionsItem>
          <ElDescriptionsItem label="发布时间">{{ notification.publish_time ? formatDate(notification.publish_time) : '-' }}</ElDescriptionsItem>
          <ElDescriptionsItem label="过期时间">{{ notification.expire_time ? formatDate(notification.expire_time) : '永不过期' }}</ElDescriptionsItem>
        </ElDescriptions>
      </div>

      <!-- 通知内容 -->
      <div class="section">
        <h3 class="section-title">通知内容</h3>
        <div class="content-box" v-html="notification.content"></div>
      </div>

      <!-- 统计信息 -->
      <div v-if="notification.statistics" class="section">
        <h3 class="section-title">阅读统计</h3>
        <ElRow :gutter="20">
          <ElCol :span="8">
            <div class="stat-card">
              <div class="stat-value">{{ notification.statistics.total }}</div>
              <div class="stat-label">总推送</div>
            </div>
          </ElCol>
          <ElCol :span="8">
            <div class="stat-card success">
              <div class="stat-value">{{ notification.statistics.read }}</div>
              <div class="stat-label">已读</div>
            </div>
          </ElCol>
          <ElCol :span="8">
            <div class="stat-card warning">
              <div class="stat-value">{{ notification.statistics.unread }}</div>
              <div class="stat-label">未读</div>
            </div>
          </ElCol>
        </ElRow>
      </div>
    </div>

    <ElEmpty v-else description="通知不存在" />
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { fetchNotificationInfo, type NotificationInfo } from '@/api/system/notification'

interface Props {
  modelValue: boolean
  notificationId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const loading = ref(false)
const notification = ref<NotificationInfo | null>(null)

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getTypeName = (type: number) => {
  const names = ['登录通知', '全局公告', '系统消息']
  return names[type] || '未知'
}

const getTypeTagType = (type: number): 'info' | 'warning' | 'success' | 'primary' | 'danger' => {
  const map: Record<number, 'info' | 'warning' | 'success'> = { 0: 'info', 1: 'warning', 2: 'success' }
  return map[type] || 'info'
}

const getScopeName = (scope: number) => {
  const names = ['全部用户', '指定部门', '指定用户']
  return names[scope] || '未知'
}

const getScopeTagType = (scope: number): 'info' | 'warning' | 'success' | 'primary' | 'danger' => {
  const map: Record<number, 'primary' | 'warning' | 'success'> = { 0: 'primary', 1: 'warning', 2: 'success' }
  return map[scope] || 'info'
}

const getPriorityName = (priority: number) => {
  const names = ['普通', '重要', '紧急']
  return names[priority] || '普通'
}

const getPriorityTagType = (priority: number): 'info' | 'warning' | 'success' | 'primary' | 'danger' => {
  const map: Record<number, 'info' | 'warning' | 'danger'> = { 0: 'info', 1: 'warning', 2: 'danger' }
  return map[priority] || 'info'
}

const getStatusName = (status: number) => {
  const names = ['草稿', '已发布', '已撤回']
  return names[status] || '未知'
}

const getStatusTagType = (status: number): 'info' | 'warning' | 'success' | 'primary' | 'danger' => {
  const map: Record<number, 'info' | 'success' | 'warning'> = { 0: 'info', 1: 'success', 2: 'warning' }
  return map[status] || 'info'
}

const handleOpen = async () => {
  if (!props.notificationId) return
  
  try {
    loading.value = true
    const res = await fetchNotificationInfo(props.notificationId)
    if (res.success && res.data) {
      notification.value = res.data
    }
  } catch (e) {
    console.error('加载通知详情失败:', e)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.notification-detail-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
}

.loading-wrapper {
  padding: 20px;
}

.detail-content {
  padding: 0 4px;
}

.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.content-box {
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
  line-height: 1.6;
  word-break: break-word;
  
  :deep(p) {
    margin: 0 0 8px;
  }
  
  :deep(img) {
    max-width: 100%;
    height: auto;
  }
  
  :deep(a) {
    color: var(--el-color-primary);
  }
}

.stat-card {
  text-align: center;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  
  .stat-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .stat-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }
  
  &.success .stat-value {
    color: var(--el-color-success);
  }
  
  &.warning .stat-value {
    color: var(--el-color-warning);
  }
}
</style>
