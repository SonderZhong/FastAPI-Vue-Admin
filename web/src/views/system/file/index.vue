<template>
  <div class="file-page art-full-height">
    <ElCard class="file-card" shadow="never">
      <!-- 头部统计 -->
      <div class="file-stats">
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

      <!-- 操作栏 -->
      <div class="file-toolbar">
        <div class="toolbar-left">
          <ElUpload
            v-auth="'file:btn:upload'"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :http-request="handleUpload"
            multiple
          >
            <ElButton type="primary" v-ripple>
              <ElIcon><Upload /></ElIcon>
              {{ t('file.upload') }}
            </ElButton>
          </ElUpload>
          <ElButton
            v-auth="'file:btn:delete'"
            type="danger"
            plain
            :disabled="selectedIds.length === 0"
            @click="handleBatchDelete"
            v-ripple
          >
            <ElIcon><Delete /></ElIcon>
            {{ t('buttons.batchDelete') }}
          </ElButton>
          <ElButton @click="loadData" v-ripple>
            <ElIcon><Refresh /></ElIcon>
            {{ t('buttons.refresh') }}
          </ElButton>
        </div>
        <div class="toolbar-right">
          <ElSelect v-model="searchParams.file_type" :placeholder="t('file.fileType')" clearable style="width: 120px" @change="handleSearch">
            <ElOption v-for="(label, key) in FileTypeLabels" :key="key" :label="label" :value="key" />
          </ElSelect>
          <ElSelect v-model="searchParams.storage_type" :placeholder="t('file.storageType')" clearable style="width: 140px" @change="handleSearch">
            <ElOption v-for="(label, key) in StorageTypeLabels" :key="key" :label="label" :value="key" />
          </ElSelect>
          <ElInput
            v-model="searchParams.name"
            :placeholder="t('file.searchPlaceholder')"
            clearable
            style="width: 200px"
            @input="handleSearch"
          >
            <template #prefix>
              <ElIcon><Search /></ElIcon>
            </template>
          </ElInput>
        </div>
      </div>

      <!-- 文件列表 -->
      <div class="file-list">
        <ElTable
          :data="fileList"
          v-loading="loading"
          @selection-change="handleSelectionChange"
          style="width: 100%"
        >
          <ElTableColumn type="selection" width="50" />
          <ElTableColumn :label="t('file.fileName')" min-width="200">
            <template #default="{ row }">
              <div class="file-name-cell">
                <ElIcon class="file-icon" :class="getFileIcon(row.file_type)">
                  <component :is="getFileIconComponent(row.file_type)" />
                </ElIcon>
                <span class="file-name" :title="row.name">{{ row.name }}</span>
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('file.fileType')" width="100">
            <template #default="{ row }">
              <ElTag size="small" :type="getFileTypeTagType(row.file_type)">
                {{ FileTypeLabels[row.file_type] || row.file_type }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('file.fileSize')" width="100">
            <template #default="{ row }">
              {{ formatFileSize(row.size) }}
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('file.storageType')" width="120">
            <template #default="{ row }">
              {{ StorageTypeLabels[row.storage_type] || row.storage_type }}
            </template>
          </ElTableColumn>
          <ElTableColumn prop="uploader_name" :label="t('file.uploader')" width="100" />
          <ElTableColumn :label="t('common.createdAt')" width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('common.actions')" width="180" fixed="right">
            <template #default="{ row }">
              <ElButton type="primary" link size="small" @click="handlePreview(row)">
                {{ t('file.preview') }}
              </ElButton>
              <ElButton type="primary" link size="small" @click="handleCopyUrl(row)">
                {{ t('file.copyUrl') }}
              </ElButton>
              <ElButton v-auth="'file:btn:delete'" type="danger" link size="small" @click="handleDelete(row)">
                {{ t('buttons.delete') }}
              </ElButton>
            </template>
          </ElTableColumn>
        </ElTable>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <ElPagination
            v-model:current-page="searchParams.page"
            v-model:page-size="searchParams.pageSize"
            :total="total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadData"
            @current-change="loadData"
          />
        </div>
      </div>
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
import {
  ElCard, ElButton, ElIcon, ElUpload, ElSelect, ElOption, ElInput,
  ElTable, ElTableColumn, ElTag, ElPagination, ElMessage, ElMessageBox,
  ElImageViewer
} from 'element-plus'
import { Upload, Delete, Refresh, Search, Document, Picture, VideoPlay, Headset, FolderOpened, QuestionFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import {
  fetchFileList, fetchDeleteFile, fetchDeleteFileList, fetchUploadFile,
  fetchFileStatistics, fetchStorageConfig, formatFileSize,
  FileTypeLabels, StorageTypeLabels,
  type FileInfo, type FileStatistics, type StorageConfig
} from '@/api/system/file'

defineOptions({ name: 'FileManagement' })

const { t } = useI18n()

// 状态
const loading = ref(false)
const fileList = ref<FileInfo[]>([])
const total = ref(0)
const selectedIds = ref<string[]>([])
const previewVisible = ref(false)
const previewUrl = ref('')

const searchParams = reactive({
  page: 1,
  pageSize: 20,
  name: '',
  file_type: '',
  storage_type: ''
})

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

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    const response = await fetchFileList(searchParams)
    if (response?.success && response.data) {
      fileList.value = response.data.result
      total.value = response.data.total
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
  } finally {
    loading.value = false
  }
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
  searchParams.page = 1
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
      loadStatistics()
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
      loadStatistics()
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
      loadStatistics()
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

// 获取文件图标类名
const getFileIcon = (fileType: string) => {
  const icons: Record<string, string> = {
    image: 'icon-image',
    document: 'icon-document',
    video: 'icon-video',
    audio: 'icon-audio',
    archive: 'icon-archive',
    other: 'icon-other'
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

// 格式化时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadData()
  loadStatistics()
  loadStorageConfig()
})
</script>

<style lang="scss" scoped>
.file-page {
  .file-card {
    height: 100%;
    
    :deep(.el-card__body) {
      height: calc(100% - 20px);
      display: flex;
      flex-direction: column;
    }
  }

  .file-stats {
    display: flex;
    gap: 40px;
    padding: 16px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
    margin-bottom: 16px;

    .stat-item {
      text-align: center;

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: rgb(var(--art-primary));
      }

      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
      }
    }
  }

  .file-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .toolbar-left {
      display: flex;
      gap: 10px;
    }

    .toolbar-right {
      display: flex;
      gap: 10px;
    }
  }

  .file-list {
    flex: 1;
    overflow: auto;

    .file-name-cell {
      display: flex;
      align-items: center;
      gap: 8px;

      .file-icon {
        font-size: 20px;
        flex-shrink: 0;

        &.icon-image { color: #67c23a; }
        &.icon-document { color: #409eff; }
        &.icon-video { color: #e6a23c; }
        &.icon-audio { color: #909399; }
        &.icon-archive { color: #f56c6c; }
        &.icon-other { color: #909399; }
      }

      .file-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    padding-top: 16px;
  }
}
</style>
