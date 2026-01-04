<template>
  <div class="data-statistics">
    <ElRow :gutter="20">
      <!-- 未读通知统计 -->
      <ElCol :xs="24" :sm="12" :md="12" :lg="6">
        <div class="stat-card notification-stat" @click="goToMyNotification">
          <div class="stat-icon">
            <i class="iconfont-sys">&#xe6c2;</i>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <CountUp :end-value="statistics.unreadNotifications" />
            </div>
            <div class="stat-label">未读通知</div>
          </div>
        </div>
      </ElCol>

      <!-- 全部通知统计 -->
      <ElCol :xs="24" :sm="12" :md="12" :lg="6">
        <div class="stat-card total-notification-stat" @click="goToMyNotification">
          <div class="stat-icon">
            <i class="iconfont-sys">&#xe747;</i>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <CountUp :end-value="statistics.totalNotifications" />
            </div>
            <div class="stat-label">全部通知</div>
          </div>
        </div>
      </ElCol>

      <!-- 今日登录统计 -->
      <ElCol :xs="24" :sm="12" :md="12" :lg="6">
        <div class="stat-card login-stat" @click="goToLoginRecord">
          <div class="stat-icon">
            <i class="iconfont-sys">&#xe608;</i>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <CountUp :end-value="statistics.todayLogins" />
            </div>
            <div class="stat-label">今日登录</div>
          </div>
        </div>
      </ElCol>

      <!-- 今日操作统计 -->
      <ElCol :xs="24" :sm="12" :md="12" :lg="6">
        <div class="stat-card operation-stat" @click="goToOperationRecord">
          <div class="stat-icon">
            <i class="iconfont-sys">&#xe7a8;</i>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <CountUp :end-value="statistics.todayOperations" />
            </div>
            <div class="stat-label">今日操作</div>
          </div>
        </div>
      </ElCol>
    </ElRow>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import CountUp from './CountUp.vue'

  const router = useRouter()

  // 统计数据
  const statistics = ref({
    unreadNotifications: 0,
    totalNotifications: 0,
    todayLogins: 0,
    todayOperations: 0
  })

  // 跳转到我的通知
  const goToMyNotification = () => {
    router.push('/my-notification')
  }

  // 跳转到登录记录
  const goToLoginRecord = () => {
    router.push('/personal-login-record')
  }

  // 跳转到操作记录
  const goToOperationRecord = () => {
    router.push('/personal-operation-record')
  }

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      const { fetchDashboardStatistics } = await import('@/api/dashboard')
      const response = await fetchDashboardStatistics()

      if (response.success && response.data) {
        statistics.value = {
          unreadNotifications: response.data.unreadNotifications || 0,
          totalNotifications: response.data.totalNotifications || 0,
          todayLogins: response.data.todayLogins || 0,
          todayOperations: response.data.todayOperations || 0
        }
      }
    } catch (error) {
      console.error('加载统计数据失败:', error)
      statistics.value = {
        unreadNotifications: 0,
        totalNotifications: 0,
        todayLogins: 0,
        todayOperations: 0
      }
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
      padding: 30px 28px;
      background: var(--el-bg-color);
      border-radius: 16px;
      box-shadow: var(--art-card-shadow);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      overflow: hidden;
      margin-bottom: 20px;
      border: 1px solid var(--art-card-border);
      cursor: pointer;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, var(--gradient-start), var(--gradient-end));
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      }

      &::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, var(--gradient-start) 0%, transparent 70%);
        opacity: 0.05;
        pointer-events: none;
      }

      &:hover {
        transform: translateY(-6px);
        box-shadow: var(--art-box-shadow-sm);
        border-color: var(--gradient-start);

        &::before {
          transform: scaleX(1);
        }

        .stat-icon {
          transform: scale(1.15) rotate(8deg);
          background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));

          i {
            color: white;
          }
        }

        .stat-value {
          color: var(--gradient-start);
        }
      }

      .stat-icon {
        position: absolute;
        right: 28px;
        top: 28px;
        width: 68px;
        height: 68px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 16px;
        background: var(--icon-bg);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);

        i {
          font-size: 34px;
          color: var(--icon-color);
          transition: color 0.3s ease;
        }
      }

      .stat-info {
        max-width: calc(100% - 90px);

        .stat-value {
          font-size: 40px;
          font-weight: 800;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
          font-family:
            -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial,
            sans-serif;
          letter-spacing: -1px;
          line-height: 1.2;
          transition: color 0.3s ease;
        }

        .stat-label {
          font-size: 15px;
          color: var(--el-text-color-regular);
          font-weight: 600;
          letter-spacing: 0.3px;
        }
      }

      // 不同统计卡片的主题色
      &.notification-stat {
        --gradient-start: rgb(var(--art-danger));
        --gradient-end: rgb(var(--art-danger));
        --icon-bg: rgb(var(--art-bg-danger));
        --icon-color: rgb(var(--art-danger));
      }

      &.total-notification-stat {
        --gradient-start: rgb(var(--art-warning));
        --gradient-end: rgb(var(--art-warning));
        --icon-bg: rgb(var(--art-bg-warning));
        --icon-color: rgb(var(--art-warning));
      }

      &.login-stat {
        --gradient-start: rgb(var(--art-secondary));
        --gradient-end: rgb(var(--art-secondary));
        --icon-bg: rgb(var(--art-bg-secondary));
        --icon-color: rgb(var(--art-secondary));
      }

      &.operation-stat {
        --gradient-start: rgb(var(--art-success));
        --gradient-end: rgb(var(--art-success));
        --icon-bg: rgb(var(--art-bg-success));
        --icon-color: rgb(var(--art-success));
      }
    }
  }

  // 暗色模式适配
  html.dark {
    .data-statistics .stat-card {
      background: var(--el-bg-color-overlay);
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);

      &:hover {
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
      }

      &::after {
        opacity: 0.08;
      }

      .stat-icon {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      }
    }
  }

  // 响应式优化
  @media (max-width: 768px) {
    .data-statistics .stat-card {
      padding: 24px 20px;

      .stat-icon {
        width: 56px;
        height: 56px;
        right: 20px;
        top: 20px;

        i {
          font-size: 28px;
        }
      }

      .stat-info {
        .stat-value {
          font-size: 32px;
        }

        .stat-label {
          font-size: 14px;
        }
      }
    }
  }
</style>
