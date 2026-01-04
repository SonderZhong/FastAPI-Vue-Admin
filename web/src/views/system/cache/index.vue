<template>
  <div class="cache-management">
    <!-- 缓存监控信息卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
      <!-- 基础信息卡片 -->
      <ElCard class="cache-monitor-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-blue-500"><Monitor /></ElIcon>
            <span class="font-medium">{{ $t('cache.monitor.title') }}</span>
          </div>
        </template>
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">{{ $t('cache.monitor.keyCount') }}</span>
            <span class="font-bold text-blue-600">{{
              cacheMonitor.db_size?.toLocaleString() || 0
            }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">{{ $t('cache.monitor.memory') }}</span>
            <span class="font-bold text-green-600">{{
              cacheMonitor.memory_stats?.used_memory_human ||
              formatMemory(cacheMonitor.info?.used_memory)
            }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">{{ $t('cache.monitor.version') }}</span>
            <span class="font-bold text-purple-600">{{
              cacheMonitor.info?.redis_version || 'N/A'
            }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">{{ $t('cache.monitor.clients') }}</span>
            <span class="font-bold text-indigo-600">{{
              cacheMonitor.connection_stats?.connected_clients || 0
            }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">{{ $t('cache.monitor.hitRate') }}</span>
            <span class="font-bold text-emerald-600"
              >{{ cacheMonitor.performance_stats?.hit_rate?.toFixed(1) || 0 }}%</span
            >
          </div>
        </div>
      </ElCard>

      <!-- 内存使用情况图表 -->
      <ElCard class="cache-memory-chart-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-green-500"><PieChart /></ElIcon>
            <span class="font-medium">{{ $t('cache.charts.memoryUsage') }}</span>
          </div>
        </template>
        <MemoryChart :memory-stats="cacheMonitor.memory_stats" />
      </ElCard>

      <!-- 命令统计图表 -->
      <ElCard class="cache-command-chart-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-orange-500"><DataLine /></ElIcon>
            <span class="font-medium">{{ $t('cache.charts.commandStats') }}</span>
          </div>
        </template>
        <CommandChart :command-stats="cacheMonitor.command_stats" />
      </ElCard>

      <!-- 性能统计图表 -->
      <ElCard class="cache-performance-chart-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-red-500"><Odometer /></ElIcon>
            <span class="font-medium">{{ $t('cache.charts.performanceStats') }}</span>
          </div>
        </template>
        <PerformanceChart
          :performance-stats="cacheMonitor.performance_stats"
          :connection-stats="cacheMonitor.connection_stats"
        />
      </ElCard>
    </div>

    <!-- 操作按钮区域 -->
    <div class="flex justify-center items-center space-x-4 mb-6">
      <ElButton
        v-auth="'cache:btn:infoList'"
        @click="refreshMonitor"
        type="primary"
        size="default"
        v-ripple
      >
        <ElIcon><Refresh /></ElIcon>
        {{ $t('cache.actions.refresh') }}
      </ElButton>
      <ElButton
        v-auth="'cache:btn:delete'"
        @click="handleClearAll"
        type="danger"
        size="default"
        plain
        v-ripple
      >
        <ElIcon><Delete /></ElIcon>
        {{ $t('cache.actions.clearAll') }}
      </ElButton>
    </div>

    <!-- 缓存名称列表 -->
    <ElCard class="art-table-card" shadow="never">
      <!-- 表格头部 -->
      <ArtTableHeader
        :showZebra="false"
        :loading="loading"
        v-model:columns="columnChecks"
        @refresh="refreshCacheNames"
      >
        <template #left>
          <ElButton
            v-if="hasSelectedRows"
            v-auth="'cache:btn:delete'"
            @click="handleBatchDelete"
            type="danger"
            plain
            v-ripple
          >
            <ElIcon><Delete /></ElIcon>
            {{ $t('buttons.delete') }}
          </ElButton>
        </template>
      </ArtTableHeader>

      <ArtTable
        ref="tableRef"
        :data="cacheNames"
        :loading="loading"
        :columns="columns"
        rowKey="cache_name"
        @selection-change="handleSelectionChange"
      />
    </ElCard>

    <!-- 缓存键列表对话框 -->
    <ElDialog
      v-model="keysDialogVisible"
      :title="$t('cache.keysDialog.title', { name: currentCacheName })"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="mb-4 flex justify-between items-center">
        <ElInput
          v-model="keySearchText"
          :placeholder="$t('cache.keysDialog.searchPlaceholder')"
          clearable
          class="w-60"
          @change="handleSearchKeys"
        >
          <template #prefix>
            <ElIcon><Search /></ElIcon>
          </template>
        </ElInput>
        <ElButton @click="handleRefreshKeys" type="primary" size="small">
          <ElIcon><Refresh /></ElIcon>
          {{ $t('buttons.refresh') }}
        </ElButton>
      </div>

      <ArtTable
        :data="cacheKeys"
        :loading="keysLoading"
        :pagination="keysPagination"
        :columns="keysColumns"
        @pagination:size-change="handleKeysPageSizeChange"
        @pagination:current-change="handleKeysCurrentChange"
        @selection-change="handleKeySelectionChange"
      />

      <template #footer>
        <div class="flex justify-between">
          <div>
            <ElButton v-if="hasSelectedKeys" @click="handleBatchDeleteKeys" type="danger" plain>
              <ElIcon><Delete /></ElIcon>
              {{ $t('cache.actions.batchDelete') }}
            </ElButton>
          </div>
          <div>
            <ElButton @click="keysDialogVisible = false">{{ $t('buttons.close') }}</ElButton>
          </div>
        </div>
      </template>
    </ElDialog>

    <!-- 缓存详情对话框 -->
    <CacheDetailDialog
      v-model="detailDialogVisible"
      :cache-name="currentCacheName"
      :cache-key="currentCacheKey"
    />

    <!-- 编辑缓存值对话框 -->
    <ElDialog
      v-model="editDialogVisible"
      :title="$t('cache.editDialog.title')"
      width="60%"
      :close-on-click-modal="false"
    >
      <ElForm label-width="120px">
        <ElFormItem :label="$t('cache.fields.cacheName')">
          <ElInput v-model="currentCacheName" readonly />
        </ElFormItem>
        <ElFormItem :label="$t('cache.fields.cacheKey')">
          <ElInput v-model="currentCacheKey" readonly />
        </ElFormItem>
        <ElFormItem :label="$t('cache.fields.cacheValue')">
          <ElInput
            v-model="currentCacheValue"
            type="textarea"
            :rows="8"
            :placeholder="$t('cache.editDialog.valuePlaceholder')"
          />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <div class="flex justify-end gap-2">
          <ElButton @click="editDialogVisible = false">{{ $t('common.cancel') }}</ElButton>
          <ElButton @click="handleSaveCacheValue" type="primary">{{
            $t('common.confirm')
          }}</ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, computed, h, reactive } from 'vue'
  import { ElMessage, ElMessageBox, ElTag, ElIcon, ElButton } from 'element-plus'
  import {
    Monitor,
    Refresh,
    Delete,
    View,
    Search,
    Edit,
    PieChart,
    DataLine,
    Odometer
  } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { useTableColumns } from '@/composables/useTableColumns'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
  import CacheDetailDialog from './modules/cache-detail-dialog.vue'
  import MemoryChart from './components/MemoryChart.vue'
  import CommandChart from './components/CommandChart.vue'
  import PerformanceChart from './components/PerformanceChart.vue'
  import {
    fetchCacheMonitor,
    fetchCacheNames,
    fetchCacheKeys,
    fetchCacheDetail,
    deleteCacheByName,
    deleteCacheByKey,
    deleteAllCache,
    updateCacheValue,
    type CacheMonitor,
    type CacheInfo,
    type CacheKeySearchParams,
    type UpdateCacheValueParams
  } from '@/api/system/cache'

  const { t } = useI18n()

  // 响应式数据
  const loading = ref(false)
  const keysLoading = ref(false)
  const cacheMonitor = ref<CacheMonitor>({})
  const cacheNames = ref<CacheInfo[]>([])
  const cacheKeys = ref<Array<{ key: string }>>([])
  const selectedRows = ref<CacheInfo[]>([])
  const selectedKeys = ref<string[]>([])

  // 表格配置
  const tableRef = ref()

  // 缓存键分页配置
  const keysPagination = reactive({
    current: 1,
    size: 10,
    total: 0
  })

  // 对话框状态
  const keysDialogVisible = ref(false)
  const detailDialogVisible = ref(false)
  const editDialogVisible = ref(false)
  const currentCacheName = ref('')
  const currentCacheKey = ref('')
  const currentCacheValue = ref('')

  // 搜索
  const keySearchText = ref('')

  // 计算属性
  const hasSelectedRows = computed(() => selectedRows.value.length > 0)
  const hasSelectedKeys = computed(() => selectedKeys.value.length > 0)

  // 表格列配置
  const { columnChecks, columns } = useTableColumns(() => [
    {
      type: 'selection' as const,
      width: 55,
      align: 'center'
    },
    {
      prop: 'cache_name',
      label: t('cache.fields.cacheName'),
      minWidth: 200,
      align: 'center',
      formatter: (row: CacheInfo) => {
        return h('div', { class: 'flex items-center justify-center' }, [
          h(ElTag, { type: 'primary', size: 'small', class: 'mr-2' }, () => row.cache_name)
        ])
      }
    },
    {
      prop: 'remark',
      label: t('cache.fields.remark'),
      minWidth: 300,
      align: 'center',
      showOverflowTooltip: true
    },
    {
      prop: 'actions',
      label: t('common.actions'),
      width: 200,
      align: 'center',
      fixed: 'right',
      formatter: (row: CacheInfo) => {
        return h('div', { class: 'flex gap-2 justify-center' }, [
          h(
            ElButton,
            {
              type: 'primary',
              link: true,
              size: 'small',
              onClick: () => handleViewKeys(row)
            },
            () => [h(ElIcon, {}, () => h(View)), t('cache.actions.viewKeys')]
          ),
          h(
            ElButton,
            {
              type: 'danger',
              link: true,
              size: 'small',
              onClick: () => handleDeleteCache(row)
            },
            () => [h(ElIcon, {}, () => h(Delete)), t('buttons.delete')]
          )
        ])
      }
    }
  ])

  // 缓存键表格列配置
  const keysColumns = computed(() => [
    {
      type: 'selection' as const,
      width: 55,
      align: 'center'
    },
    {
      type: 'index' as const,
      label: t('table.column.index'),
      width: 60,
      align: 'center'
    },
    {
      prop: 'key',
      label: t('cache.fields.cacheKey'),
      minWidth: 200,
      align: 'center',
      formatter: (row: { key: string }) => {
        return h(ElTag, { size: 'small' }, () => row.key)
      }
    },
    {
      prop: 'actions',
      label: t('common.actions'),
      width: 200,
      align: 'center',
      formatter: (row: { key: string }) => {
        return h('div', { class: 'flex gap-2 justify-center' }, [
          h(
            ElButton,
            {
              type: 'primary',
              link: true,
              size: 'small',
              onClick: () => handleViewCacheDetail(row.key)
            },
            () => [h(ElIcon, {}, () => h(View)), t('cache.actions.viewKeys')]
          ),
          h(
            ElButton,
            {
              type: 'warning',
              link: true,
              size: 'small',
              onClick: () => handleEditCacheValue(row.key)
            },
            () => [h(ElIcon, {}, () => h(Edit)), t('buttons.edit')]
          ),
          h(
            ElButton,
            {
              type: 'danger',
              link: true,
              size: 'small',
              onClick: () => handleDeleteCacheKey(row.key)
            },
            () => [h(ElIcon, {}, () => h(Delete)), t('buttons.delete')]
          )
        ])
      }
    }
  ])

  // 格式化内存大小
  const formatMemory = (bytes?: number): string => {
    if (!bytes) return 'N/A'
    const sizes = ['B', 'KB', 'MB', 'GB']
    let i = 0
    while (bytes >= 1024 && i < sizes.length - 1) {
      bytes /= 1024
      i++
    }
    return `${bytes.toFixed(2)} ${sizes[i]}`
  }

  // 获取缓存监控信息
  const getCacheMonitor = async () => {
    try {
      const response = await fetchCacheMonitor()
      if (response?.success) {
        cacheMonitor.value = response.data || {}
      }
    } catch (error) {
      console.error('获取缓存监控信息失败:', error)
    }
  }

  // 获取缓存名称列表
  const getCacheNames = async () => {
    loading.value = true
    try {
      const response = await fetchCacheNames()
      if (response?.success) {
        cacheNames.value = response.data || []
      }
    } catch (error) {
      console.error('获取缓存名称列表失败:', error)
      ElMessage.error(t('cache.messages.fetchNamesError'))
    } finally {
      loading.value = false
    }
  }

  // 获取缓存键列表
  const getCacheKeys = async (cacheName: string, refresh = false) => {
    if (refresh) {
      keysPagination.current = 1
      keySearchText.value = ''
    }

    keysLoading.value = true
    try {
      const params: CacheKeySearchParams = {
        page: keysPagination.current,
        size: keysPagination.size,
        search: keySearchText.value || undefined
      }

      const response = await fetchCacheKeys(cacheName, params)
      if (response?.success) {
        cacheKeys.value = response.data?.result || []
        keysPagination.total = response.data?.total || 0
      }
    } catch (error) {
      console.error('获取缓存键列表失败:', error)
      ElMessage.error(t('cache.messages.fetchKeysError'))
    } finally {
      keysLoading.value = false
    }
  }

  // 刷新监控信息
  const refreshMonitor = async () => {
    await getCacheMonitor()
    ElMessage.success(t('cache.messages.refreshSuccess'))
  }

  // 刷新缓存名称列表
  const refreshCacheNames = async () => {
    await getCacheNames()
    ElMessage.success(t('cache.messages.refreshSuccess'))
  }

  // 查看缓存键
  const handleViewKeys = async (row: CacheInfo) => {
    currentCacheName.value = row.cache_name || ''
    keysDialogVisible.value = true
    await getCacheKeys(currentCacheName.value, true)
  }

  // 查看缓存详情
  const handleViewCacheDetail = (cacheKey: string) => {
    currentCacheKey.value = cacheKey
    detailDialogVisible.value = true
  }

  // 编辑缓存值
  const handleEditCacheValue = async (cacheKey: string) => {
    currentCacheKey.value = cacheKey
    try {
      const response = await fetchCacheDetail(currentCacheName.value, cacheKey)
      if (response?.success) {
        const value = response.data?.cache_value
        currentCacheValue.value = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
        editDialogVisible.value = true
      }
    } catch (error) {
      console.error('获取缓存详情失败:', error)
      ElMessage.error(t('cache.messages.fetchDetailError'))
    }
  }

  // 保存缓存值
  const handleSaveCacheValue = async () => {
    try {
      const params: UpdateCacheValueParams = {
        cache_value: currentCacheValue.value
      }
      const response = await updateCacheValue(currentCacheName.value, currentCacheKey.value, params)
      if (response?.success) {
        ElMessage.success(t('cache.messages.updateSuccess'))
        editDialogVisible.value = false
        await getCacheKeys(currentCacheName.value)
      }
    } catch (error) {
      console.error('更新缓存值失败:', error)
      ElMessage.error(t('cache.messages.updateError'))
    }
  }

  // 搜索缓存键
  const handleSearchKeys = () => {
    keysPagination.current = 1
    getCacheKeys(currentCacheName.value)
  }

  // 刷新缓存键
  const handleRefreshKeys = () => {
    getCacheKeys(currentCacheName.value, true)
  }

  // 缓存键分页处理
  const handleKeysPageSizeChange = (size: number) => {
    keysPagination.size = size
    keysPagination.current = 1
    getCacheKeys(currentCacheName.value)
  }

  const handleKeysCurrentChange = (current: number) => {
    keysPagination.current = current
    getCacheKeys(currentCacheName.value)
  }

  // 删除单个缓存
  const handleDeleteCache = async (row: CacheInfo) => {
    try {
      await ElMessageBox.confirm(
        t('cache.messages.deleteCacheConfirm', { name: row.cache_name }),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      const response = await deleteCacheByName(row.cache_name!)
      if (response?.success) {
        ElMessage.success(t('cache.messages.deleteSuccess'))
        await getCacheNames()
        await getCacheMonitor()
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除缓存失败:', error)
        ElMessage.error(t('cache.messages.deleteError'))
      }
    }
  }

  // 删除缓存键
  const handleDeleteCacheKey = async (cacheKey: string) => {
    try {
      await ElMessageBox.confirm(
        t('cache.messages.deleteCacheKeyConfirm', { key: cacheKey }),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      const response = await deleteCacheByKey(cacheKey)
      if (response?.success) {
        ElMessage.success(t('cache.messages.deleteSuccess'))
        await getCacheKeys(currentCacheName.value)
        await getCacheMonitor()
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除缓存键失败:', error)
        ElMessage.error(t('cache.messages.deleteError'))
      }
    }
  }

  // 批量删除缓存
  const handleBatchDelete = async () => {
    try {
      await ElMessageBox.confirm(
        t('cache.messages.batchDeleteConfirm', { count: selectedRows.value.length }),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      for (const row of selectedRows.value) {
        await deleteCacheByName(row.cache_name!)
      }

      ElMessage.success(t('cache.messages.deleteSuccess'))
      selectedRows.value = []
      await getCacheNames()
      await getCacheMonitor()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量删除缓存失败:', error)
        ElMessage.error(t('cache.messages.deleteError'))
      }
    }
  }

  // 批量删除缓存键
  const handleBatchDeleteKeys = async () => {
    try {
      await ElMessageBox.confirm(
        t('cache.messages.batchDeleteKeysConfirm', { count: selectedKeys.value.length }),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      for (const key of selectedKeys.value) {
        await deleteCacheByKey(key)
      }

      ElMessage.success(t('cache.messages.deleteSuccess'))
      selectedKeys.value = []
      await getCacheKeys(currentCacheName.value)
      await getCacheMonitor()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量删除缓存键失败:', error)
        ElMessage.error(t('cache.messages.deleteError'))
      }
    }
  }

  // 清空所有缓存
  const handleClearAll = async () => {
    try {
      await ElMessageBox.confirm(t('cache.messages.clearAllConfirm'), t('common.warning'), {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      })

      const response = await deleteAllCache()
      if (response?.success) {
        ElMessage.success(t('cache.messages.clearAllSuccess'))
        await getCacheNames()
        await getCacheMonitor()
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('清空缓存失败:', error)
        ElMessage.error(t('cache.messages.clearAllError'))
      }
    }
  }

  // 表格选择变化
  const handleSelectionChange = (selection: CacheInfo[]) => {
    selectedRows.value = selection
  }

  // 缓存键选择变化
  const handleKeySelectionChange = (selection: any[]) => {
    selectedKeys.value = selection.map((item) => item.key)
  }

  // 初始化
  onMounted(async () => {
    await getCacheMonitor()
    await getCacheNames()
  })
</script>

<style lang="scss" scoped>
  .cache-management {
    .cache-monitor-card,
    .cache-memory-chart-card,
    .cache-command-chart-card,
    .cache-performance-chart-card {
      transition: all 0.3s ease;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--art-card-shadow);
      border: 1px solid var(--art-card-border);

      &:hover {
        transform: translateY(-2px);
        box-shadow: var(--art-box-shadow-sm);
      }

      :deep(.el-card__header) {
        padding: 16px 20px;
        border-bottom: 1px solid var(--art-border-color);
      }

      :deep(.el-card__body) {
        padding: 20px;
      }
    }

    .cache-monitor-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-primary));
        color: rgb(var(--art-primary));

        .el-icon {
          color: rgb(var(--art-primary));
        }
      }
    }

    .cache-memory-chart-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-danger));
        color: rgb(var(--art-danger));

        .el-icon {
          color: rgb(var(--art-danger));
        }
      }
    }

    .cache-command-chart-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-secondary));
        color: rgb(var(--art-secondary));

        .el-icon {
          color: rgb(var(--art-secondary));
        }
      }
    }

    .cache-performance-chart-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-warning));
        color: rgb(var(--art-warning));

        .el-icon {
          color: rgb(var(--art-warning));
        }
      }
    }

    .art-table-card {
      margin-top: 20px;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--art-card-shadow);
    }
  }
</style>
