<template>
  <ElDialog
    v-model="visible"
    :title="t('logManager.loginLog.detailTitle')"
    width="45%"
    :before-close="handleClose"
  >
    <ElDescriptions v-if="detailData" :column="2" border class="mb-4">
      <ElDescriptionsItem :label="t('logManager.loginLog.username')" align="center">
        {{ detailData.username }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.nickname')" align="center">
        {{ detailData.user_nickname }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.department')" align="center">
        {{ detailData.department_name }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.loginIp')" align="center">
        {{ detailData.login_ip }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.loginLocation')" align="center">
        {{ detailData.login_location }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.browser')" align="center">
        {{ detailData.browser }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.os')" align="center">
        {{ detailData.os }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.status')" align="center">
        <ElTag :type="detailData.status === 1 ? 'success' : 'danger'">
          {{
            detailData.status === 1
              ? t('logManager.loginLog.success')
              : t('logManager.loginLog.failed')
          }}
        </ElTag>
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.sessionId')" :span="2" align="center">
        <ElInput v-model="detailData.session_id" readonly size="small">
          <template #append>
            <ElButton size="small" @click="copySessionId">
              {{ t('common.copy') }}
            </ElButton>
          </template>
        </ElInput>
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.loginTime')" align="center">
        {{ formatDateTime(detailData.created_at) }}
      </ElDescriptionsItem>
      <ElDescriptionsItem :label="t('logManager.loginLog.updateTime')" align="center">
        {{ formatDateTime(detailData.updated_at) }}
      </ElDescriptionsItem>
    </ElDescriptions>

    <template #footer>
      <div class="flex justify-center items-center">
        <ElButton @click="handleClose">
          {{ t('common.close') }}
        </ElButton>
        <ElButton
          v-if="detailData && detailData.online === true"
          type="danger"
          @click="handleLogout"
        >
          {{ t('logManager.loginLog.forceLogout') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { fetchLogoutUser } from '@/api/system/log'
  import type { LoginLogInfo } from '@/api/system/log'

  interface Props {
    modelValue: boolean
    data?: LoginLogInfo | null
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
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // 复制会话ID
  const copySessionId = async () => {
    if (!detailData.value?.session_id) return

    try {
      await navigator.clipboard.writeText(detailData.value.session_id)
      ElMessage.success(t('common.copySuccess'))
    } catch {
      // 降级处理
      const textArea = document.createElement('textarea')
      textArea.value = detailData.value.session_id
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      ElMessage.success(t('common.copySuccess'))
    }
  }

  // 强制注销
  const handleLogout = async () => {
    if (!detailData.value?.session_id) return

    try {
      await fetchLogoutUser(detailData.value.session_id)
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
</script>
