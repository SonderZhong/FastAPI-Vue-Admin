<template>
  <ElDialog
    v-model="dialogVisible"
    :title="$t('user.resetPassword', '重置密码')"
    width="500px"
    :before-close="handleClose"
    destroy-on-close
  >
    <template #header>
      <div class="flex items-center gap-3">
        <ElIcon class="text-blue-500"><Key /></ElIcon>
        <div>
          <h3 class="text-lg font-medium text-gray-900">
            {{ $t('user.resetPassword', '重置密码') }}
          </h3>
          <p class="text-sm text-gray-500" v-if="props.userData">
            {{ props.userData.nickname }} (@{{ props.userData.username }})
          </p>
        </div>
      </div>
    </template>

    <div v-if="props.userData">
      <!-- 用户信息展示 -->
      <div class="bg-gray-50 p-4 rounded-lg mb-6">
        <div class="flex items-center gap-3">
          <ElAvatar :size="50" :src="getAvatarUrl(props.userData.avatar)">
            <ElIcon><User /></ElIcon>
          </ElAvatar>
          <div>
            <h4 class="font-medium text-gray-900">{{ props.userData.nickname }}</h4>
            <p class="text-sm text-gray-600">@{{ props.userData.username }}</p>
            <p class="text-sm text-gray-500">
              {{ props.userData.department_name || $t('common.noDepartment', '无部门') }}
            </p>
          </div>
        </div>
      </div>

      <!-- 密码重置表单 -->
      <ElForm
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        label-position="right"
      >
        <ElFormItem :label="$t('user.resetMode', '重置方式')" prop="resetMode">
          <ElRadioGroup v-model="formData.resetMode">
            <ElRadio value="default">{{ $t('user.useDefaultPassword', '使用默认密码') }}</ElRadio>
            <ElRadio value="custom">{{ $t('user.customPassword', '自定义密码') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>

        <ElFormItem
          v-if="formData.resetMode === 'default'"
          :label="$t('user.defaultPassword', '默认密码')"
        >
          <ElInput v-model="defaultPassword" readonly show-password style="cursor: pointer" />
        </ElFormItem>

        <ElFormItem
          v-if="formData.resetMode === 'custom'"
          :label="$t('user.newPassword', '新密码')"
          prop="password"
        >
          <ElInput
            v-model="formData.password"
            type="password"
            :placeholder="$t('user.enterNewPassword', '请输入新密码')"
            show-password
          />
        </ElFormItem>

        <ElFormItem
          v-if="formData.resetMode === 'custom'"
          :label="$t('user.confirmPassword', '确认密码')"
          prop="confirmPassword"
        >
          <ElInput
            v-model="formData.confirmPassword"
            type="password"
            :placeholder="$t('user.enterConfirmPassword', '请再次输入密码')"
            show-password
          />
        </ElFormItem>
      </ElForm>

      <!-- 密码强度提示 -->
      <div v-if="formData.resetMode === 'custom' && formData.password" class="mb-4">
        <div class="text-sm text-gray-600 mb-2"
          >{{ $t('user.passwordStrength', '密码强度') }}：</div
        >
        <div class="flex gap-2">
          <div
            v-for="level in 4"
            :key="level"
            :class="['h-2 rounded-full flex-1', getPasswordStrengthColor(level)]"
          ></div>
        </div>
        <div class="text-xs text-gray-500 mt-1">
          {{ getPasswordStrengthText() }}
        </div>
      </div>

      <!-- 温馨提示 -->
      <ElAlert
        :title="$t('user.resetPasswordTip', '重置密码提示')"
        type="warning"
        :closable="false"
        class="mb-4"
      >
        <template #default>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• {{ $t('user.resetPasswordTip1', '重置后用户需要使用新密码登录') }}</li>
            <li>• {{ $t('user.resetPasswordTip2', '建议通知用户修改默认密码') }}</li>
            <li v-if="formData.resetMode === 'custom'"
              >• {{ $t('user.resetPasswordTip3', '密码长度至少6位，建议包含字母和数字') }}</li
            >
          </ul>
        </template>
      </ElAlert>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <ElButton @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" :loading="loading" @click="handleConfirm">
          {{ $t('buttons.confirm', '确认重置') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
  import { Key, User } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { resetUserPassword, type UserInfo } from '@/api/system/user'
  import { getAvatarUrl } from '@/utils'

  // Props 和 Emits
  interface Props {
    visible: boolean
    userData: UserInfo | null
  }

  interface Emits {
    (e: 'update:visible', visible: boolean): void
    (e: 'success'): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()
  const { t: $t } = useI18n()

  // 表单引用
  const formRef = ref<FormInstance>()

  // 响应式数据
  const loading = ref(false)
  const defaultPassword = ref('123456')

  // 表单数据
  const formData = ref({
    resetMode: 'default' as 'default' | 'custom',
    password: '',
    confirmPassword: ''
  })

  // 对话框显示状态
  const dialogVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  // 表单验证规则
  const rules = computed<FormRules>(() => ({
    password: [
      { required: true, message: $t('user.passwordRequired', '请输入密码'), trigger: 'blur' },
      { min: 6, message: $t('user.passwordMinLength', '密码长度至少6位'), trigger: 'blur' }
    ],
    confirmPassword: [
      {
        required: true,
        message: $t('user.confirmPasswordRequired', '请确认密码'),
        trigger: 'blur'
      },
      {
        validator: (rule, value, callback) => {
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

  /**
   * 计算密码强度
   */
  const getPasswordStrength = () => {
    const password = formData.value.password
    if (!password) return 0

    let strength = 0
    // 长度
    if (password.length >= 6) strength++
    if (password.length >= 8) strength++
    // 包含数字
    if (/\d/.test(password)) strength++
    // 包含字母
    if (/[a-zA-Z]/.test(password)) strength++
    // 包含特殊字符
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++

    return Math.min(strength, 4)
  }

  /**
   * 获取密码强度颜色
   */
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

  /**
   * 获取密码强度文本
   */
  const getPasswordStrengthText = () => {
    const strength = getPasswordStrength()
    if (strength <= 1) return $t('user.passwordWeak', '弱')
    if (strength <= 2) return $t('user.passwordMedium', '中')
    if (strength <= 3) return $t('user.passwordStrong', '强')
    return $t('user.passwordVeryStrong', '很强')
  }

  /**
   * 处理对话框关闭
   */
  const handleClose = () => {
    formData.value = {
      resetMode: 'default',
      password: '',
      confirmPassword: ''
    }
    formRef.value?.resetFields()
    emit('update:visible', false)
  }

  /**
   * 处理确认重置
   */
  const handleConfirm = async () => {
    if (!props.userData) return

    try {
      loading.value = true

      // 如果是自定义密码，需要验证表单
      if (formData.value.resetMode === 'custom') {
        await formRef.value?.validate()
      }

      // 确定要使用的密码
      const passwordToReset =
        formData.value.resetMode === 'custom' ? formData.value.password : defaultPassword.value

      // 调用重置密码API
      await resetUserPassword(props.userData.id, { password: passwordToReset })

      ElMessage.success($t('user.resetPasswordSuccess', '密码重置成功'))
      emit('success')
      handleClose()
    } catch (error) {
      console.error('重置密码失败:', error)
      ElMessage.error($t('user.resetPasswordFailed', '重置密码失败'))
    } finally {
      loading.value = false
    }
  }

  // 监听对话框显示状态，重置表单
  watch(
    () => props.visible,
    (visible) => {
      if (visible) {
        formData.value = {
          resetMode: 'default',
          password: '',
          confirmPassword: ''
        }
      }
    }
  )
</script>

<style scoped>
  :deep(.el-dialog__header) {
    padding: 20px 20px 10px 20px;
  }

  :deep(.el-dialog__body) {
    padding: 0 20px 20px 20px;
  }

  :deep(.el-dialog__footer) {
    padding: 20px;
    border-top: 1px solid #ebeef5;
  }

  :deep(.el-radio-group) {
    width: 100%;
  }

  :deep(.el-radio) {
    margin-right: 20px;
    white-space: nowrap;
  }
</style>
