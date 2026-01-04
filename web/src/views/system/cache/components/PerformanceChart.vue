<template>
  <div ref="chartRef" class="w-full h-64"></div>
</template>

<script setup lang="ts">
  import { ref, onMounted, watch, nextTick } from 'vue'
  import * as echarts from 'echarts'
  import { useI18n } from 'vue-i18n'

  interface Props {
    performanceStats?: {
      total_commands_processed: number
      instantaneous_ops_per_sec: number
      total_net_input_bytes: number
      total_net_output_bytes: number
      keyspace_hits: number
      keyspace_misses: number
      hit_rate: number
    }
    connectionStats?: {
      connected_clients: number
      blocked_clients: number
      total_connections_received: number
    }
  }

  const props = withDefaults(defineProps<Props>(), {
    performanceStats: () => ({
      total_commands_processed: 0,
      instantaneous_ops_per_sec: 0,
      total_net_input_bytes: 0,
      total_net_output_bytes: 0,
      keyspace_hits: 0,
      keyspace_misses: 0,
      hit_rate: 0
    }),
    connectionStats: () => ({
      connected_clients: 0,
      blocked_clients: 0,
      total_connections_received: 0
    })
  })

  const { t } = useI18n()
  const chartRef = ref<HTMLDivElement>()
  let chartInstance: echarts.ECharts | null = null

  const initChart = () => {
    if (!chartRef.value) return

    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }

  const updateChart = () => {
    if (!chartInstance || !props.performanceStats || !props.connectionStats) return

    const { hit_rate, instantaneous_ops_per_sec } = props.performanceStats

    const option = {
      title: {
        text: t('cache.charts.performanceStats'),
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        formatter: (params: any) => {
          const { name, value } = params
          if (name === t('cache.charts.hitRate')) {
            return `${name}: ${value.toFixed(1)}%`
          } else if (name === t('cache.charts.opsPerSec')) {
            return `${name}: ${value.toLocaleString()} ops/s`
          } else {
            return `${name}: ${value.toLocaleString()}`
          }
        }
      },
      series: [
        {
          name: t('cache.charts.hitRate'),
          type: 'gauge',
          center: ['25%', '55%'],
          radius: '70%',
          min: 0,
          max: 100,
          splitNumber: 5,
          axisLine: {
            lineStyle: {
              width: 8,
              color: [
                [0.3, '#e74c3c'],
                [0.7, '#f39c12'],
                [1, '#27ae60']
              ]
            }
          },
          pointer: {
            itemStyle: {
              color: 'inherit'
            }
          },
          axisTick: {
            distance: -15,
            length: 5,
            lineStyle: {
              color: '#fff',
              width: 1
            }
          },
          splitLine: {
            distance: -20,
            length: 10,
            lineStyle: {
              color: '#fff',
              width: 2
            }
          },
          axisLabel: {
            color: 'inherit',
            distance: 25,
            fontSize: 10,
            formatter: (value: number) => value + '%'
          },
          detail: {
            valueAnimation: true,
            formatter: '{value}%',
            color: 'inherit',
            fontSize: 16,
            offsetCenter: [0, '80%']
          },
          title: {
            fontSize: 12,
            offsetCenter: [0, '-80%']
          },
          data: [
            {
              value: hit_rate,
              name: t('cache.charts.hitRate')
            }
          ]
        },
        {
          name: t('cache.charts.opsPerSec'),
          type: 'gauge',
          center: ['75%', '55%'],
          radius: '70%',
          min: 0,
          max: Math.max(instantaneous_ops_per_sec * 2, 1000),
          splitNumber: 4,
          axisLine: {
            lineStyle: {
              width: 8,
              color: [
                [0.3, '#3498db'],
                [0.7, '#9b59b6'],
                [1, '#e67e22']
              ]
            }
          },
          pointer: {
            itemStyle: {
              color: 'inherit'
            }
          },
          axisTick: {
            distance: -15,
            length: 5,
            lineStyle: {
              color: '#fff',
              width: 1
            }
          },
          splitLine: {
            distance: -20,
            length: 10,
            lineStyle: {
              color: '#fff',
              width: 2
            }
          },
          axisLabel: {
            color: 'inherit',
            distance: 25,
            fontSize: 10,
            formatter: (value: number) => {
              if (value >= 1000) {
                return (value / 1000).toFixed(0) + 'K'
              }
              return value.toString()
            }
          },
          detail: {
            valueAnimation: true,
            formatter: (value: number) => {
              if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K'
              }
              return value.toString()
            },
            color: 'inherit',
            fontSize: 16,
            offsetCenter: [0, '80%']
          },
          title: {
            fontSize: 12,
            offsetCenter: [0, '-80%']
          },
          data: [
            {
              value: instantaneous_ops_per_sec,
              name: t('cache.charts.opsPerSec')
            }
          ]
        }
      ]
    }

    chartInstance.setOption(option, true)
  }

  watch(() => [props.performanceStats, props.connectionStats], updateChart, { deep: true })

  onMounted(async () => {
    await nextTick()
    initChart()
  })
</script>
