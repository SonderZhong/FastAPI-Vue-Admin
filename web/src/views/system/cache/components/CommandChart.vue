<template>
  <div ref="chartRef" class="w-full h-64"></div>
</template>

<script setup lang="ts">
  import { ref, onMounted, watch, nextTick } from 'vue'
  import * as echarts from 'echarts'
  import { useI18n } from 'vue-i18n'

  interface Props {
    commandStats?: Array<{
      name: string
      value: number
      usec: number
      usec_per_call: number
    }>
  }

  const props = withDefaults(defineProps<Props>(), {
    commandStats: () => []
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
    if (!chartInstance || !props.commandStats) return

    // 获取前10个最常用的命令
    const topCommands = [...props.commandStats].sort((a, b) => b.value - a.value).slice(0, 10)

    const commandNames = topCommands.map((cmd) => cmd.name.toUpperCase())
    const commandValues = topCommands.map((cmd) => cmd.value)
    const avgTimes = topCommands.map((cmd) => cmd.usec_per_call.toFixed(2))

    const option = {
      title: {
        text: t('cache.charts.commandStats'),
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params: any) => {
          const data = params[0]
          const index = data.dataIndex
          return `${data.name}<br/>
                  ${t('cache.charts.callCount')}: ${data.value.toLocaleString()}<br/>
                  ${t('cache.charts.avgTime')}: ${avgTimes[index]}μs`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: commandNames,
        axisLabel: {
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        name: t('cache.charts.callCount'),
        nameTextStyle: {
          fontSize: 12
        },
        axisLabel: {
          formatter: (value: number) => {
            if (value >= 1000000) {
              return (value / 1000000).toFixed(1) + 'M'
            } else if (value >= 1000) {
              return (value / 1000).toFixed(1) + 'K'
            }
            return value.toString()
          }
        }
      },
      series: [
        {
          name: t('cache.charts.callCount'),
          type: 'bar',
          data: commandValues,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#3498db' },
              { offset: 1, color: '#2980b9' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#5dade2' },
                { offset: 1, color: '#3498db' }
              ])
            }
          }
        }
      ]
    }

    chartInstance.setOption(option, true)
  }

  watch(() => props.commandStats, updateChart, { deep: true })

  onMounted(async () => {
    await nextTick()
    initChart()
  })
</script>
