<template>
  <div class="art-full-height">
    <!-- 搜索区域 -->
    <LoginLogSearch v-model="searchParams" @search="handleSearch" @reset="resetSearchParams" />

    <ElCard class="art-table-card" shadow="never">
      <!-- 表格头部 -->
      <ArtTableHeader :loading="loading" v-model:columns="columnChecks" @refresh="refreshData">
        <template #left>
          <ElButton 
            v-if="onlineSelectedCount > 0" 
            v-auth="'login:btn:logout'" 
            type="danger" 
            @click="handleBatchLogout"
          >
            <i class="iconfont-sys mr-1">&#xe6dc;</i>
            {{ t('logManager.loginLog.batchForceLogout') }} ({{ onlineSelectedCount }})
          </ElButton>
          <ElButton 
            v-if="selectedRows.length > 0" 
            v-auth="'login:btn:delete'" 
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
        row-key="session_id"
        @selection-change="handleSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <!-- 详情对话框 -->
    <LoginLogDetail v-model="detailVisible" :data="currentDetailData" @refresh="refreshData" />
  </div>
</template>

<script setup lang="ts">
  import { ref, h, computed } from 'vue'
  import { ElMessage, ElMessageBox, ElButton, ElCard, ElTag } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { useTable } from '@/composables/useTable'
  import { usePermission } from '@/composables/usePermission'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
  import {
    fetchLoginLogList,
    fetchLogoutUser,
    fetchLogoutUserList,
    fetchDeleteLoginLog,
    fetchDeleteLoginLogList,
    type LoginLogInfo
  } from '@/api/system/log'
  import LoginLogSearch from './modules/login-log-search.vue'
  import LoginLogDetail from './modules/login-log-detail.vue'

  const { t } = useI18n()
  const { hasPermission } = usePermission()

  // 详情对话框
  const detailVisible = ref(false)
  const currentDetailData = ref<LoginLogInfo | null>(null)

  // 选中的行
  const selectedRows = ref<LoginLogInfo[]>([])

  // 计算在线用户数量
  const onlineSelectedCount = computed(() => {
    return selectedRows.value.filter((row) => row.online === true).length
  })

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
      apiFn: fetchLoginLogList,
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
          prop: 'username',
          label: t('logManager.loginLog.username'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'user_nickname',
          label: t('logManager.loginLog.nickname'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'department_name',
          label: t('logManager.loginLog.department'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'login_ip',
          label: t('logManager.loginLog.loginIp'),
          align: 'center'
        },
        {
          prop: 'login_location',
          label: t('logManager.loginLog.loginLocation'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'browser',
          label: t('logManager.loginLog.browser'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'os',
          label: t('logManager.loginLog.os'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'status',
          label: t('logManager.loginLog.status'),
          align: 'center',
          formatter: (row: LoginLogInfo) => {
            const isSuccess = String(row.status) === '1'
            return h(ElTag, { type: isSuccess ? 'success' : 'danger' }, () =>
              isSuccess ? t('logManager.loginLog.success') : t('logManager.loginLog.failed')
            )
          }
        },
        {
          prop: 'created_at',
          label: t('logManager.loginLog.loginTime'),
          align: 'center',
          formatter: (row: LoginLogInfo) => {
            return new Date(row.created_at).toLocaleString('zh-CN')
          }
        },
        {
          prop: 'actions',
          label: t('common.actions'),
          width: 300,
          align: 'center',
          fixed: 'right',
          formatter: (row: LoginLogInfo) => {
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
            
            // 强制登出按钮
            if (hasPermission('login:btn:logout')) {
              buttons.push(
                h(
                  ElButton,
                  {
                    type: 'warning',
                    size: 'small',
                    disabled: !row.online,
                    onClick: () => handleSingleLogout(row)
                  },
                  () => [t('logManager.loginLog.forceLogout')]
                )
              )
            }
            
            // 删除按钮
            if (hasPermission('login:btn:delete')) {
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
  const handleSelectionChange = (selection: LoginLogInfo[]): void => {
    selectedRows.value = selection
  }

  // 查看详情
  const handleViewDetail = (row: LoginLogInfo) => {
    currentDetailData.value = row
    detailVisible.value = true
  }

  // 单个强制注销
  const handleSingleLogout = async (row: LoginLogInfo) => {
    try {
      await ElMessageBox.confirm(
        t('logManager.loginLog.logoutConfirm').replace('{username}', row.username),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      await fetchLogoutUser(row.session_id)
      refreshData()
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('强制注销失败:', error)
      }
    }
  }

  // 单个删除
  const handleSingleDelete = async (row: LoginLogInfo) => {
    try {
      await ElMessageBox.confirm(
        t('logManager.loginLog.deleteConfirm').replace('{username}', row.username),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      await fetchDeleteLoginLog(row.id)
      refreshData()
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('删除失败:', error)
      }
    }
  }

  // 批量强制注销
  const handleBatchLogout = async () => {
    if (selectedRows.value.length === 0) {
      ElMessage.warning(t('common.pleaseSelectData'))
      return
    }

    const onlineUsers = selectedRows.value.filter((row) => row.online === true)
    if (onlineUsers.length === 0) {
      ElMessage.warning(t('logManager.loginLog.noOnlineUsers'))
      return
    }

    try {
      await ElMessageBox.confirm(
        t('logManager.loginLog.batchLogoutConfirm').replace('  ', onlineUsers.length.toString()),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      await fetchLogoutUserList({
        ids: onlineUsers.map((row) => row.session_id)
      })
      selectedRows.value = []
      refreshData()
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('批量强制注销失败:', error)
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
        t('logManager.loginLog.batchDeleteConfirm').replace(
          '  ',
          selectedRows.value.length.toString()
        ),
        t('common.warning'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      await fetchDeleteLoginLogList({
        ids: selectedRows.value.map((row) => row.id)
      })
      selectedRows.value = []
      refreshData()
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('批量删除失败:', error)
      }
    }
  }

  // 页面标题
  defineOptions({
    name: 'LoginLog'
  })
</script>

<style scoped></style>
