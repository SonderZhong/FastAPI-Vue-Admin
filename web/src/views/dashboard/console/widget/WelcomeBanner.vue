<template>
  <div class="welcome-banner">
    <div class="banner-content">
      <div class="welcome-info">
        <div class="greeting">
          <h2>{{ greeting }}，{{ userDisplayName }}</h2>
          <p class="user-role">
            <ElTag :type="userTypeTagType" size="small">
              {{ userTypeText }}
            </ElTag>
            <span v-if="userInfo?.department_name" class="department">
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
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useUserStore } from '@/store/modules/user'
  import { getUserTypeName, UserType } from '@/utils/permission'

  const { t } = useI18n()
  const userStore = useUserStore()
  const userInfo = computed(() => userStore.getUserInfo)
  const userDisplayName = computed(() => userInfo.value?.nickname || userInfo.value?.username || '-')
  const currentTime = ref('')
  const currentDate = ref('')
  let timer: number | null = null

  const greeting = computed(() => {
    const hour = new Date().getHours()
    if (hour < 6) return t('dashboard.greetings.lateNight')
    if (hour < 9) return t('dashboard.greetings.morning')
    if (hour < 12) return t('dashboard.greetings.forenoon')
    if (hour < 14) return t('dashboard.greetings.noon')
    if (hour < 18) return t('dashboard.greetings.afternoon')
    if (hour < 22) return t('dashboard.greetings.evening')
    return t('dashboard.greetings.night')
  })

  const userTypeText = computed(() => {
    const type = userInfo.value?.user_type ?? UserType.NORMAL_USER
    return getUserTypeName(type)
  })

  const userTypeTagType = computed(() => {
    const type = userInfo.value?.user_type ?? UserType.NORMAL_USER
    switch (type) {
      case UserType.SUPER_ADMIN:
        return 'danger'
      case UserType.TENANT_ADMIN:
        return 'warning'
      case UserType.DEPT_ADMIN:
        return 'primary'
      default:
        return 'info'
    }
  })

  const updateTime = () => {
    const now = new Date()
    currentTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
    const weeks = [
      t('dashboard.weekdays.sun'),
      t('dashboard.weekdays.mon'),
      t('dashboard.weekdays.tue'),
      t('dashboard.weekdays.wed'),
      t('dashboard.weekdays.thu'),
      t('dashboard.weekdays.fri'),
      t('dashboard.weekdays.sat')
    ]
    currentDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${weeks[now.getDay()]}`
  }

  onMounted(() => {
    updateTime()
    timer = window.setInterval(updateTime, 1000)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })
</script>

<style lang="scss" scoped>
  .welcome-banner {
    margin-bottom: 20px;
    background: linear-gradient(135deg, rgb(var(--art-primary)) 0%, #91a7ff 100%);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--art-card-shadow);
  }

  .banner-content {
    padding: 24px 32px;
    color: #fff;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .welcome-info {
    display: flex;
    width: 100%;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
  }

  .greeting h2 {
    margin: 0 0 8px;
    font-size: 24px;
    font-weight: 600;
  }

  .user-role {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin: 0;
  }

  .department {
    color: rgba(255, 255, 255, 0.9);
  }

  .time-info {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .current-time,
  .current-date {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .time {
    font-size: 20px;
    font-weight: 600;
    font-family: 'Courier New', monospace;
  }

  @media (max-width: 900px) {
    .banner-content {
      padding: 20px 24px;
    }

    .welcome-info {
      flex-direction: column;
      align-items: flex-start;
    }

    .time-info {
      justify-content: flex-start;
      gap: 12px 20px;
    }
  }
</style>
