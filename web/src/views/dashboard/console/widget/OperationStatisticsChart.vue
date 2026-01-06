<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>{{ t('dashboard.operationStatistics') }}</h3>
      <p class="chart-desc">{{ t('dashboard.operationStatisticsDesc') }}</p>
    </div>
    <div class="chart-content">
      <ElRow :gutter="20">
        <ElCol :xs="24" :sm="24" :md="8">
          <div ref="typeChartRef" class="chart-item"></div>
        </ElCol>
        <ElCol :xs="24" :sm="24" :md="8">
          <div ref="moduleChartRef" class="chart-item"></div>
        </ElCol>
        <ElCol :xs="24" :sm="24" :md="8">
          <div ref="trendChartRef" class="chart-item"></div>
        </ElCol>
      </ElRow>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import * as echarts from 'echarts'
  import { fetchOperationStatistics } from '@/api/dashboard'
  import { ElMessage } from 'element-plus'
  import { useSettingStore } from '@/store/modules/setting'
  import { storeToRefs } from 'pinia'

  const { t } = useI18n()
  const settingStore = useSettingStore()
  const { isDark } = storeToRefs(settingStore)

  const typeChartRef = ref<HTMLElement>()
  const moduleChartRef = ref<HTMLElement>()
  const trendChartRef = ref<HTMLElement>()

  let typeChart: echarts.ECharts | null = null
  let moduleChart: echarts.ECharts | null = null
  let trendChart: echarts.ECharts | null = null

  // 缓存数据用于主题切换时重新渲染
  let cachedData: any = null

  // 获取主题相关样式
  const getThemeStyles = () => ({
    textColor: isDark.value ? '#b5b7c8' : '#303133',
    subTextColor: isDark.value ? '#808290' : '#909399',
    borderColor: isDark.value ? '#363843' : '#fff',
    axisLineColor: isDark.value ? '#444' : '#EDEDED',
    splitLineColor: isDark.value ? '#363843' : '#ebeef5'
  })

  // 加载统计数据
  const loadData = async () => {
    try {
      const res = await fetchOperationStatistics()
      if (res.data) {
        cachedData = res.data
        initTypeChart(res.data.typeDistribution || [])
        initModuleChart(res.data.moduleDistribution || [])
        initTrendChart(res.data.dates || [], res.data.dailyTrend || [])
      }
    } catch (error) {
      console.error('Failed to load operation statistics:', error)
      ElMessage.error(t('dashboard.loadStatisticsFailed'))
    }
  }

  // 初始化操作类型饼图
  const initTypeChart = (data: any[]) => {
    if (!typeChartRef.value) return
    const theme = getThemeStyles()

    if (!typeChart) {
      typeChart = echarts.init(typeChartRef.value)
    }
    const option = {
      title: {
        text: t('dashboard.operationTypeDistribution'),
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
          color: theme.textColor
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 10,
        type: 'scroll',
        textStyle: { color: theme.subTextColor }
      },
      series: [
        {
          name: t('dashboard.operationTypeDistribution'),
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: theme.borderColor,
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
              color: theme.textColor
            }
          },
          labelLine: {
            show: false
          },
          data: data
        }
      ]
    }
    typeChart.setOption(option)
  }

  // 初始化模块分布饼图
  const initModuleChart = (data: any[]) => {
    if (!moduleChartRef.value) return
    const theme = getThemeStyles()

    if (!moduleChart) {
      moduleChart = echarts.init(moduleChartRef.value)
    }
    const option = {
      title: {
        text: t('dashboard.moduleDistribution'),
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
          color: theme.textColor
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 10,
        type: 'scroll',
        textStyle: { color: theme.subTextColor }
      },
      series: [
        {
          name: t('dashboard.moduleDistribution'),
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: theme.borderColor,
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
              color: theme.textColor
            }
          },
          labelLine: {
            show: false
          },
          data: data
        }
      ]
    }
    moduleChart.setOption(option)
  }

  // 初始化操作趋势折线图
  const initTrendChart = (dates: string[], data: number[]) => {
    if (!trendChartRef.value) return
    const theme = getThemeStyles()

    if (!trendChart) {
      trendChart = echarts.init(trendChartRef.value)
    }
    const option = {
      title: {
        text: t('dashboard.operationTrend'),
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
          color: theme.textColor
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'line'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '20%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates.map(d => d.slice(5)),
        axisLine: { lineStyle: { color: theme.axisLineColor } },
        axisLabel: { color: theme.subTextColor }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: theme.axisLineColor } },
        axisLabel: { color: theme.subTextColor },
        splitLine: { lineStyle: { color: theme.splitLineColor } }
      },
      series: [
        {
          name: t('dashboard.operationCount'),
          type: 'line',
          smooth: true,
          data: data,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ])
          },
          lineStyle: {
            color: '#67C23A',
            width: 2
          },
          itemStyle: {
            color: '#67C23A'
          }
        }
      ]
    }
    trendChart.setOption(option)
  }

  // 窗口大小改变时调整图表
  const handleResize = () => {
    typeChart?.resize()
    moduleChart?.resize()
    trendChart?.resize()
  }

  // 监听主题变化，重新渲染图表
  watch(isDark, () => {
    if (cachedData) {
      initTypeChart(cachedData.typeDistribution || [])
      initModuleChart(cachedData.moduleDistribution || [])
      initTrendChart(cachedData.dates || [], cachedData.dailyTrend || [])
    }
  })

  onMounted(() => {
    loadData()
    window.addEventListener('resize', handleResize)
  })

  onBeforeUnmount(() => {
    typeChart?.dispose()
    moduleChart?.dispose()
    trendChart?.dispose()
    window.removeEventListener('resize', handleResize)
  })
</script>

<style lang="scss" scoped>
  .chart-container {
    background: var(--art-main-bg-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: var(--art-card-shadow);
    border: 1px solid var(--art-card-border);

    .chart-header {
      margin-bottom: 20px;

      h3 {
        font-size: 16px;
        font-weight: 500;
        color: var(--art-gray-900);
        margin: 0 0 8px 0;
      }

      .chart-desc {
        font-size: 13px;
        color: var(--art-gray-600);
        margin: 0;
      }
    }

    .chart-content {
      .chart-item {
        height: 300px;
        min-height: 300px;
      }
    }
  }

  @media (max-width: 768px) {
    .chart-container {
      .chart-content {
        .chart-item {
          margin-bottom: 20px;
        }
      }
    }
  }
</style>
