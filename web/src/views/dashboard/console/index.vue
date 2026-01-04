<template>
  <div class="console">
    <!-- 欢迎横幅 + 实时时间 -->
    <WelcomeBanner />

    <!-- 数据统计卡片 -->
    <DataStatistics />

    <!-- 登录统计图表（含趋势） -->
    <LoginStatisticsChart />

    <!-- 操作统计图表 -->
    <OperationStatisticsChart />
  </div>
</template>

<script setup lang="ts">
  import WelcomeBanner from './widget/WelcomeBanner.vue'
  import DataStatistics from './widget/DataStatistics.vue'
  import LoginStatisticsChart from './widget/LoginStatisticsChart.vue'
  import OperationStatisticsChart from './widget/OperationStatisticsChart.vue'
  import { useCommon } from '@/composables/useCommon'

  defineOptions({ name: 'Console' })

  useCommon().scrollToTop()
</script>

<style lang="scss" scoped>
  @use './style';
</style>
