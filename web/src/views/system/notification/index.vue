<template>
  <div class="art-full-height">
    <!-- 搜索区域 -->
    <div class="search-area">
      <div class="search-form">
        <div class="search-item">
          <span class="search-label">通知类型</span>
          <ElSelect v-model="selectedType" placeholder="类型" style="width: 140px" @change="handleTypeChange">
            <ElOption v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
        </div>
        <div class="search-item">
          <span class="search-label">状态</span>
          <ElSelect v-model="selectedStatus" placeholder="状态" style="width: 140px" @change="loadData">
            <ElOption label="全部" :value="-1" />
            <ElOption label="草稿" :value="0" />
            <ElOption label="已发布" :value="1" />
            <ElOption label="已撤回" :value="2" />
          </ElSelect>
        </div>
        <div class="search-item">
          <span class="search-label">标题</span>
          <ElInput
            v-model="searchText"
            placeholder="搜索通知标题"
            clearable
            style="width: 220px"
            :prefix-icon="Search"
            @input="handleSearch"
          />
        </div>
      </div>
    </div>

    <!-- 表格卡片 -->
    <ElCard class="art-table-card" shadow="never">
      <ArtTableHeader :loading="loading" v-model:columns="columnChecks" @refresh="refreshData">
        <template #left>
          <ElButton
            v-auth="'notification:btn:add'"
            type="primary"
            :icon="Plus"
            @click="showDrawer('add')"
          >
            新建通知
          </ElButton>
        </template>
      </ArtTableHeader>
      
      <ArtTable
        :data="data"
        :loading="loading"
        :columns="columns"
        :pagination="pagination"
        :show-table-header="false"
        row-key="id"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

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
import { ref, h, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElTag, ElButton } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useTable } from '@/composables/useTable'
import { usePermission } from '@/composables/usePermission'
import ArtTable from '@/components/core/tables/art-table/index.vue'
import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
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

const { t: $t } = useI18n()
const { hasPermission } = usePermission()

// Tag类型定义
type TagType = 'info' | 'warning' | 'success' | 'primary' | 'danger'

// 类型选项
const typeOptions = [
  { value: -1, label: '全部' },
  { value: NotificationType.ANNOUNCEMENT, label: '全局公告' },
  { value: NotificationType.MESSAGE, label: '系统消息' },
  { value: NotificationType.LOGIN, label: '登录通知' }
]

// 响应式数据
const selectedType = ref<NotificationType | -1>(-1)
const selectedStatus = ref<NotificationStatus | -1>(-1)
const searchText = ref('')

// 抽屉状态
const drawerVisible = ref(false)
const drawerType = ref<'add' | 'edit'>('add')
const currentNotification = ref<NotificationInfo | undefined>(undefined)
const detailVisible = ref(false)

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

// 使用 useTable 管理通知列表
const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  searchParams,
  handleSizeChange,
  handleCurrentChange,
  getData,
  refreshUpdate
} = useTable<typeof fetchNotificationList>({
  core: {
    apiFn: fetchNotificationList,
    apiParams: {},
    paginationKey: { current: 'page', size: 'pageSize' },
    columnsFactory: () => [
      { type: 'index', width: 80, label: $t('table.column.index'), align: 'center' },
      { prop: 'title', label: '标题', align: 'center', showOverflowTooltip: true },
      {
        prop: 'type',
        label: '类型',
        width: 100,
        align: 'center',
        formatter: (row: NotificationInfo) => h(ElTag, { type: getTypeTagType(row.type), size: 'small' }, () => getTypeName(row.type))
      },
      {
        prop: 'scope',
        label: '范围',
        width: 100,
        align: 'center',
        formatter: (row: NotificationInfo) => h(ElTag, { type: getScopeTagType(row.scope), size: 'small' }, () => getScopeName(row.scope))
      },
      {
        prop: 'priority',
        label: '优先级',
        width: 80,
        align: 'center',
        formatter: (row: NotificationInfo) => h(ElTag, { type: getPriorityTagType(row.priority), size: 'small' }, () => getPriorityName(row.priority))
      },
      {
        prop: 'status',
        label: '状态',
        width: 80,
        align: 'center',
        formatter: (row: NotificationInfo) => h(ElTag, { type: getStatusTagType(row.status), size: 'small' }, () => getStatusName(row.status))
      },
      { prop: 'creator_name', label: '创建者', width: 100, align: 'center' },
      {
        prop: 'publish_time',
        label: '发布时间',
        width: 160,
        align: 'center',
        formatter: (row: NotificationInfo) => row.publish_time ? formatDate(row.publish_time) : '-'
      },
      {
        prop: 'created_at',
        label: '创建时间',
        width: 160,
        align: 'center',
        formatter: (row: NotificationInfo) => formatDate(row.created_at)
      },
      {
        prop: 'actions',
        label: '操作',
        width: 200,
        align: 'center',
        fixed: 'right',
        formatter: (row: NotificationInfo) => {
          const buttons = []
          buttons.push(h(ElButton, { type: 'primary', size: 'small', onClick: () => showDetail(row) }, () => '详情'))
          if (row.status === 0 && hasPermission('notification:btn:update')) {
            buttons.push(h(ElButton, { type: 'warning', size: 'small', onClick: () => showDrawer('edit', row) }, () => '编辑'))
          }
          if (row.status === 0 && hasPermission('notification:btn:publish')) {
            buttons.push(h(ElButton, { type: 'success', size: 'small', onClick: () => handlePublish(row) }, () => '发布'))
          }
          if (row.status === 1 && hasPermission('notification:btn:revoke')) {
            buttons.push(h(ElButton, { type: 'warning', size: 'small', onClick: () => handleRevoke(row) }, () => '撤回'))
          }
          if (hasPermission('notification:btn:delete')) {
            buttons.push(h(ElButton, { type: 'danger', size: 'small', onClick: () => handleDelete(row) }, () => '删除'))
          }
          return h('div', { class: 'flex gap-2 justify-center' }, buttons)
        }
      }
    ]
  },
  performance: {
    enableCache: true,
    cacheTime: 5 * 60 * 1000,
    debounceTime: 300
  }
})

// 刷新数据
const refreshData = () => refreshUpdate()

// 加载数据
const loadData = async () => {
  Object.assign(searchParams, {
    type: selectedType.value === -1 ? undefined : selectedType.value,
    status: selectedStatus.value === -1 ? undefined : selectedStatus.value,
    title: searchText.value || undefined
  })
  getData()
}

// 类型切换
const handleTypeChange = () => {
  ;(searchParams as any).page = 1
  loadData()
}

// 搜索
const handleSearch = () => {
  ;(searchParams as any).page = 1
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
      refreshUpdate()
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
      refreshUpdate()
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
      refreshUpdate()
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
.search-area {
  flex-shrink: 0;
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 12px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 24px;
}

.search-item {
  display: flex;
  align-items: center;
  gap: 12px;
  
  :deep(.el-input),
  :deep(.el-select) {
    --el-component-size: 36px;
  }
}

.search-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.art-table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  margin-top: 0;
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }
  
  .table-header {
    flex-shrink: 0;
    margin-bottom: 12px;
  }
  
  :deep(.art-table) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }
}
</style>
