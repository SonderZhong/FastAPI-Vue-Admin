<template>
  <div ref="chartRef" class="w-full h-64"></div>
</template>

<script setup lang="ts">
  import { ref, onMounted, watch, nextTick } from 'vue'
  import * as echarts from 'echarts'
  import { useI18n } from 'vue-i18n'

  interface Props {
    memoryStats?: {
      used_memory: number
      used_memory_human: string
      used_memory_rss: number
      used_memory_peak: number
      maxmemory: number
      maxmemory_human: string
      mem_fragmentation_ratio: number
    }
  }

  const props = withDefaults(defineProps<Props>(), {
    memoryStats: () => ({
      used_memory: 0,
      used_memory_human: '0B',
      used_memory_rss: 0,
      used_memory_peak: 0,
      maxmemory: 0,
      maxmemory_human: 'unlimited',
      mem_fragmentation_ratio: 0
    })
  })

  const { t } = useI18n()
  const chartRef = ref<HTMLDivElement>()
  let chartInstance: echarts.ECharts | null = null

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + sizes[i]
  }

  const initChart = () => {
    if (!chartRef.value) return

    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }

  const updateChart = () => {
    if (!chartInstance || !props.memoryStats) return

    const { used_memory, used_memory_rss, maxmemory } = props.memoryStats

    // 计算可用内存
    const availableMemory = maxmemory > 0 ? maxmemory - used_memory : used_memory * 2
    const rssMemory = used_memory_rss - used_memory

    const option = {
      title: {
        text: t('cache.charts.memoryUsage'),
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const percentage = (
            (params.value / (used_memory + availableMemory + Math.max(0, rssMemory))) *
            100
          ).toFixed(1)
          return `${params.name}<br/>${formatBytes(params.value)} (${percentage}%)`
        }
      },
      legend: {
        bottom: 0,
        left: 'center',
        textStyle: {
          fontSize: 12
        }
      },
      series: [
        {
          name: t('cache.charts.memoryDistribution'),
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              formatter: (params: any) => {
                return `${params.name}\n${formatBytes(params.value)}`
              }
            }
          },
          labelLine: {
            show: false
          },
          data: [
            {
              value: used_memory,
              name: t('cache.charts.usedMemory'),
              itemStyle: { color: '#e74c3c' }
            },
            {
              value: Math.max(0, rssMemory),
              name: t('cache.charts.rssMemory'),
              itemStyle: { color: '#f39c12' }
            },
            {
              value: Math.max(0, availableMemory),
              name:
                maxmemory > 0 ? t('cache.charts.availableMemory') : t('cache.charts.systemMemory'),
              itemStyle: { color: '#27ae60' }
            }
          ].filter((item) => item.value > 0)
        }
      ]
    }

    chartInstance.setOption(option, true)
  }

  watch(() => props.memoryStats, updateChart, { deep: true })

  onMounted(async () => {
    await nextTick()
    initChart()
  })
</script>
