<template>
  <div class="art-full-height">
    <!-- 头部统计 -->
    <div class="stats-area">
      <div class="stat-item">
        <div class="stat-value">{{ statistics.total_count }}</div>
        <div class="stat-label">{{ t('file.totalFiles') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatFileSize(statistics.total_size) }}</div>
        <div class="stat-label">{{ t('file.totalSize') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ storageConfig.storage_type }}</div>
        <div class="stat-label">{{ t('file.storageType') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ storageConfig.max_size }}MB</div>
        <div class="stat-label">{{ t('file.maxSize') }}</div>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-area">
      <div class="search-form">
        <div class="search-item">
          <span class="search-label">{{ t('file.fileType') }}</span>
          <ElSelect v-model="selectedFileType" placeholder="全部" clearable style="width: 140px" @change="handleSearch">
            <ElOption v-for="(label, key) in FileTypeLabels" :key="key" :label="label" :value="key" />
          </ElSelect>
        </div>
        <div class="search-item">
          <span class="search-label">{{ t('file.storageType') }}</span>
          <ElSelect v-model="selectedStorageType" placeholder="全部" clearable style="width: 140px" @change="handleSearch">
            <ElOption v-for="(label, key) in StorageTypeLabels" :key="key" :label="label" :value="key" />
          </ElSelect>
        </div>
        <div class="search-item">
          <span class="search-label">{{ t('file.fileName') }}</span>
          <ElInput
            v-model="searchText"
            :placeholder="t('file.searchPlaceholder')"
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
      <ArtTableHeader :loading="loading" v-model:columns="columnChecks" @refresh="loadData">
        <template #left>
          <ElUpload
            v-auth="'file:btn:upload'"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :http-request="handleUpload"
            multiple
          >
            <ElButton type="primary" :icon="Upload">
              {{ t('file.upload') }}
            </ElButton>
          </ElUpload>
          <ElButton
            v-if="selectedIds.length > 0"
            v-auth="'file:btn:delete'"
            type="danger"
            plain
            @click="handleBatchDelete"
          >
            {{ t('buttons.batchDelete') }} ({{ selectedIds.length }})
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
        @selection-change="handleSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <!-- 图片预览 -->
    <ElImageViewer
      v-if="previewVisible"
      :url-list="[previewUrl]"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import {
  ElCard, ElButton, ElIcon, ElUpload, ElSelect, ElOption, ElInput,
  ElTag, ElMessage, ElMessageBox, ElImageViewer
} from 'element-plus'
import { Upload, Search, Document, Picture, VideoPlay, Headset, FolderOpened, QuestionFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useTable } from '@/composables/useTable'
import { usePermission } from '@/composables/usePermission'
import ArtTable from '@/components/core/tables/art-table/index.vue'
import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
import {
  fetchFileList, fetchDeleteFile, fetchDeleteFileList, fetchUploadFile,
  fetchFileStatistics, fetchStorageConfig, formatFileSize,
  FileTypeLabels, StorageTypeLabels,
  type FileInfo, type FileStatistics, type StorageConfig
} from '@/api/system/file'

defineOptions({ name: 'FileManagement' })

const { t } = useI18n()
const { hasPermission } = usePermission()

// 搜索状态
const searchText = ref('')
const selectedFileType = ref('')
const selectedStorageType = ref('')
const selectedIds = ref<string[]>([])

// 预览状态
const previewVisible = ref(false)
const previewUrl = ref('')

// 统计数据
const statistics = ref<FileStatistics>({
  total_count: 0,
  total_size: 0,
  type_stats: [],
  storage_stats: []
})

const storageConfig = ref<StorageConfig>({
  storage_type: 'local',
  max_size: 100,
  allowed_extensions: []
})

// 获取文件图标组件
const getFileIconComponent = (fileType: string) => {
  const icons: Record<string, any> = {
    image: Picture,
    document: Document,
    video: VideoPlay,
    audio: Headset,
    archive: FolderOpened,
    other: QuestionFilled
  }
  return icons[fileType] || icons.other
}

// 获取文件类型标签类型
const getFileTypeTagType = (fileType: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const types: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    image: 'success',
    document: 'primary',
    video: 'warning',
    audio: 'info',
    archive: 'danger',
    other: 'info'
  }
  return types[fileType] || 'info'
}

// 获取文件图标颜色
const getFileIconColor = (fileType: string) => {
  const colors: Record<string, string> = {
    image: '#67c23a',
    document: '#409eff',
    video: '#e6a23c',
    audio: '#909399',
    archive: '#f56c6c',
    other: '#909399'
  }
  return colors[fileType] || colors.other
}

