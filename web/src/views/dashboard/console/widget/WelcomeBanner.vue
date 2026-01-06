<template>
  <div class="welcome-banner">
    <div class="banner-content">
      <div class="welcome-info">
        <div class="greeting">
          <h2>{{ greeting }}，{{ userInfo?.nickname || userInfo?.username }}！</h2>
          <p class="user-role">
            <ElTag :type="getUserTypeTagType" size="small">
              {{ getUserTypeText }}
            </ElTag>
            <span class="department" v-if="userInfo?.department_name">
              {{ userInfo.department_name }}
            </span>
          </p>
        </div>
        
        <div class="time-info">
          <div class="current-time">
            <i class="iconfont-sys">&#xe6f1;</i>
            <span class="time">{{ currentTime }}</span>
          </div>
          <div class="current-date">
            <i class="iconfont-sys">&#xe6a0;</i>
            <span>{{ currentDate }}</span>
          </div>
        </div>
      </div>
      
      <div class="banner-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { getUserTypeName, UserType } from '@/utils/permission'

const userStore = useUserStore()
const userInfo = computed(() => userStore.getUserInfo)

// 当前时间
const currentTime = ref('')
const currentDate = ref('')
let timer: number | null = null

// 问候语
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '凌晨好'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

// 用户身份文本
const getUserTypeText = computed(() => {
  const userType = userInfo.value?.user_type ?? 3
  return getUserTypeName(userType)
})

// 用户身份标签类型
const getUserTypeTagType = computed(() => {
  const userType = userInfo.value?.user_type ?? 3
  switch (userType) {
    case UserType.SUPER_ADMIN:
      return 'danger'
    case UserType.ADMIN:
      return 'warning'
    case UserType.DEPT_ADMIN:
      return 'primary'
    default:
      return 'info'
  }
})

// 更新时间
const updateTime = () => {
  const now = new Date()
  
  // 格式化时间 HH:mm:ss
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}:${seconds}`
  
  // 格式化日期
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const date = String(now.getDate()).padStart(2, '0')
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const weekDay = weekDays[now.getDay()]
  currentDate.value = `${year}年${month}月${date}日 ${weekDay}`
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style lang="scss" scoped>
.welcome-banner {
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgb(var(--art-primary)) 0%, #91A7FF 100%);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  box-shadow: var(--art-card-shadow);

  .banner-content {
    position: relative;
    padding: 24px 32px;
    color: white;
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .welcome-info {
    flex: 1;

    .greeting {
      margin-bottom: 16px;

      h2 {
        margin: 0 0 8px 0;
        font-size: 24px;
        font-weight: 600;
        color: white !important;
      }

      .user-role {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 14px;

        .department {
          color: rgba(255, 255, 255, 0.9);
        }
      }
    }

    .time-info {
      display: flex;
      gap: 24px;
      font-size: 14px;

      .current-time,
      .current-date {
        display: flex;
        align-items: center;
        gap: 8px;
        color: rgba(255, 255, 255, 0.95);

        i {
          font-size: 18px;
          color: rgba(255, 255, 255, 0.95) !important;
        }

        .time {
          font-size: 20px;
          font-weight: 600;
          font-family: 'Courier New', monospace;
        }
      }
    }
  }

  .banner-decoration {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 300px;
    pointer-events: none;

    .circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      animation: float 6s ease-in-out infinite;

      &.circle-1 {
        width: 120px;
        height: 120px;
        right: 50px;
        top: -20px;
        animation-delay: 0s;
      }

      &.circle-2 {
        width: 80px;
        height: 80px;
        right: 180px;
        bottom: 20px;
        animation-delay: 2s;
      }

      &.circle-3 {
        width: 60px;
        height: 60px;
        right: 120px;
        top: 50%;
        transform: translateY(-50%);
        animation-delay: 4s;
      }
    }
  }
}

// 暗色模式适配
html.dark {
  .welcome-banner {
    background: linear-gradient(135deg, rgba(93, 135, 255, 0.8) 0%, rgba(145, 167, 255, 0.6) 100%);
    
    .banner-decoration .circle {
      background: rgba(255, 255, 255, 0.08);
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}
</style>

