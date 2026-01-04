<template>
  <ElDialog
    v-model="visible"
    :title="$t('cache.detailDialog.title')"
    width="70%"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="loading">
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem :label="$t('cache.fields.cacheName')" align="center">
          <ElTag type="primary">{{ cacheDetail.cache_name }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('cache.fields.cacheKey')" align="center">
          <ElTag>{{ cacheDetail.cache_key }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('cache.fields.ttl')" align="center">
          <div
            v-if="cacheDetail.ttl && cacheDetail.ttl > 0"
            class="flex items-center justify-center space-x-2"
          >
            <ElTag type="warning">{{ formatTime(countdown) }}</ElTag>
            <span class="text-sm text-gray-500">
              ({{ $t('cache.fields.expireTime') }}: {{ cacheDetail.expire_time }})
            </span>
          </div>
          <ElTag v-else-if="cacheDetail.ttl === -1" type="success">{{
            $t('cache.fields.permanent')
          }}</ElTag>
          <ElTag v-else type="info">{{ $t('cache.fields.unknown') }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('cache.fields.cacheValue')" :span="2" align="center">
          <div class="cache-value-container">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm text-gray-600">
                {{ $t('cache.detailDialog.valueType') }}:
                {{ getValueType(cacheDetail.cache_value) }}
              </span>
              <div class="flex gap-2">
                <ElButton @click="formatValue" size="small" type="primary" plain>
                  <ElIcon><MagicStick /></ElIcon>
                  {{ $t('cache.detailDialog.format') }}
                </ElButton>
                <ElButton @click="copyValue" size="small" type="success" plain>
                  <ElIcon><CopyDocument /></ElIcon>
                  {{ $t('cache.detailDialog.copy') }}
                </ElButton>
              </div>
            </div>
            <div v-if="getValueType(cacheDetail.cache_value) === 'JSON'">
              <ElScrollbar height="200px">
                <VueJsonPretty
                  :data="parseJson(cacheDetail.cache_value)"
                  :show-double-quotes="true"
                  :show-length="true"
                  :show-line="true"
                  :expand-depth="3"
                  :editable="false"
                  :show-line-number="true"
                  :show-select-controller="true"
                  :show-icon="true"
                  :select-on-click-node="false"
                  :path-collapsible="() => true"
                  :path-selectable="() => false"
                  :virtual="false"
                  :height="200"
                />
              </ElScrollbar>
            </div>
            <ElInput
              v-else
              v-model="formattedValue"
              type="textarea"
              :rows="15"
              readonly
              class="cache-value-textarea"
            />
          </div>
        </ElDescriptionsItem>
      </ElDescriptions>
    </div>

    <template #footer>
      <div class="flex justify-between">
        <ElButton @click="refreshDetail" type="primary" plain>
          <ElIcon><Refresh /></ElIcon>
          {{ $t('buttons.refresh') }}
        </ElButton>
        <div>
          <ElButton @click="handleClose">{{ $t('buttons.close') }}</ElButton>
        </div>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, watch, computed, onUnmounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { MagicStick, CopyDocument, Refresh } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { fetchCacheDetail, type CacheInfo } from '@/api/system/cache'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'

  interface Props {
    modelValue: boolean
    cacheName: string
    cacheKey: string
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: false,
    cacheName: '',
    cacheKey: ''
  })

  const emit = defineEmits<{
    'update:modelValue': [value: boolean]
  }>()

  const { t } = useI18n()

  // 响应式数据
  const loading = ref(false)
  const cacheDetail = ref<CacheInfo>({})
  const formattedValue = ref('')
  const countdown = ref(0)
  let countdownTimer: ReturnType<typeof setInterval> | null = null

  // 计算属性
  const visible = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value)
  })

  // 格式化时间显示
  const formatTime = (seconds: number): string => {
    if (seconds <= 0) return '00:00:00'

    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes
        .toString()
        .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    } else {
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
  }

  // 开始倒计时
  const startCountdown = (ttl: number) => {
    countdown.value = ttl

    // 清除之前的定时器
    if (countdownTimer) {
      clearInterval(countdownTimer)
    }

    // 开始新的倒计时
    countdownTimer = setInterval(() => {
      if (countdown.value > 0) {
        countdown.value--
      } else {
        // 倒计时结束，停止定时器
        if (countdownTimer) {
          clearInterval(countdownTimer)
          countdownTimer = null
        }
      }
    }, 1000)
  }

  // 停止倒计时
  const stopCountdown = () => {
    if (countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }

  // 获取值类型
  const getValueType = (value: any): string => {
    if (value === null || value === undefined) return 'null'
    if (typeof value === 'string') {
      try {
        JSON.parse(value)
        return 'JSON'
      } catch {
        return 'String'
      }
    }
    if (typeof value === 'number') return 'Number'
    if (typeof value === 'boolean') return 'Boolean'
    if (Array.isArray(value)) return 'Array'
    if (typeof value === 'object') return 'Object'
    return 'Unknown'
  }

  // 格式化值
  const formatValue = () => {
    try {
      const value = cacheDetail.value.cache_value
      if (typeof value === 'string') {
        try {
          const parsed = JSON.parse(value)
          formattedValue.value = JSON.stringify(parsed, null, 2)
        } catch {
          formattedValue.value = value
        }
      } else if (typeof value === 'object') {
        formattedValue.value = JSON.stringify(value, null, 2)
      } else {
        formattedValue.value = String(value)
      }
      ElMessage.success(t('cache.messages.formatSuccess'))
    } catch (error) {
      console.error('格式化失败:', error)
      ElMessage.error(t('cache.messages.formatError'))
    }
  }

  // 复制值
  const copyValue = async () => {
    try {
      await navigator.clipboard.writeText(formattedValue.value)
      ElMessage.success(t('cache.messages.copySuccess'))
    } catch (error) {
      console.error('复制失败:', error)
      ElMessage.error(t('cache.messages.copyError'))
    }
  }

  // 获取缓存详情
  const getCacheDetail = async () => {
    if (!props.cacheName || !props.cacheKey) return

    loading.value = true
    try {
      const response = await fetchCacheDetail(props.cacheName, props.cacheKey)
      if (response?.success) {
        cacheDetail.value = response.data || {}
        const value = cacheDetail.value.cache_value
        if (typeof value === 'string') {
          formattedValue.value = value
        } else {
          formattedValue.value = JSON.stringify(value, null, 2)
        }

        // 如果有TTL，启动倒计时
        if (cacheDetail.value.ttl && cacheDetail.value.ttl > 0) {
          startCountdown(cacheDetail.value.ttl)
        }
      }
    } catch (error) {
      console.error('获取缓存详情失败:', error)
      ElMessage.error(t('cache.messages.fetchDetailError'))
    } finally {
      loading.value = false
    }
  }

  // 刷新详情
  const refreshDetail = async () => {
    await getCacheDetail()
    ElMessage.success(t('cache.messages.refreshSuccess'))
  }

  // 关闭对话框
  const handleClose = () => {
    visible.value = false
    cacheDetail.value = {}
    formattedValue.value = ''
    stopCountdown()
  }

  // 解析JSON字符串
  const parseJson = (jsonStr: string) => {
    if (!jsonStr) return {}
    if (typeof jsonStr === 'object') return jsonStr
    try {
      const parsed = JSON.parse(jsonStr)
      return parsed
    } catch (error) {
      // 如果解析失败，返回包装的对象以便显示原始字符串
      return {
        _error: 'JSON解析失败',
        _rawData: jsonStr,
        _errorMessage: error instanceof Error ? error.message : '未知错误'
      }
    }
  }

  // 监听对话框打开
  watch(visible, (newVal) => {
    if (newVal && props.cacheName && props.cacheKey) {
      getCacheDetail()
    } else if (!newVal) {
      stopCountdown()
    }
  })

  // 组件卸载时清理定时器
  onUnmounted(() => {
    stopCountdown()
  })
</script>

<style lang="scss" scoped>
  .cache-value-container {
    .cache-value-textarea {
      :deep(.el-textarea__inner) {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
      }
    }
  }
</style>
