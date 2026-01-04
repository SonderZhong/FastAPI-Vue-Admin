<template>
  <ElDrawer
    v-model="visible"
    :title="t('personalOperationRecord.detailTitle')"
    direction="rtl"
    size="800px"
    :before-close="handleClose"
  >
    <ElDescriptions v-if="detailData" :column="2" border class="mb-4">
      <ElDescriptionsItem :label="t('personalOperationRecord.operationName')" align="center">
        {{ detailData.operation_name }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.operationType')" align="center">
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
      <ElDescriptionsItem :label="t('personalOperationRecord.requestMethod')" align="center">
        <ElTag
          v-if="getMethodColor(detailData.request_method)"
          :type="getMethodColor(detailData.request_method)!"
        >
          {{ detailData.request_method }}
        </ElTag>
        <span v-else>{{ detailData.request_method }}</span>
      </ElDescriptionsItem>
      <ElDescriptionsItem
        :label="t('personalOperationRecord.requestPath')"
        :span="2"
        align="center"
      >
        <ElInput v-model="detailData.request_path" readonly size="small" />
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.host')" align="center">
        {{ detailData.host }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.location')" align="center">
        {{ detailData.location }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.browser')" align="center">
        {{ detailData.browser }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.os')" align="center">
        {{ detailData.os }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.status')" align="center">
        <ElTag :type="String(detailData.status) === '1' ? 'success' : 'danger'">
          {{
            String(detailData.status) === '1'
              ? t('personalOperationRecord.success')
              : t('personalOperationRecord.failed')
          }}
        </ElTag>
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('personalOperationRecord.costTime')" align="center">
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

      <ElDescriptionsItem :label="t('personalOperationRecord.operationTime')" align="center">
        {{ formatDateTime(detailData.created_at) }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.operationLog.updateTime')" align="center">
        {{ formatDateTime(detailData.updated_at) }}
      </ElDescriptionsItem>
    </ElDescriptions>

    <!-- 请求参数 -->
    <ElDivider>
      <div class="flex items-center justify-between w-full px-4">
        <span>{{ t('personalOperationRecord.requestParams') }}</span>
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
        <span>{{ t('personalOperationRecord.responseResult') }}</span>
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
    <ElDivider>{{ t('personalOperationRecord.userAgent') }}</ElDivider>
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
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import { DocumentCopy } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import type { OperationLogInfo } from '@/api/system/log'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import {
    ElDrawer,
    ElDescriptions,
    ElDescriptionsItem,
    ElTag,
    ElInput,
    ElButton,
    ElDivider,
    ElScrollbar,
    ElIcon
  } from 'element-plus'

  interface Props {
    modelValue: boolean
    data?: OperationLogInfo | null
  }

  interface Emits {
    (e: 'update:modelValue', value: boolean): void
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

  // 关闭抽屉
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
  :deep(.el-drawer__body) {
    padding: 20px;
  }

  :deep(.el-descriptions__cell) {
    vertical-align: middle;
  }

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
