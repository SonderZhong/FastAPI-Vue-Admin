<!-- 通知组件 -->
<template>
  <div
    class="notice"
    v-show="visible"
    :style="{
      transform: show ? 'scaleY(1)' : 'scaleY(0.9)',
      opacity: show ? 1 : 0
    }"
    @click.stop=""
  >
    <div class="header">
      <span class="text">{{ $t('notice.title') }}</span>
      <span class="btn" @click="handleMarkAllRead">{{ $t('notice.btnRead') }}</span>
    </div>

    <ul class="bar">
      <li
        v-for="(item, index) in barList"
        :key="index"
        :class="{ active: barActiveIndex === index }"
        @click="changeBar(index)"
      >
        {{ item.name }} ({{ item.num }})
      </li>
    </ul>

    <div class="content">
      <div class="scroll" v-loading="loading">
        <!-- 通知列表 -->
        <ul class="notice-list" v-show="barActiveIndex === 0">
          <li v-for="item in notificationList" :key="item.id" @click="handleNotificationClick(item)">
            <div
              class="icon"
              :style="{ background: getNoticeStyle(item.notification_type).backgroundColor + '!important' }"
            >
              <i
                class="iconfont-sys"
                :style="{ color: getNoticeStyle(item.notification_type).iconColor + '!important' }"
                v-html="getNoticeStyle(item.notification_type).icon"
              ></i>
            </div>
            <div class="text">
              <h4 :class="{ 'is-read': item.is_read }">{{ item.title }}</h4>
              <p>{{ formatTime(item.publish_time) }}</p>
            </div>
            <div v-if="!item.is_read" class="unread-dot"></div>
          </li>
        </ul>

        <!-- 公告列表 -->
        <ul class="notice-list" v-show="barActiveIndex === 1">
          <li v-for="item in announcementList" :key="item.id" @click="handleNotificationClick(item)">
            <div
              class="icon"
              :style="{ background: 'rgb(var(--art-warning))' }"
            >
              <i class="iconfont-sys" style="color: #fff">&#xe6c2;</i>
            </div>
            <div class="text">
              <h4 :class="{ 'is-read': item.is_read }">{{ item.title }}</h4>
              <p>{{ formatTime(item.publish_time) }}</p>
            </div>
            <div v-if="!item.is_read" class="unread-dot"></div>
          </li>
        </ul>

        <!-- 消息列表 -->
        <ul class="notice-list" v-show="barActiveIndex === 2">
          <li v-for="item in messageList" :key="item.id" @click="handleNotificationClick(item)">
            <div
              class="icon"
              :style="{ background: 'rgb(var(--art-success))' }"
            >
              <i class="iconfont-sys" style="color: #fff">&#xe747;</i>
            </div>
            <div class="text">
              <h4 :class="{ 'is-read': item.is_read }">{{ item.title }}</h4>
              <p>{{ formatTime(item.publish_time) }}</p>
            </div>
            <div v-if="!item.is_read" class="unread-dot"></div>
          </li>
        </ul>

        <!-- 空状态 -->
        <div class="empty-tips" v-show="currentTabIsEmpty && !loading">
          <i class="iconfont-sys">&#xe8d7;</i>
          <p>{{ $t('notice.text[0]') }}{{ barList[barActiveIndex].name }}</p>
        </div>
      </div>

      <div class="btn-wrapper">
        <ElButton class="view-all" @click="handleViewAll" v-ripple>
          {{ $t('notice.viewAll') }}
        </ElButton>
      </div>
    </div>

    <div style="height: 100px"></div>
  </div>

  <!-- 通知详情弹窗 -->
  <ElDialog v-model="detailVisible" title="通知详情" width="500px">
    <div v-if="currentNotification" class="notification-detail">
      <h3>{{ currentNotification.title }}</h3>
      <div class="meta">
        <span>{{ currentNotification.creator_name || '系统' }}</span>
        <span>{{ formatTime(currentNotification.publish_time) }}</span>
      </div>
      <div class="content-text" v-html="currentNotification.content"></div>
    </div>
  </ElDialog>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import {
  fetchMyNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  fetchUnreadCount,
  NotificationType,
  type UserNotificationInfo
} from '@/api/system/notification'
import { notificationWs, type NotificationMessage } from '@/utils/websocket'

defineOptions({ name: 'ArtNotification' })

interface NoticeStyle {
  icon: string
  iconColor: string
  backgroundColor: string
}

const { t } = useI18n()
const router = useRouter()

const props = defineProps<{
  value: boolean
}>()

const emit = defineEmits<{
  'update:unreadCount': [count: number]
}>()

const show = ref(false)
const visible = ref(false)
const barActiveIndex = ref(0)
const loading = ref(false)
const detailVisible = ref(false)
const currentNotification = ref<UserNotificationInfo | null>(null)

// 通知数据
const notificationList = ref<UserNotificationInfo[]>([])
const announcementList = ref<UserNotificationInfo[]>([])
const messageList = ref<UserNotificationInfo[]>([])
const unreadCount = ref(0)

// 标签栏数据
const barList = computed(() => [
  { name: t('notice.bar[0]'), num: notificationList.value.filter(n => !n.is_read).length },
  { name: t('notice.bar[1]'), num: announcementList.value.filter(n => !n.is_read).length },
  { name: t('notice.bar[2]'), num: messageList.value.filter(n => !n.is_read).length }
])

