<template>
  <div class="art-full-height">
    <!-- 搜索区域 -->
    <OperationLogSearch v-model="searchParams" @search="handleSearch" @reset="resetSearchParams" />

    <ElCard class="art-table-card" shadow="never">
      <!-- 表格头部 -->
      <ArtTableHeader :loading="loading" v-model:columns="columnChecks" @refresh="refreshData">
        <template #left>
          <ElButton 
            v-if="selectedRows.length > 0" 
            v-auth="'operation:btn:delete'" 
            type="danger" 
            plain 
            @click="handleBatchDelete"
          >
            <i class="iconfont-sys mr-1">&#xe6e2;</i>
            {{ t('common.batchDelete') }} ({{ selectedRows.length }})
          </ElButton>
        </template>
      </ArtTableHeader>

      <!-- 表格 -->
      <ArtTable
        :data="data"
        :loading="loading"
        :columns="columns"
        :pagination="pagination"
        row-key="id"
        @selection-change="handleSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <!-- 详情对话框 -->
    <OperationLogDetail v-model="detailVisible" :data="currentDetailData" @refresh="refreshData" />
  </div>
</template>

<script setup lang="ts">
  import { ref, h } from 'vue'
  import { ElMessage, ElMessageBox, ElButton, ElCard, ElTag } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { useTable } from '@/composables/useTable'
  import { usePermission } from '@/composables/usePermission'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
  import {
    fetchOperationLogList,
    fetchDeleteOperationLog,
    type OperationLogInfo
  } from '@/api/system/log'
  import OperationLogSearch from './modules/operation-log-search.vue'
  import OperationLogDetail from './modules/operation-log-detail.vue'

  defineOptions({ name: 'OperationLog' })

  const { t } = useI18n()
  const { hasPermission } = usePermission()

  // 详情对话框
  const detailVisible = ref(false)
  const currentDetailData = ref<OperationLogInfo | null>(null)

  // 选中的行
  const selectedRows = ref<OperationLogInfo[]>([])

  const {
    columns,
    columnChecks,
    data,
    loading,
    pagination,
    getData,
    searchParams,
    resetSearchParams,
    handleSizeChange,
    handleCurrentChange,
    refreshData
  } = useTable({
    // 核心配置
    core: {
      apiFn: fetchOperationLogList,
      apiParams: {
        page: 1,
        pageSize: 20
      },
      // 配置分页字段映射
      paginationKey: {
        current: 'page',
        size: 'pageSize'
      },
      columnsFactory: () => [
        { type: 'selection' }, // 勾选列
        { type: 'index', width: 80, label: t('table.column.index'), align: 'center' }, // 序号
        {
          prop: 'operation_name',
          label: t('logManager.operationLog.operationName'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'operation_type',
          label: t('logManager.operationLog.operationType'),
          align: 'center',
          width: 100,
          formatter: (row: OperationLogInfo) => {
            const typeMap: Record<
              string,
              { color: 'success' | 'warning' | 'danger' | 'info' | 'primary' | ''; text: string }
            > = {
              '1': { color: 'success', text: t('logManager.operationLog.typeOptions.insert') },
              '2': { color: 'warning', text: t('logManager.operationLog.typeOptions.update') },
              '3': { color: 'danger', text: t('logManager.operationLog.typeOptions.delete') },
              '4': { color: 'info', text: t('logManager.operationLog.typeOptions.select') },
              '5': { color: 'primary', text: t('logManager.operationLog.typeOptions.export') },
              '6': { color: 'primary', text: t('logManager.operationLog.typeOptions.import') },
              '7': { color: 'warning', text: t('logManager.operationLog.typeOptions.grant') },
              '0': { color: '', text: t('logManager.operationLog.typeOptions.other') }
            }
            const config = typeMap[row.operation_type] || typeMap['0']
            return config.color
              ? h(ElTag, { type: config.color }, () => config.text)
              : h('span', config.text)
          }
        },
        {
          prop: 'operator_name',
          label: t('logManager.operationLog.operator'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'operator_nickname',
          label: t('logManager.operationLog.operatorNickname'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'department_name',
          label: t('logManager.operationLog.department'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'request_method',
          label: t('logManager.operationLog.requestMethod'),
          align: 'center',
          width: 100,
          formatter: (row: OperationLogInfo) => {
            const methodMap: Record<
              string,
              'success' | 'warning' | 'danger' | 'info' | 'primary' | ''
            > = {
              GET: 'info',
              POST: 'success',
              PUT: 'warning',
              DELETE: 'danger',
              PATCH: 'warning'
            }
            const color = methodMap[row.request_method] || ''
            return color
              ? h(ElTag, { type: color }, () => row.request_method)
              : h('span', row.request_method)
          }
        },
        {
          prop: 'request_path',
          label: t('logManager.operationLog.requestPath'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'host',
          label: t('logManager.operationLog.host'),
          align: 'center'
        },
        {
          prop: 'status',
          label: t('logManager.operationLog.status'),
          align: 'center',
          width: 100,
          formatter: (row: OperationLogInfo) => {
            const isSuccess = String(row.status) === '1'
            return h(ElTag, { type: isSuccess ? 'success' : 'danger' }, () =>
              isSuccess ? t('logManager.operationLog.success') : t('logManager.operationLog.failed')
            )
          }
        },
        {
          prop: 'cost_time',
          label: t('logManager.operationLog.costTime'),
          align: 'center',
          width: 100,
          // 格式化下 小于300ms 绿色 大于300ms 黄色 大于1000ms 红色
          formatter: (row: OperationLogInfo) => {
            if (row.cost_time < 300) {
              return h(ElTag, { type: 'success' }, () => `${row.cost_time} ms`)
            } else if (row.cost_time > 300 && row.cost_time < 1000) {
              return h(ElTag, { type: 'warning' }, () => `${row.cost_time} ms`)
            } else {
              return h(ElTag, { type: 'danger' }, () => `${row.cost_time} ms`)
            }
          }
        },
        {
          prop: 'created_at',
          label: t('logManager.operationLog.operationTime'),
          align: 'center',
          formatter: (row: OperationLogInfo) => {
            return new Date(row.created_at).toLocaleString('zh-CN')
          }
        },
        {
          prop: 'actions',
          label: t('common.actions'),
          width: 180,
          align: 'center',
          fixed: 'right',
          formatter: (row: OperationLogInfo) => {
            const buttons = []
            
            // 查看详情按钮
            buttons.push(
              h(
                ElButton,
                {
                  type: 'primary',
                  size: 'small',
                  onClick: () => handleViewDetail(row)
                },
                () => [t('buttons.info')]
              )
            )
            
            // 删除按钮
            if (hasPermission('operation:btn:delete')) {
              buttons.push(
                h(
                  ElButton,
                  {
                    type: 'danger',
                    size: 'small',
                    onClick: () => handleSingleDelete(row)
                  },
                  () => [t('buttons.delete')]
                )
              )
            }
            
            return h('div', { class: 'flex gap-2 justify-center' }, buttons)
          }
        }
      ]
    }
  })

  /**
   * 搜索处理
   * @param params 参数
   */
  const handleSearch = (params: Record<string, any>) => {
    // 搜索参数赋值
    Object.assign(searchParams, params)
    getData()
  }

  /**
   * 处理表格行选择变化
   */
  const handleSelectionChange = (selection: OperationLogInfo[]): void => {
    selectedRows.value = selection
  }

  // 查看详情
  const handleViewDetail = (row: OperationLogInfo) => {
    currentDetailData.value = row
    detailVisible.value = true
  }

  // 单个删除
  const handleSingleDelete = async (row: OperationLogInfo) => {
    try {
      await ElMessageBox.confirm(
        t('logManager.operationLog.deleteConfirm').replace('{operation}', row.operation_name),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      await fetchDeleteOperationLog(row.id)
      refreshData()
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('删除失败:', error)
      }
    }
  }

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRows.value.length === 0) {
      ElMessage.warning(t('common.pleaseSelectData'))
      return
    }

    try {
      await ElMessageBox.confirm(
        t('logManager.operationLog.batchDeleteConfirm').replace(
          '{count}',
          selectedRows.value.length.toString()
        ),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      // 批量删除操作
      for (const row of selectedRows.value) {
        await fetchDeleteOperationLog(row.id)
      }

      selectedRows.value = []
      refreshData()
      ElMessage.success(t('common.deleteSuccess'))
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('批量删除失败:', error)
      }
    }
  }
</script>

<style scoped></style>
