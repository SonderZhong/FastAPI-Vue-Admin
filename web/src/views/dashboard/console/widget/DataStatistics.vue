<template>
  <div class="data-statistics">
    <ElRow :gutter="20">
      <ElCol v-for="item in statCards" :key="item.key" :xs="24" :sm="12" :md="12" :lg="6">
        <div class="stat-card" :class="item.themeClass" @click="item.onClick">
          <div class="stat-icon">
            <i class="iconfont-sys" v-html="item.icon"></i>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <CountUp :end-value="item.value" />
            </div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-meta">{{ item.meta }}</div>
          </div>
        </div>
      </ElCol>
    </ElRow>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRouter } from 'vue-router'
  import CountUp from './CountUp.vue'
  import { fetchDashboardStatistics } from '@/api/dashboard'

  const { t } = useI18n()
  const router = useRouter()

  const statistics = ref({
    unreadNotifications: 0,
    totalNotifications: 0,
    todayLogins: 0,
    todayOperations: 0,
    weekLogins: 0,
    weekOperations: 0,
    notificationReadRate: 0
  })

  const goToMyNotification = () => router.push('/my-notification')
  const goToLoginRecord = () => router.push('/personal-login-record')
  const goToOperationRecord = () => router.push('/personal-operation-record')

  const statCards = computed(() => [
    {
      key: 'unreadNotifications',
      value: statistics.value.unreadNotifications,
      label: t('dashboard.unreadNotifications'),
      meta: `${t('dashboard.readRate')} ${statistics.value.notificationReadRate}%`,
      icon: '&#xe6c2;',
      themeClass: 'notification-stat',
      onClick: goToMyNotification
    },
    {
      key: 'totalNotifications',
      value: statistics.value.totalNotifications,
      label: t('dashboard.totalNotifications'),
      meta: t('dashboard.checkMessages'),
      icon: '&#xe747;',
      themeClass: 'total-notification-stat',
      onClick: goToMyNotification
    },
    {
      key: 'todayLogins',
      value: statistics.value.todayLogins,
      label: t('dashboard.todayLogins'),
      meta: `${t('dashboard.last7DaysLogins')} ${statistics.value.weekLogins}`,
      icon: '&#xe608;',
      themeClass: 'login-stat',
      onClick: goToLoginRecord
    },
    {
      key: 'todayOperations',
      value: statistics.value.todayOperations,
      label: t('dashboard.todayOperations'),
      meta: `${t('dashboard.last7DaysOperations')} ${statistics.value.weekOperations}`,
      icon: '&#xe7a8;',
      themeClass: 'operation-stat',
      onClick: goToOperationRecord
    }
  ])

  const loadStatistics = async () => {
    try {
      const response = await fetchDashboardStatistics()
      if (response.success && response.data) {
        statistics.value = {
          unreadNotifications: response.data.unreadNotifications || 0,
          totalNotifications: response.data.totalNotifications || 0,
          todayLogins: response.data.todayLogins || 0,
          todayOperations: response.data.todayOperations || 0,
          weekLogins: response.data.weekLogins || 0,
          weekOperations: response.data.weekOperations || 0,
          notificationReadRate: response.data.notificationReadRate || 0
        }
      }
    } catch (error) {
      console.error('Failed to load dashboard statistics:', error)
    }
  }

  onMounted(() => {
    loadStatistics()
  })
</script>

<style lang="scss" scoped>
  .data-statistics {
    margin-bottom: 24px;

    .stat-card {
      position: relative;
      padding: 28px;
      background: var(--el-bg-color);
      border-radius: 16px;
      box-shadow: var(--art-card-shadow);
      transition: all 0.3s ease;
      overflow: hidden;
      margin-bottom: 20px;
      border: 1px solid var(--art-card-border);
      cursor: pointer;
      min-height: 166px;

      &::before {
        content: '';
        position: absolute;
        inset: 0 0 auto;
        height: 4px;
        background: linear-gradient(90deg, var(--gradient-start), var(--gradient-end));
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.3s ease;
      }

      &::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, var(--gradient-start) 0%, transparent 70%);
        opacity: 0.06;
        pointer-events: none;
      }

      &:hover {
        transform: translateY(-4px);
        box-shadow: var(--art-box-shadow-sm);
        border-color: var(--gradient-start);

        &::before {
          transform: scaleX(1);
        }

        .stat-icon {
          transform: scale(1.08);
        }

        .stat-value {
          color: var(--gradient-start);
        }
      }
    }

    .stat-icon {
      position: absolute;
      right: 28px;
      top: 28px;
      width: 64px;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 16px;
      background: var(--icon-bg);
      transition: transform 0.3s ease;

      :deep(i) {
        font-size: 32px;
        color: var(--icon-color);
      }
    }

    .stat-info {
      max-width: calc(100% - 88px);
      display: flex;
      min-height: 110px;
      flex-direction: column;
      justify-content: space-between;
      gap: 6px;
    }

    .stat-value {
      font-size: 38px;
      line-height: 1.15;
      font-weight: 800;
      color: var(--el-text-color-primary);
      transition: color 0.3s ease;
    }

    .stat-label {
      font-size: 15px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .stat-meta {
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }

    .notification-stat {
      --gradient-start: rgb(var(--art-danger));
      --gradient-end: rgb(var(--art-danger));
      --icon-bg: rgb(var(--art-bg-danger));
      --icon-color: rgb(var(--art-danger));
    }

    .total-notification-stat {
      --gradient-start: rgb(var(--art-warning));
      --gradient-end: rgb(var(--art-warning));
      --icon-bg: rgb(var(--art-bg-warning));
      --icon-color: rgb(var(--art-warning));
    }

    .login-stat {
      --gradient-start: rgb(var(--art-secondary));
      --gradient-end: rgb(var(--art-secondary));
      --icon-bg: rgb(var(--art-bg-secondary));
      --icon-color: rgb(var(--art-secondary));
    }

    .operation-stat {
      --gradient-start: rgb(var(--art-success));
      --gradient-end: rgb(var(--art-success));
      --icon-bg: rgb(var(--art-bg-success));
      --icon-color: rgb(var(--art-success));
    }
  }

  html.dark {
    .data-statistics .stat-card {
      background: var(--el-bg-color-overlay);
    }
  }

  @media (max-width: 768px) {
    .data-statistics {
      .stat-card {
        min-height: 148px;
        padding: 22px;
      }

      .stat-icon {
        width: 54px;
        height: 54px;
        right: 22px;
        top: 22px;

        :deep(i) {
          font-size: 26px;
        }
      }

      .stat-info {
        max-width: calc(100% - 74px);
      }

      .stat-value {
        font-size: 30px;
      }
    }
  }
</style>
