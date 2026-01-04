<template>
  <ElDrawer
    v-model="visible"
    :title="t('logManager.operationLog.detailTitle')"
    size="800px"
    direction="rtl"
    :before-close="handleClose"
  >
    <ElDescriptions v-if="detailData" :column="2" border class="mb-4">
      <ElDescriptionsItem :label="t('logManager.operationLog.operationName')" align="center">
        {{ detailData.operation_name }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.operationType')" align="center">
        <ElTag
          v-if="getOperationTypeColor(detailData.operation_type)"
          :type="getOperationTypeColor(detailData.operation_type)!"
        >
          {{ getOperationTypeText(detailData.operation_type) }}
        </ElTag>
        <span v-else>{{ getOperationTypeText(detailData.operation_type) }}</span>
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.operator')" align="center">
        {{ detailData.operator_name }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.operatorNickname')" align="center">
        {{ detailData.operator_nickname }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.department')" align="center">
        {{ detailData.department_name }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.requestMethod')" align="center">
        <ElTag
          v-if="getMethodColor(detailData.request_method)"
          :type="getMethodColor(detailData.request_method)!"
        >
          {{ detailData.request_method }}
        </ElTag>
        <span v-else>{{ detailData.request_method }}</span>
      </ElDescriptionsItem>
      <ElDescriptionsItem
        :label="t('logManager.operationLog.requestPath')"
        :span="2"
        align="center"
      >
        <ElInput v-model="detailData.request_path" readonly size="small" />
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.host')" align="center">
        {{ detailData.host }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.location')" align="center">
        {{ detailData.location }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.browser')" align="center">
        {{ detailData.browser }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.os')" align="center">
        {{ detailData.os }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.status')" align="center">
        <ElTag :type="String(detailData.status) === '1' ? 'success' : 'danger'">
          {{
            String(detailData.status) === '1'
              ? t('logManager.operationLog.success')
              : t('logManager.operationLog.failed')
          }}
        </ElTag>
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.costTime')" align="center">
        <ElTag
          :type="
            detailData.cost_time < 300
              ? 'success'
              : detailData.cost_time > 300 && detailData.cost_time < 1000
                ? 'warning'
                : 'danger'
          "
        >
          {{ detailData.cost_time }} ms
        </ElTag>
      </ElDescriptionsItem>

      <ElDescriptionsItem :label="t('logManager.operationLog.operationTime')" align="center">
        {{ formatDateTime(detailData.created_at) }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.updateTime')" align="center">
        {{ formatDateTime(detailData.updated_at) }}
      </ElDescriptionsItem>
    </ElDescriptions>

    <!-- 请求参数 -->
    <ElDivider>
      <div class="flex items-center justify-between w-full px-4">
        <span>{{ t('logManager.operationLog.requestParams') }}</span>
        <ElButton size="small" type="primary" link @click="copyRequestParams">
          <template #icon>
            <ElIcon><DocumentCopy /></ElIcon>
          </template>
          复制
        </ElButton>
      </div>
    </ElDivider>
    <div v-if="detailData" class="json-container">
      <ElScrollbar max-height="400px">
        <VueJsonPretty
          :data="parseJson(detailData.request_params)"
          :show-double-quotes="true"
          :show-length="true"
          :show-line="true"
          :deep="3"
          :editable="false"
          :show-line-number="true"
          :show-icon="true"
          :path-collapsible="() => true"
        />
      </ElScrollbar>
    </div>

    <!-- 响应结果 -->
    <ElDivider>
      <div class="flex items-center justify-between w-full px-4">
        <span>{{ t('logManager.operationLog.responseResult') }}</span>
        <ElButton size="small" type="primary" link @click="copyResponseResult">
          <template #icon>
            <ElIcon><DocumentCopy /></ElIcon>
          </template>
          复制
        </ElButton>
      </div>
    </ElDivider>
    <div v-if="detailData" class="json-container">
      <ElScrollbar max-height="400px">
        <VueJsonPretty
          :data="parseJson(detailData.response_result)"
          :show-double-quotes="true"
          :show-length="true"
          :show-line="true"
          :deep="3"
          :editable="false"
          :show-line-number="true"
          :show-icon="true"
          :path-collapsible="() => true"
        />
      </ElScrollbar>
    </div>

    <!-- 用户代理 -->
    <ElDivider>{{ t('logManager.operationLog.userAgent') }}</ElDivider>
    <ElInput
      v-if="detailData"
      v-model="detailData.user_agent"
      type="textarea"
      :rows="3"
      readonly
      resize="none"
    />

    <template #footer>
      <div class="flex justify-center items-center">
        <ElButton type="primary" @click="handleClose">
          {{ t('common.close') }}
        </ElButton>
        <ElButton type="danger" @click="handleDelete">
          {{ t('common.delete') }}
        </ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import { DocumentCopy } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { fetchDeleteOperationLog } from '@/api/system/log'
  import type { OperationLogInfo } from '@/api/system/log'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'

  interface Props {
    modelValue: boolean
    data?: OperationLogInfo | null
  }

  interface Emits {
    (e: 'update:modelValue', value: boolean): void
    (e: 'refresh'): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()

  const { t } = useI18n()

  const visible = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
  })

  const detailData = computed(() => props.data)

  // 格式化日期时间
  const formatDateTime = (dateString: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('zh-CN')
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

  // 获取操作类型颜色
  const getOperationTypeColor = (
    type: string
  ): 'success' | 'warning' | 'danger' | 'info' | 'primary' | null => {
    const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary' | null> = {
      '1': 'success', // 新增
      '2': 'warning', // 更新
      '3': 'danger', // 删除
      '4': 'info', // 查询
      '5': 'primary', // 导出
      '6': 'primary', // 导入
      '7': 'warning', // 授权
      '0': null // 其他
    }
    return typeMap[type] || null
  }

  // 获取操作类型文本
  const getOperationTypeText = (type: string) => {
    const typeMap: Record<string, string> = {
      '1': t('logManager.operationLog.typeOptions.insert'),
      '2': t('logManager.operationLog.typeOptions.update'),
      '3': t('logManager.operationLog.typeOptions.delete'),
      '4': t('logManager.operationLog.typeOptions.select'),
      '5': t('logManager.operationLog.typeOptions.export'),
      '6': t('logManager.operationLog.typeOptions.import'),
      '7': t('logManager.operationLog.typeOptions.grant'),
      '0': t('logManager.operationLog.typeOptions.other')
    }
    return typeMap[type] || type
  }

  // 获取请求方法颜色
  const getMethodColor = (
    method: string
  ): 'success' | 'warning' | 'danger' | 'info' | 'primary' | null => {
    const methodMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary' | null> =
      {
        GET: 'info',
        POST: 'success',
        PUT: 'warning',
        DELETE: 'danger',
        PATCH: 'warning'
      }
    return methodMap[method] || null
  }

  // 删除操作日志
  const handleDelete = async () => {
    if (!detailData.value?.id) return

    try {
      await fetchDeleteOperationLog(detailData.value.id)
      emit('refresh')
      handleClose()
    } catch {
      // 错误已经通过API显示
    }
  }

  // 关闭对话框
  const handleClose = () => {
    visible.value = false
  }

  // 复制请求参数
  const copyRequestParams = async () => {
    if (!detailData.value?.request_params) return

    try {
      const jsonData = parseJson(detailData.value.request_params)
      const jsonString = JSON.stringify(jsonData, null, 2)
      await navigator.clipboard.writeText(jsonString)
      ElMessage.success('复制成功')
    } catch (error) {
      console.error('复制失败:', error)
      ElMessage.error('复制失败')
    }
  }

  // 复制响应结果
  const copyResponseResult = async () => {
    if (!detailData.value?.response_result) return

    try {
      const jsonData = parseJson(detailData.value.response_result)
      const jsonString = JSON.stringify(jsonData, null, 2)
      await navigator.clipboard.writeText(jsonString)
      ElMessage.success('复制成功')
    } catch (error) {
      console.error('复制失败:', error)
      ElMessage.error('复制失败')
    }
  }
</script>

<style scoped lang="scss">
  .json-container {
    background-color: #f5f7fa;
    border-radius: 4px;
    padding: 12px;
    margin: 8px 0;

    :deep(.vjs-tree) {
      font-size: 13px;
      line-height: 1.6;
    }

    :deep(.vjs-tree-node) {
      &:hover {
        background-color: #e8eef5;
      }
    }

    :deep(.vjs-key) {
      color: #e96900;
      font-weight: 500;
    }

    :deep(.vjs-value-string) {
      color: #50a14f;
    }

    :deep(.vjs-value-number) {
      color: #0184bc;
    }

    :deep(.vjs-value-boolean) {
      color: #986801;
    }

    :deep(.vjs-value-null) {
      color: #a0a1a7;
    }
  }
</style>