// 格式化时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 使用 useTable 管理文件列表
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
} = useTable<typeof fetchFileList>({
  core: {
    apiFn: fetchFileList,
    apiParams: {},
    paginationKey: { current: 'page', size: 'pageSize' },
    columnsFactory: () => [
      { type: 'selection' },
      { type: 'index', width: 80, label: t('table.column.index'), align: 'center' },
      {
        prop: 'name',
        label: t('file.fileName'),
        minWidth: 200,
        showOverflowTooltip: true,
        formatter: (row: FileInfo) => h('div', { class: 'flex items-center gap-2' }, [
          h(ElIcon, { size: 20, style: { color: getFileIconColor(row.file_type) } }, () => h(getFileIconComponent(row.file_type))),
          h('span', row.name)
        ])
      },
      {
        prop: 'file_type',
        label: t('file.fileType'),
        width: 100,
        align: 'center',
        formatter: (row: FileInfo) => h(ElTag, { type: getFileTypeTagType(row.file_type), size: 'small' }, () => FileTypeLabels[row.file_type] || row.file_type)
      },
      {
        prop: 'size',
        label: t('file.fileSize'),
        width: 100,
        align: 'center',
        formatter: (row: FileInfo) => formatFileSize(row.size)
      },
      {
        prop: 'storage_type',
        label: t('file.storageType'),
        width: 120,
        align: 'center',
        formatter: (row: FileInfo) => StorageTypeLabels[row.storage_type] || row.storage_type
      },
      {
        prop: 'uploader_name',
        label: t('file.uploader'),
        width: 100,
        align: 'center',
        formatter: (row: FileInfo) => row.uploader_name || '-'
      },
      {
        prop: 'created_at',
        label: t('common.createdAt'),
        width: 160,
        align: 'center',
        formatter: (row: FileInfo) => formatDateTime(row.created_at)
      },
      {
        prop: 'actions',
        label: t('common.actions'),
        width: 200,
        align: 'center',
        fixed: 'right',
        formatter: (row: FileInfo) => {
          const buttons = []
          buttons.push(h(ElButton, { type: 'primary', size: 'small', onClick: () => handlePreview(row) }, () => t('file.preview')))
          buttons.push(h(ElButton, { type: 'info', size: 'small', onClick: () => handleCopyUrl(row) }, () => t('file.copyUrl')))
          if (hasPermission('file:btn:delete')) {
            buttons.push(h(ElButton, { type: 'danger', size: 'small', onClick: () => handleDelete(row) }, () => t('buttons.delete')))
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

// 加载数据
const loadData = () => {
  Object.assign(searchParams, {
    name: searchText.value || undefined,
    file_type: selectedFileType.value || undefined,
    storage_type: selectedStorageType.value || undefined
  })
  getData()
  loadStatistics()
}

// 加载统计
const loadStatistics = async () => {
  try {
    const response = await fetchFileStatistics()
    if (response?.success && response.data) {
      statistics.value = response.data
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

// 加载存储配置
const loadStorageConfig = async () => {
  try {
    const response = await fetchStorageConfig()
    if (response?.success && response.data) {
      storageConfig.value = response.data
    }
  } catch (error) {
    console.error('加载存储配置失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  ;(searchParams as any).page = 1
  loadData()
}

// 选择变化
const handleSelectionChange = (rows: FileInfo[]) => {
  selectedIds.value = rows.map(r => r.id)
}

// 上传前检查
const handleBeforeUpload = (file: File) => {
  const maxSize = storageConfig.value.max_size * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(t('file.fileTooLarge', { size: storageConfig.value.max_size }))
    return false
  }
  
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (storageConfig.value.allowed_extensions.length > 0 && !storageConfig.value.allowed_extensions.includes(ext)) {
    ElMessage.error(t('file.fileTypeNotAllowed'))
    return false
  }
  
  return true
}

// 上传文件
const handleUpload = async (options: { file: File }) => {
  try {
    const response = await fetchUploadFile(options.file)
    if (response?.success) {
      ElMessage.success(t('file.uploadSuccess'))
      loadData()
    } else {
      ElMessage.error(response?.msg || t('file.uploadFailed'))
    }
  } catch (error) {
    ElMessage.error(t('file.uploadFailed'))
  }
}

// 删除文件
const handleDelete = async (row: FileInfo) => {
  try {
    await ElMessageBox.confirm(
      t('file.confirmDelete', { name: row.name }),
      t('common.deleteConfirm'),
      { type: 'warning' }
    )
    
    const response = await fetchDeleteFile(row.id)
    if (response?.success) {
      ElMessage.success(t('common.deleteSuccess'))
      loadData()
    } else {
      ElMessage.error(response?.msg || t('common.deleteFailed'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.deleteFailed'))
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      t('common.confirmBatchDelete', { count: selectedIds.value.length }),
      t('common.deleteConfirm'),
      { type: 'warning' }
    )
    
    const response = await fetchDeleteFileList(selectedIds.value)
    if (response?.success) {
      ElMessage.success(t('common.deleteSuccess'))
      selectedIds.value = []
      loadData()
    } else {
      ElMessage.error(response?.msg || t('common.deleteFailed'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.deleteFailed'))
    }
  }
}

// 预览
const handlePreview = (row: FileInfo) => {
  if (row.file_type === 'image') {
    previewUrl.value = row.url
    previewVisible.value = true
  } else {
    window.open(row.url, '_blank')
  }
}

// 复制URL
const handleCopyUrl = async (row: FileInfo) => {
  try {
    await navigator.clipboard.writeText(row.url)
    ElMessage.success(t('common.copySuccess'))
  } catch {
    ElMessage.error(t('common.copyFailed'))
  }
}

onMounted(() => {
  loadData()
  loadStorageConfig()
})
</script>

<style lang="scss" scoped>
.stats-area {
  flex-shrink: 0;
  display: flex;
  gap: 40px;
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 16px 24px;
  margin-bottom: 12px;

  .stat-item {
    text-align: center;

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: var(--el-color-primary);
    }

    .stat-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-top: 4px;
    }
  }
}

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
