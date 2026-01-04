<template>
  <div class="page-content my-notification-page">
    <div class="content">
      <!-- 左侧用户信息卡片 -->
      <div class="left-wrap">
        <div class="user-wrap box-style">
          <div class="profile-header">
            <img class="bg" src="@imgs/user/bg.webp" />
            <div class="avatar-section">
              <ElAvatar :size="60" :src="getAvatarUrl(userInfo?.avatar)">
                {{ userInfo?.username }}
              </ElAvatar>
              <div class="status-indicator"></div>
            </div>
          </div>

          <div class="profile-info">
            <h2 class="name">{{ userInfo?.nickname || userInfo?.username }}</h2>
            <p class="position">{{ userInfo?.department_name || '暂无部门' }}</p>

            <div class="quick-stats">
              <div class="stat-item">
                <span class="stat-number">{{ pagination.total }}</span>
                <span class="stat-label">全部通知</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ unreadCount }}</span>
                <span class="stat-label">未读通知</span>
              </div>
            </div>
          </div>

          <div class="outer-info">
            <div class="info-item">
              <i class="iconfont-sys">&#xe72e;</i>
              <span>{{ userInfo?.email || '暂无邮箱' }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe6f5;</i>
              <span>{{ userInfo?.phone || '暂无手机' }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe811;</i>
              <span>{{ userInfo?.department_name || '暂无部门' }}</span>
            </div>
          </div>
        </div>

        <!-- 快捷导航卡片 -->
        <div class="quick-nav box-style">
          <div class="nav-header">
            <h3>快捷导航</h3>
          </div>
          <div class="nav-items">
            <div class="nav-item" @click="goToUserCenter">
              <div class="nav-icon user-icon">
                <i class="iconfont-sys">&#xe7ae;</i>
              </div>
              <div class="nav-content">
                <h4>个人中心</h4>
                <p>管理个人信息</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
            <div class="nav-item" @click="goToLoginRecord">
              <div class="nav-icon login-icon">
                <i class="iconfont-sys">&#xe6ce;</i>
              </div>
              <div class="nav-content">
                <h4>登录记录</h4>
                <p>查看登录历史</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
            <div class="nav-item" @click="goToOperationRecord">
              <div class="nav-icon operation-icon">
                <i class="iconfont-sys">&#xe694;</i>
              </div>
              <div class="nav-content">
                <h4>操作记录</h4>
                <p>查看操作日志</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧通知列表 -->
      <div class="right-wrap">
        <div class="notification-records box-style">
          <div class="section-header">
            <div class="header-title">
              <div class="title-icon">
                <i class="iconfont-sys">&#xe6c2;</i>
              </div>
              <h3>我的通知</h3>
            </div>
            <div class="header-actions">
              <ElButton @click="handleMarkAllRead" :disabled="unreadCount === 0" size="small" type="success" plain round>
                <i class="iconfont-sys mr-1">&#xe621;</i>
                全部已读
              </ElButton>
              <ElButton @click="loadData" :loading="loading" size="small" type="primary" plain round>
                <i class="iconfont-sys mr-1">&#xe6cf;</i>
                刷新
              </ElButton>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <ElForm :model="searchForm" inline>
              <ElFormItem label="阅读状态">
                <ElSelect v-model="searchForm.is_read" placeholder="全部" clearable style="width: 120px" @change="handleSearch">
                  <ElOption label="未读" :value="false" />
                  <ElOption label="已读" :value="true" />
                </ElSelect>
              </ElFormItem>
              <ElFormItem label="通知类型">
                <ElSelect v-model="searchForm.type" placeholder="全部" clearable style="width: 120px" @change="handleSearch">
                  <ElOption label="登录通知" :value="0" />
                  <ElOption label="全局公告" :value="1" />
                  <ElOption label="系统消息" :value="2" />
                </ElSelect>
              </ElFormItem>
              <ElFormItem>
                <ElButton type="primary" @click="handleSearch" round>搜索</ElButton>
                <ElButton @click="handleReset" round>重置</ElButton>
              </ElFormItem>
            </ElForm>
          </div>

          <!-- 通知列表 -->
          <ArtTable
            :data="tableData"
            :loading="loading"
            :pagination="{ current: pagination.page, size: pagination.pageSize, total: pagination.total }"
            @pagination:current-change="handlePageChange"
            @pagination:size-change="handleSizeChange"
          >
            <ElTableColumn type="index" label="#" width="50" />
            <ElTableColumn label="标题" min-width="200">
              <template #default="{ row }">
                <div class="title-cell" @click="handleView(row)">
                  <span class="title" :class="{ 'is-read': row.is_read }">{{ row.title }}</span>
                  <ElTag v-if="!row.is_read" type="danger" size="small" class="unread-tag">未读</ElTag>
                </div>
              </template>
            </ElTableColumn>
            <ElTableColumn label="类型" width="100">
              <template #default="{ row }">
                <ElTag :type="getTypeTagType(row.notification_type)" size="small">
                  {{ getTypeName(row.notification_type) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn label="优先级" width="80">
              <template #default="{ row }">
                <ElTag :type="getPriorityTagType(row.priority)" size="small">
                  {{ getPriorityName(row.priority) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn label="发送者" width="100">
              <template #default="{ row }">
                {{ row.creator_name || '系统' }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="发布时间" width="170">
              <template #default="{ row }">
                {{ formatDate(row.publish_time) }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <ElButton link type="primary" @click="handleView(row)">查看</ElButton>
                <ElButton v-if="!row.is_read" link type="success" @click="handleMarkRead(row)">标记已读</ElButton>
              </template>
            </ElTableColumn>
          </ArtTable>
        </div>
      </div>
    </div>

    <!-- 通知详情弹窗 -->
    <ElDialog v-model="detailVisible" title="通知详情" width="600px" class="notification-dialog">
      <div v-if="currentNotification" class="notification-detail">
        <div class="detail-header">
          <h3>{{ currentNotification.title }}</h3>
          <div class="meta">
            <ElTag :type="getTypeTagType(currentNotification.notification_type)" size="small">
              {{ getTypeName(currentNotification.notification_type) }}
            </ElTag>
            <ElTag :type="getPriorityTagType(currentNotification.priority)" size="small">
              {{ getPriorityName(currentNotification.priority) }}
            </ElTag>
            <span class="time">{{ formatDate(currentNotification.publish_time) }}</span>
          </div>
        </div>
        <ElDivider />
        <div class="detail-content" v-html="currentNotification.content"></div>
        <div class="detail-footer">
          <span>发送者：{{ currentNotification.creator_name || '系统' }}</span>
        </div>
      </div>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { getAvatarUrl } from '@/utils'
import ArtTable from '@/components/core/tables/art-table/index.vue'
import {
  fetchMyNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  fetchUnreadCount,
  type UserNotificationInfo
} from '@/api/system/notification'

defineOptions({ name: 'MyNotification' })

const router = useRouter()
const userStore = useUserStore()

const userInfo = computed(() => userStore.getUserInfo)

const loading = ref(false)
const tableData = ref<UserNotificationInfo[]>([])
const detailVisible = ref(false)
const currentNotification = ref<UserNotificationInfo | null>(null)
const unreadCount = ref(0)

const searchForm = reactive({
  is_read: undefined as boolean | undefined,
  type: undefined as number | undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getTypeName = (type: number) => {
  const names = ['登录通知', '全局公告', '系统消息']
  return names[type] || '未知'
}

const getTypeTagType = (type: number): 'info' | 'warning' | 'success' => {
  const map: Record<number, 'info' | 'warning' | 'success'> = { 0: 'info', 1: 'warning', 2: 'success' }
  return map[type] || 'info'
}

const getPriorityName = (priority: number) => {
  const names = ['普通', '重要', '紧急']
  return names[priority] || '普通'
}

const getPriorityTagType = (priority: number): 'info' | 'warning' | 'danger' => {
  const map: Record<number, 'info' | 'warning' | 'danger'> = { 0: 'info', 1: 'warning', 2: 'danger' }
  return map[priority] || 'info'
}

const loadData = async () => {
  try {
    loading.value = true
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize
    }
    if (searchForm.is_read !== undefined) {
      params.is_read = searchForm.is_read
    }
    if (searchForm.type !== undefined) {
      params.type = searchForm.type
    }
    
    const res = await fetchMyNotifications(params)
    if (res.success && res.data) {
      tableData.value = res.data.result || []
      pagination.total = res.data.total || 0
    }
    
    // 加载未读数量
    const countRes = await fetchUnreadCount()
    if (countRes.success && countRes.data) {
      unreadCount.value = countRes.data.count
    }
  } catch (e) {
    console.error('加载通知失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.is_read = undefined
  searchForm.type = undefined
  pagination.page = 1
  loadData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadData()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadData()
}

const handleView = async (row: UserNotificationInfo) => {
  currentNotification.value = row
  detailVisible.value = true
  
  if (!row.is_read) {
    await handleMarkRead(row, false)
  }
}

const handleMarkRead = async (row: UserNotificationInfo, showMessage = true) => {
  try {
    const res = await markNotificationRead(row.id)
    if (res.success) {
      row.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      if (showMessage) {
        ElMessage.success('已标记为已读')
      }
    }
  } catch (e) {
    console.error('标记已读失败:', e)
  }
}

const handleMarkAllRead = async () => {
  try {
    const res = await markAllNotificationsRead()
    if (res.success) {
      tableData.value.forEach(item => item.is_read = true)
      unreadCount.value = 0
      ElMessage.success('已全部标记为已读')
    }
  } catch (e) {
    console.error('标记全部已读失败:', e)
  }
}

// 快捷导航
const goToUserCenter = () => {
  router.push('/user-center')
}

const goToLoginRecord = () => {
  router.push('/personal-login-record')
}

const goToOperationRecord = () => {
  router.push('/personal-operation-record')
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.my-notification-page {
  .content {
    display: flex;
    gap: 20px;
    height: 100%;

    .left-wrap {
      width: 300px;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 20px;

      .user-wrap {
        padding: 0;
        border-radius: 12px;
        overflow: hidden;
        background: var(--el-bg-color);

        .profile-header {
          position: relative;
          height: 120px;

          .bg {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }

          .avatar-section {
            position: absolute;
            bottom: -30px;
            left: 50%;
            transform: translateX(-50%);

            :deep(.el-avatar) {
              border: 3px solid white;
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .status-indicator {
              position: absolute;
              bottom: 5px;
              right: 5px;
              width: 12px;
              height: 12px;
              background: var(--el-color-success);
              border: 2px solid white;
              border-radius: 50%;
            }
          }
        }

        .profile-info {
          padding: 40px 20px 20px;
          text-align: center;

          .name {
            margin: 0 0 5px;
            font-size: 18px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }

          .position {
            margin: 0 0 20px;
            color: var(--el-text-color-regular);
            font-size: 14px;
          }

          .quick-stats {
            display: flex;
            justify-content: space-around;
            padding: 15px 0;
            border-top: 1px solid var(--el-border-color-light);

            .stat-item {
              text-align: center;

              .stat-number {
                display: block;
                font-size: 20px;
                font-weight: 600;
                color: var(--el-color-primary);
                margin-bottom: 5px;
              }

              .stat-label {
                font-size: 12px;
                color: var(--el-text-color-regular);
              }
            }
          }
        }

        .outer-info {
          padding: 0 20px 20px;

          .info-item {
            display: flex;
            align-items: center;
            padding: 8px 0;
            color: var(--el-text-color-regular);

            i {
              margin-right: 10px;
              color: var(--el-color-primary);
              font-size: 16px;
            }

            span {
              font-size: 14px;
            }
          }
        }
      }

      .quick-nav {
        background: var(--el-bg-color);
        border-radius: 12px;
        padding: 20px;

        .nav-header {
          margin-bottom: 16px;

          h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }
        }

        .nav-items {
          display: flex;
          flex-direction: column;
          gap: 12px;

          .nav-item {
            display: flex;
            align-items: center;
            padding: 16px;
            background: var(--el-fill-color-light);
            border: 1px solid var(--el-border-color);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;

            &:hover {
              border-color: var(--el-color-primary-light-5);
              background: var(--el-color-primary-light-9);
              transform: translateX(4px);
            }

            .nav-icon {
              width: 40px;
              height: 40px;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 10px;
              margin-right: 12px;

              i {
                font-size: 18px;
                color: #fff;
              }

              &.user-icon {
                background: var(--el-color-primary);
              }

              &.login-icon {
                background: var(--el-color-success);
              }

              &.operation-icon {
                background: var(--el-color-warning);
              }

              &.notification-icon {
                background: var(--el-color-info);
              }
            }

            .nav-content {
              flex: 1;

              h4 {
                margin: 0 0 4px;
                font-size: 14px;
                font-weight: 600;
                color: var(--el-text-color-primary);
              }

              p {
                margin: 0;
                font-size: 12px;
                color: var(--el-text-color-regular);
              }
            }

            .arrow {
              font-size: 14px;
              color: var(--el-text-color-secondary);
              transition: transform 0.3s ease;
            }

            &:hover .arrow {
              transform: translateX(4px);
              color: var(--el-color-primary);
            }
          }
        }
      }
    }

    .right-wrap {
      flex: 1;

      .notification-records {
        padding: 20px;
        border-radius: 12px;
        background: var(--el-bg-color);

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--el-border-color-light);

          .header-title {
            display: flex;
            align-items: center;
            gap: 12px;

            .title-icon {
              width: 36px;
              height: 36px;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 8px;
              background: var(--el-color-primary);

              i {
                font-size: 18px;
                color: #fff;
              }
            }

            h3 {
              margin: 0;
              font-size: 18px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }
          }

          .header-actions {
            display: flex;
            gap: 8px;
          }
        }

        .search-bar {
          margin-bottom: 20px;
          padding: 15px;
          background: var(--el-fill-color-light);
          border-radius: 8px;

          :deep(.el-form-item) {
            margin-bottom: 0;
            margin-right: 16px;
          }
        }
      }
    }
  }
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  
  .title {
    color: var(--el-text-color-primary);
    
    &:hover {
      color: var(--el-color-primary);
    }
    
    &.is-read {
      color: var(--el-text-color-secondary);
    }
  }
  
  .unread-tag {
    flex-shrink: 0;
  }
}

.notification-dialog {
  :deep(.el-dialog__body) {
    padding-top: 10px;
  }
}

.notification-detail {
  .detail-header {
    h3 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 12px;
    }
    
    .meta {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .time {
        color: var(--el-text-color-secondary);
        font-size: 13px;
      }
    }
  }
  
  .detail-content {
    line-height: 1.8;
    min-height: 100px;
    
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
  
  .detail-footer {
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .my-notification-page .content {
    flex-direction: column;

    .left-wrap {
      width: 100%;
    }
  }
}
</style>
