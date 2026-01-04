<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>{{ t('dashboard.loginStatistics') }}</h3>
      <p class="chart-desc">{{ t('dashboard.loginStatisticsDesc') }}</p>
    </div>
    <div class="chart-content">
      <!-- 第一行：饼图 -->
      <ElRow :gutter="20">
        <ElCol :xs="24" :sm="24" :md="8">
          <div ref="osChartRef" class="chart-item"></div>
        </ElCol>
        <ElCol :xs="24" :sm="24" :md="8">
          <div ref="browserChartRef" class="chart-item"></div>
        </ElCol>
        <ElCol :xs="24" :sm="24" :md="8">
          <div ref="locationChartRef" class="chart-item"></div>
        </ElCol>
      </ElRow>
      <!-- 第二行：趋势图 -->
      <ElRow :gutter="20" class="trend-row">
        <ElCol :span="24">
          <div ref="trendChartRef" class="chart-item trend-chart"></div>
        </ElCol>
      </ElRow>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onBeforeUnmount } from 'vue'
  import { useI18n } from 'vue-i18n'
  import * as echarts from 'echarts'
  import { fetchLoginStatistics, fetchLoginTrend } from '@/api/dashboard'
  import { ElMessage } from 'element-plus'

  const { t } = useI18n()

  const osChartRef = ref<HTMLElement>()
  const browserChartRef = ref<HTMLElement>()
  const locationChartRef = ref<HTMLElement>()
  const trendChartRef = ref<HTMLElement>()

  let osChart: echarts.ECharts | null = null
  let browserChart: echarts.ECharts | null = null
  let locationChart: echarts.ECharts | null = null
  let trendChart: echarts.ECharts | null = null

  // 加载统计数据
  const loadStatisticsData = async () => {
    try {
      const res = await fetchLoginStatistics()
      if (res.data) {
        initOsChart(res.data.osDistribution || [])
        initBrowserChart(res.data.browserDistribution || [])
        initLocationChart(res.data.locationDistribution || [])
      }
    } catch (error) {
      console.error('Failed to load login statistics:', error)
      ElMessage.error(t('dashboard.loadStatisticsFailed'))
    }
  }

  // 加载趋势数据
  const loadTrendData = async () => {
    try {
      const res = await fetchLoginTrend()
      if (res.data) {
        initTrendChart(res.data)
      }
    } catch (error) {
      console.error('Failed to load login trend:', error)
      ElMessage.error(t('dashboard.loadTrendFailed'))
    }
  }

  // 初始化操作系统饼图
  const initOsChart = (data: any[]) => {
    if (!osChartRef.value) return
    osChart = echarts.init(osChartRef.value)
    const option = {
      title: {
        text: t('dashboard.osDistribution'),
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, fontWeight: 'normal' }
      },
      tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
      legend: { orient: 'horizontal', bottom: 10, type: 'scroll' },
      series: [{
        name: t('dashboard.osDistribution'),
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: data
      }]
    }
    osChart.setOption(option)
  }

  // 初始化浏览器饼图
  const initBrowserChart = (data: any[]) => {
    if (!browserChartRef.value) return
    browserChart = echarts.init(browserChartRef.value)
    const option = {
      title: {
        text: t('dashboard.browserDistribution'),
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, fontWeight: 'normal' }
      },
      tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
      legend: { orient: 'horizontal', bottom: 10, type: 'scroll' },
      series: [{
        name: t('dashboard.browserDistribution'),
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: data
      }]
    }
    browserChart.setOption(option)
  }

  // 初始化登录地区柱状图
  const initLocationChart = (data: any[]) => {
    if (!locationChartRef.value) return
    locationChart = echarts.init(locationChartRef.value)
    const option = {
      title: {
        text: t('dashboard.locationDistribution'),
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, fontWeight: 'normal' }
      },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
      xAxis: { type: 'value', boundaryGap: [0, 0.01] },
      yAxis: { type: 'category', data: data.map((item) => item.name) },
      series: [{
        name: t('dashboard.loginCount'),
        type: 'bar',
        data: data.map((item) => item.value),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#79bbff' }
          ])
        }
      }]
    }
    locationChart.setOption(option)
  }

  // 初始化趋势图
  const initTrendChart = (data: any) => {
    if (!trendChartRef.value) return
    trendChart = echarts.init(trendChartRef.value)
    
    const locationSeries = data.locationSeries.map((item: any) => ({
      name: item.name,
      type: 'line',
      smooth: true,
      data: item.data,
      areaStyle: { opacity: 0.1 }
    }))
    
    const option = {
      title: {
        text: t('dashboard.last7DaysLoginTrend'),
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, fontWeight: 'normal' }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } }
      },
      legend: {
        data: [t('dashboard.totalLogins'), ...data.locationSeries.map((item: any) => item.name)],
        bottom: 10,
        type: 'scroll'
      },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: data.dates },
      yAxis: { type: 'value' },
      series: [
        {
          name: t('dashboard.totalLogins'),
          type: 'line',
          smooth: true,
          data: data.loginCounts,
          itemStyle: { color: '#409EFF' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ])
          },
          lineStyle: { width: 3 },
          emphasis: { focus: 'series' }
        },
        ...locationSeries
      ]
    }
    trendChart.setOption(option)
  }

  // 窗口大小改变时调整图表
  const handleResize = () => {
    osChart?.resize()
    browserChart?.resize()
    locationChart?.resize()
    trendChart?.resize()
  }

  onMounted(() => {
    loadStatisticsData()
    loadTrendData()
    window.addEventListener('resize', handleResize)
  })

  onBeforeUnmount(() => {
    osChart?.dispose()
    browserChart?.dispose()
    locationChart?.dispose()
    trendChart?.dispose()
    window.removeEventListener('resize', handleResize)
  })
</script>

<style lang="scss" scoped>
  .chart-container {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

    .chart-header {
      margin-bottom: 20px;
      h3 {
        font-size: 16px;
        font-weight: 500;
        color: #303133;
        margin: 0 0 8px 0;
      }
      .chart-desc {
        font-size: 13px;
        color: #909399;
        margin: 0;
      }
    }

    .chart-content {
      .chart-item {
        height: 300px;
        min-height: 300px;
      }
      .trend-row {
        margin-top: 20px;
        border-top: 1px solid #ebeef5;
        padding-top: 20px;
      }
      .trend-chart {
        height: 350px;
        min-height: 350px;
      }
    }
  }

  @media (max-width: 768px) {
    .chart-container .chart-content {
      .chart-item {
        margin-bottom: 20px;
      }
      .trend-chart {
        height: 280px;
        min-height: 280px;
      }
    }
  }
</style>