// 检查当前标签页是否为空
const currentTabIsEmpty = computed(() => {
  const tabDataMap = [notificationList.value, announcementList.value, messageList.value]
  return tabDataMap[barActiveIndex.value]?.length === 0
})

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 获取通知样式
const getNoticeStyle = (type: number): NoticeStyle => {
  const styleMap: Record<number, NoticeStyle> = {
    [NotificationType.LOGIN]: {
      icon: '&#xe6ce;',
      iconColor: '#fff',
      backgroundColor: 'rgb(var(--art-info))'
    },
    [NotificationType.ANNOUNCEMENT]: {
      icon: '&#xe6c2;',
      iconColor: '#fff',
      backgroundColor: 'rgb(var(--art-warning))'
    },
    [NotificationType.MESSAGE]: {
      icon: '&#xe747;',
      iconColor: '#fff',
      backgroundColor: 'rgb(var(--art-success))'
    }
  }
  return styleMap[type] || styleMap[NotificationType.MESSAGE]
}

// 加载通知数据
const loadNotifications = async () => {
  try {
    loading.value = true
    
    // 按类型加载通知：登录通知、公告、系统消息
    const [loginRes, announcementRes, messageRes] = await Promise.all([
      fetchMyNotifications({ pageSize: 10, type: NotificationType.LOGIN }),
      fetchMyNotifications({ pageSize: 10, type: NotificationType.ANNOUNCEMENT }),
      fetchMyNotifications({ pageSize: 10, type: NotificationType.MESSAGE })
    ])
    
    if (loginRes.success && loginRes.data) {
      notificationList.value = loginRes.data.result || []
    }
    if (announcementRes.success && announcementRes.data) {
      announcementList.value = announcementRes.data.result || []
    }
    if (messageRes.success && messageRes.data) {
      messageList.value = messageRes.data.result || []
    }
    
    // 更新未读数量
    await loadUnreadCount()
  } catch (e) {
    console.error('加载通知失败:', e)
  } finally {
    loading.value = false
  }
}

// 加载未读数量
const loadUnreadCount = async () => {
  try {
    const res = await fetchUnreadCount()
    if (res.success && res.data) {
      unreadCount.value = res.data.count
      emit('update:unreadCount', unreadCount.value)
    }
  } catch (e) {
    console.error('获取未读数量失败:', e)
  }
}

// 点击通知
const handleNotificationClick = async (item: UserNotificationInfo) => {
  currentNotification.value = item
  detailVisible.value = true
  
  if (!item.is_read) {
    try {
      await markNotificationRead(item.id)
      item.is_read = true
      await loadUnreadCount()
    } catch (e) {
      console.error('标记已读失败:', e)
    }
  }
}

// 全部标记已读
const handleMarkAllRead = async () => {
  try {
    const res = await markAllNotificationsRead()
    if (res.success) {
      ElMessage.success('已全部标记为已读')
      notificationList.value.forEach(n => n.is_read = true)
      announcementList.value.forEach(n => n.is_read = true)
      messageList.value.forEach(n => n.is_read = true)
      await loadUnreadCount()
    }
  } catch (e) {
    console.error('标记全部已读失败:', e)
  }
}

// 切换标签
const changeBar = (index: number) => {
  barActiveIndex.value = index
}

// 查看全部
const handleViewAll = () => {
  router.push('/my-notification')
}

// 动画控制
const showNotice = (open: boolean) => {
  if (open) {
    visible.value = open
    loadNotifications()
    setTimeout(() => {
      show.value = open
    }, 5)
  } else {
    show.value = open
    setTimeout(() => {
      visible.value = open
    }, 350)
  }
}

// 监听属性变化
watch(() => props.value, (newValue) => {
  showNotice(newValue)
})

// 初始化加载未读数量
onMounted(() => {
  loadUnreadCount()
  
  // 连接 WebSocket
  notificationWs.connect()
  notificationWs.addHandler(handleWsMessage)
})

// 组件卸载时移除处理器
onUnmounted(() => {
  notificationWs.removeHandler(handleWsMessage)
})

// 处理 WebSocket 消息
const handleWsMessage = (message: NotificationMessage) => {
  switch (message.type) {
    case 'notification':
    case 'login_notification':
      // 收到新通知，刷新列表和未读数
      loadNotifications()
      // 显示桌面通知 - 去除 HTML 标签
      const plainText = message.data.content?.replace(/<[^>]*>/g, '').substring(0, 100) || ''
      ElNotification({
        title: message.data.title || '新通知',
        message: plainText,
        type: 'info',
        duration: 5000
      })
      break
    case 'unread_count':
      // 更新未读数量
      unreadCount.value = message.data.count
      emit('update:unreadCount', message.data.count)
      break
    case 'connected':
      console.log('[通知] WebSocket 连接成功')
      break
  }
}

// 暴露方法供外部调用
defineExpose({
  loadUnreadCount,
  unreadCount
})
</script>

<style lang="scss" scoped>
@use './style';

.is-read {
  color: var(--el-text-color-secondary) !important;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: rgb(var(--art-danger));
  border-radius: 50%;
  flex-shrink: 0;
  margin-left: 8px;
}

.notification-detail {
  h3 {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 12px;
  }
  
  .meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 16px;
    
    span + span {
      margin-left: 16px;
    }
  }
  
  .content-text {
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
}

.notice-list li {
  position: relative;
  display: flex;
  align-items: center;
}
</style>
