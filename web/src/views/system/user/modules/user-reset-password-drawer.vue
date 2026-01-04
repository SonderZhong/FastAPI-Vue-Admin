<template>
  <ElDrawer
    v-model="visible"
    :title="$t('user.resetPassword', '重置密码')"
    size="400px"
    :destroy-on-close="false"
    class="reset-password-drawer"
    @close="handleClose"
  >
    <div v-if="userData" class="h-full flex flex-col">
      <!-- 用户信息 -->
      <div class="user-info-card">
        <ElAvatar :size="48" :src="getAvatarUrl(userData.avatar)">
          <ElIcon><User /></ElIcon>
        </ElAvatar>
        <div class="user-info">
          <div class="user-name">{{ userData.nickname }}</div>
          <div class="user-meta">@{{ userData.username }}</div>
          <div class="user-dept">{{ userData.department_name || '无部门' }}</div>
        </div>
      </div>

      <!-- 密码重置表单 -->
      <div class="form-container">
        <ElForm ref="formRef" :model="formData" :rules="rules" label-width="100px" label-position="left">
          <ElFormItem :label="$t('user.resetMode', '重置方式')" prop="resetMode">
            <ElRadioGroup v-model="formData.resetMode" class="w-full">
              <ElRadio value="default">{{ $t('user.useDefaultPassword', '使用默认密码') }}</ElRadio>
              <ElRadio value="custom">{{ $t('user.customPassword', '自定义密码') }}</ElRadio>
            </ElRadioGroup>
          </ElFormItem>

          <ElFormItem v-if="formData.resetMode === 'default'" :label="$t('user.defaultPassword', '默认密码')">
            <ElInput v-model="defaultPassword" readonly show-password />
          </ElFormItem>

          <ElFormItem v-if="formData.resetMode === 'custom'" :label="$t('user.newPassword', '新密码')" prop="password">
            <ElInput
              v-model="formData.password"
              type="password"
              :placeholder="$t('user.enterNewPassword', '请输入新密码')"
              show-password
            />
          </ElFormItem>

          <ElFormItem v-if="formData.resetMode === 'custom'" :label="$t('user.confirmPassword', '确认密码')" prop="confirmPassword">
            <ElInput
              v-model="formData.confirmPassword"
              type="password"
              :placeholder="$t('user.enterConfirmPassword', '请再次输入密码')"
              show-password
            />
          </ElFormItem>
        </ElForm>

        <!-- 密码强度 -->
        <div v-if="formData.resetMode === 'custom' && formData.password" class="password-strength">
          <div class="strength-label">{{ $t('user.passwordStrength', '密码强度') }}：</div>
          <div class="strength-bars">
            <div
              v-for="level in 4"
              :key="level"
              :class="['strength-bar', getPasswordStrengthColor(level)]"
            ></div>
          </div>
          <div class="strength-text">{{ getPasswordStrengthText() }}</div>
        </div>

        <!-- 提示 -->
        <ElAlert type="warning" :closable="false" class="mt-4">
          <template #title>
            <span class="font-medium">{{ $t('user.resetPasswordTip', '重置密码提示') }}</span>
          </template>
          <ul class="tip-list">
            <li>• {{ $t('user.resetPasswordTip1', '重置后用户需要使用新密码登录') }}</li>
            <li>• {{ $t('user.resetPasswordTip2', '建议通知用户修改默认密码') }}</li>
            <li v-if="formData.resetMode === 'custom'">• {{ $t('user.resetPasswordTip3', '密码长度至少6位，建议包含字母和数字') }}</li>
          </ul>
        </ElAlert>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <ElButton round @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" round :loading="submitting" @click="handleConfirm">
          {{ $t('buttons.confirm', '确认重置') }}
        </ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { resetUserPassword, type UserInfo } from '@/api/system/user'
import { getAvatarUrl } from '@/utils'

const { t: $t } = useI18n()

interface Props {
  modelValue: boolean
  userData: UserInfo | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref<FormInstance>()
const submitting = ref(false)
const defaultPassword = ref('123456')

const formData = ref({
  resetMode: 'default' as 'default' | 'custom',
  password: '',
  confirmPassword: ''
})

const rules = computed<FormRules>(() => ({
  password: [
    { required: true, message: $t('user.passwordRequired', '请输入密码'), trigger: 'blur' },
    { min: 6, message: $t('user.passwordMinLength', '密码长度至少6位'), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: $t('user.confirmPasswordRequired', '请确认密码'), trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== formData.value.password) {
          callback(new Error($t('user.passwordNotMatch', '两次输入的密码不一致')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}))

watch(visible, (newVisible) => {
  if (newVisible) {
    formData.value = {
      resetMode: 'default',
      password: '',
      confirmPassword: ''
    }
  }
})

const getPasswordStrength = () => {
  const password = formData.value.password
  if (!password) return 0
  let strength = 0
  if (password.length >= 6) strength++
  if (password.length >= 8) strength++
  if (/\d/.test(password)) strength++
  if (/[a-zA-Z]/.test(password)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++
  return Math.min(strength, 4)
}

const getPasswordStrengthColor = (level: number) => {
  const strength = getPasswordStrength()
  if (level <= strength) {
    if (strength <= 1) return 'bg-red-400'
    if (strength <= 2) return 'bg-orange-400'
    if (strength <= 3) return 'bg-yellow-400'
    return 'bg-green-400'
  }
  return 'bg-gray-200'
}

const getPasswordStrengthText = () => {
  const strength = getPasswordStrength()
  if (strength <= 1) return $t('user.passwordWeak', '弱')
  if (strength <= 2) return $t('user.passwordMedium', '中')
  if (strength <= 3) return $t('user.passwordStrong', '强')
  return $t('user.passwordVeryStrong', '很强')
}

const handleClose = () => {
  formData.value = {
    resetMode: 'default',
    password: '',
    confirmPassword: ''
  }
  formRef.value?.resetFields()
  visible.value = false
}

const handleConfirm = async () => {
  if (!props.userData) return

  try {
    submitting.value = true

    if (formData.value.resetMode === 'custom') {
      await formRef.value?.validate()
    }

    const passwordToReset = formData.value.resetMode === 'custom' 
      ? formData.value.password 
      : defaultPassword.value

    await resetUserPassword(props.userData.id, { password: passwordToReset })

    ElMessage.success($t('user.resetPasswordSuccess', '密码重置成功'))
    emit('success')
    handleClose()
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error($t('user.resetPasswordFailed', '重置密码失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.reset-password-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
  
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  :deep(.el-drawer__body) {
    padding: 0;
    display: flex;
    flex-direction: column;
  }
  
  :deep(.el-drawer__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

.user-info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.user-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.user-dept {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.form-container {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.password-strength {
  margin-top: 12px;
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.strength-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.strength-bars {
  display: flex;
  gap: 4px;
}

.strength-bar {
  flex: 1;
  height: 6px;
  border-radius: 3px;
}

.strength-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
  text-align: right;
}

.tip-list {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
  
  li {
    margin-bottom: 4px;
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
