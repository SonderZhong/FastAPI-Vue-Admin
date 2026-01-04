<template>
  <div class="art-full-height">
    <ElContainer class="h-full">
      <!-- 左侧类型筛选 -->
      <ElAside width="200px" class="type-aside">
        <ElCard shadow="never" class="h-full type-card">
          <template #header>
            <span class="font-medium">通知类型</span>
          </template>
          
          <div class="type-list">
            <div
              v-for="item in typeOptions"
              :key="item.value"
              class="type-item"
              :class="{ active: selectedType === item.value }"
              @click="handleTypeChange(item.value)"
            >
              <ElIcon :size="18" :class="item.iconClass">
                <component :is="item.icon" />
              </ElIcon>
              <span>{{ item.label }}</span>
              <ElBadge v-if="item.count > 0" :value="item.count" :max="99" />
            </div>
          </div>
        </ElCard>
      </ElAside>

      <!-- 右侧主内容区 -->
      <ElMain class="main-content">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <ElBreadcrumb separator="/">
              <ElBreadcrumbItem>通知管理</ElBreadcrumbItem>
              <ElBreadcrumbItem>{{ currentTypeName }}</ElBreadcrumbItem>
            </ElBreadcrumb>
          </div>
          <div class="toolbar-right">
            <ElInput
              v-model="searchText"
              placeholder="搜索通知标题"
              clearable
              size="small"
              style="width: 200px"
              :prefix-icon="Search"
              @input="handleSearch"
            />
            <ElSelect v-model="selectedStatus" placeholder="状态" size="small" clearable style="width: 120px" @change="loadData">
              <ElOption label="全部" :value="-1" />
              <ElOption label="草稿" :value="0" />
              <ElOption label="已发布" :value="1" />
              <ElOption label="已撤回" :value="2" />
            </ElSelect>
            <ElButton
              v-auth="'notification:btn:add'"
              round
              type="primary"
              size="small"
              :icon="Plus"
              @click="showDrawer('add')"
            >
              新建通知
            </ElButton>
          </div>
        </div>

        <!-- 表格卡片 -->
        <ElCard class="table-card" shadow="never">
          <ElTable v-loading="loading" :data="notifications" border stripe>
            <ElTableColumn type="index" width="60" align="center" label="#" />
            <ElTableColumn prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <ElTableColumn prop="type" label="类型" width="100" align="center">
              <template #default="{ row }">
                <ElTag :type="getTypeTagType(row.type)" size="small">
                  {{ getTypeName(row.type) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="scope" label="范围" width="100" align="center">
              <template #default="{ row }">
                <ElTag :type="getScopeTagType(row.scope)" size="small">
                  {{ getScopeName(row.scope) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="priority" label="优先级" width="80" align="center">
              <template #default="{ row }">
                <ElTag :type="getPriorityTagType(row.priority)" size="small">
                  {{ getPriorityName(row.priority) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <ElTag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusName(row.status) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="creator_name" label="创建者" width="100" align="center" />
            <ElTableColumn prop="publish_time" label="发布时间" width="160" align="center">
              <template #default="{ row }">
                {{ row.publish_time ? formatDate(row.publish_time) : '-' }}
              </template>
            </ElTableColumn>
            <ElTableColumn prop="created_at" label="创建时间" width="160" align="center">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="操作" width="200" align="center" fixed="right">
              <template #default="{ row }">
                <ElButton type="primary" size="small" link @click="showDetail(row)">详情</ElButton>
                <ElButton
                  v-if="row.status === 0"
                  v-auth="'notification:btn:update'"
                  type="warning"
                  size="small"
                  link
                  @click="showDrawer('edit', row)"
                >
                  编辑
                </ElButton>
                <ElButton
                  v-if="row.status === 0"
                  v-auth="'notification:btn:publish'"
                  type="success"
                  size="small"
                  link
                  @click="handlePublish(row)"
                >
                  发布
                </ElButton>
                <ElButton
                  v-if="row.status === 1"
                  v-auth="'notification:btn:revoke'"
                  type="warning"
                  size="small"
                  link
                  @click="handleRevoke(row)"
                >
                  撤回
                </ElButton>
                <ElButton
                  v-auth="'notification:btn:delete'"
                  type="danger"
                  size="small"
                  link
                  @click="handleDelete(row)"
                >
                  删除
                </ElButton>
              </template>
            </ElTableColumn>
          </ElTable>

          <!-- 分页 -->
          <div class="pagination-wrapper">
            <span class="total-text">共 {{ total }} 条</span>
            <ElPagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              :total="total"
              layout="sizes, prev, pager, next"
              small
              @size-change="loadData"
              @current-change="loadData"
            />
          </div>
        </ElCard>
      </ElMain>
    </ElContainer>

    <!-- 通知编辑抽屉 -->
    <NotificationDrawer
      v-model="drawerVisible"
      :dialog-type="drawerType"
      :notification-data="currentNotification"
      @success="loadData"
    />

    <!-- 通知详情抽屉 -->
    <NotificationDetailDrawer
      v-model="detailVisible"
      :notification-id="currentNotification?.id"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Bell, Notification, ChatDotRound, Message } from '@element-plus/icons-vue'
import {
  fetchNotificationList,
  publishNotification,
  revokeNotification,
  deleteNotification,
  NotificationType,
  NotificationStatus,
  type NotificationInfo
} from '@/api/system/notification'
import NotificationDrawer from './modules/notification-drawer.vue'
import NotificationDetailDrawer from './modules/notification-detail-drawer.vue'

defineOptions({ name: 'NotificationManage' })

// Tag类型定义
type TagType = 'info' | 'warning' | 'success' | 'primary' | 'danger'

// 类型选项
const typeOptions = [
  { value: -1, label: '全部', icon: Bell, iconClass: 'text-blue-500', count: 0 },
  { value: NotificationType.ANNOUNCEMENT, label: '全局公告', icon: Notification, iconClass: 'text-orange-500', count: 0 },
  { value: NotificationType.MESSAGE, label: '系统消息', icon: Message, iconClass: 'text-green-500', count: 0 },
  { value: NotificationType.LOGIN, label: '登录通知', icon: ChatDotRound, iconClass: 'text-purple-500', count: 0 }
]

// 响应式数据
const loading = ref(false)
const notifications = ref<NotificationInfo[]>([])
const selectedType = ref<NotificationType | -1>(-1)
const selectedStatus = ref<NotificationStatus | -1>(-1)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 抽屉状态
const drawerVisible = ref(false)
const drawerType = ref<'add' | 'edit'>('add')
const currentNotification = ref<NotificationInfo | undefined>(undefined)
const detailVisible = ref(false)

// 计算属性
const currentTypeName = computed(() => {
  const item = typeOptions.find(t => t.value === selectedType.value)
  return item?.label || '全部'
})

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 获取类型名称
const getTypeName = (type: number) => {
  const names = ['登录通知', '全局公告', '系统消息']
  return names[type] || '未知'
}

const getTypeTagType = (type: number): TagType => {
  const map: Record<number, TagType> = { 0: 'info', 1: 'warning', 2: 'success' }
  return map[type] || 'info'
}

// 获取范围名称
const getScopeName = (scope: number) => {
  const names = ['全部用户', '指定部门', '指定用户']
  return names[scope] || '未知'
}

const getScopeTagType = (scope: number): TagType => {
  const map: Record<number, TagType> = { 0: 'primary', 1: 'warning', 2: 'success' }
  return map[scope] || 'info'
}

// 获取优先级名称
const getPriorityName = (priority: number) => {
  const names = ['普通', '重要', '紧急']
  return names[priority] || '普通'
}

const getPriorityTagType = (priority: number): TagType => {
  const map: Record<number, TagType> = { 0: 'info', 1: 'warning', 2: 'danger' }
  return map[priority] || 'info'
}

// 获取状态名称
const getStatusName = (status: number) => {
  const names = ['草稿', '已发布', '已撤回']
  return names[status] || '未知'
}

const getStatusTagType = (status: number): TagType => {
  const map: Record<number, TagType> = { 0: 'info', 1: 'success', 2: 'warning' }
  return map[status] || 'info'
}

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    const res = await fetchNotificationList({
      page: currentPage.value,
      pageSize: pageSize.value,
      type: selectedType.value === -1 ? undefined : selectedType.value,
      status: selectedStatus.value === -1 ? undefined : selectedStatus.value,
      title: searchText.value || undefined
    })
    if (res.success && res.data) {
      notifications.value = res.data.result || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('加载通知列表失败:', e)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 类型切换
const handleTypeChange = (type: NotificationType | -1) => {
  selectedType.value = type
  currentPage.value = 1
  loadData()
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

// 显示抽屉
const showDrawer = (type: 'add' | 'edit', row?: NotificationInfo) => {
  drawerType.value = type
  currentNotification.value = row
  drawerVisible.value = true
}

// 显示详情
const showDetail = (row: NotificationInfo) => {
  currentNotification.value = row
  detailVisible.value = true
}

// 发布通知
const handlePublish = async (row: NotificationInfo) => {
  const confirm = await ElMessageBox.confirm(
    `确定发布通知【${row.title}】吗？发布后将推送给目标用户。`,
    '确认发布',
    { type: 'warning' }
  ).catch(() => false)
  if (!confirm) return

  try {
    const res = await publishNotification(row.id)
    if (res.success) {
      ElMessage.success(`发布成功！已推送给 ${res.data?.total_users || 0} 个用户`)
      loadData()
    } else {
      ElMessage.error(res.msg || '发布失败')
    }
  } catch (e) {
    console.error('发布失败:', e)
    ElMessage.error('发布失败')
  }
}

// 撤回通知
const handleRevoke = async (row: NotificationInfo) => {
  const confirm = await ElMessageBox.confirm(
    `确定撤回通知【${row.title}】吗？`,
    '确认撤回',
    { type: 'warning' }
  ).catch(() => false)
  if (!confirm) return

  try {
    const res = await revokeNotification(row.id)
    if (res.success) {
      ElMessage.success('撤回成功')
      loadData()
    } else {
      ElMessage.error(res.msg || '撤回失败')
    }
  } catch (e) {
    console.error('撤回失败:', e)
    ElMessage.error('撤回失败')
  }
}

// 删除通知
const handleDelete = async (row: NotificationInfo) => {
  const confirm = await ElMessageBox.confirm(
    `确定删除通知【${row.title}】吗？`,
    '确认删除',
    { type: 'warning' }
  ).catch(() => false)
  if (!confirm) return

  try {
    const res = await deleteNotification(row.id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadData()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    console.error('删除失败:', e)
    ElMessage.error('删除失败')
  }
}

onMounted(() => loadData())
</script>

<style lang="scss" scoped>
:deep(.el-container) {
  height: 100%;
}

.type-aside {
  height: 100%;
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.type-card {
  height: 100%;
  border-radius: 0;
  border: none;
  
  :deep(.el-card__header) {
    padding: 12px 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  :deep(.el-card__body) {
    padding: 8px;
  }
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.type-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: var(--el-fill-color-light);
  }
  
  &.active {
    background: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
  }
  
  span {
    flex: 1;
    font-size: 14px;
  }
}

.main-content {
  height: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
  background: var(--el-fill-color-lighter);
}

.toolbar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-card {
  flex: 1;
  margin: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 12px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
}

.pagination-wrapper {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.total-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
