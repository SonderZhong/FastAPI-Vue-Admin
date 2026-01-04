<template>
  <div class="art-captcha">
    <div class="captcha-input-wrapper">
      <ElInput
        :model-value="modelValue"
        @input="handleInput"
        :placeholder="placeholder"
        :disabled="disabled"
        maxlength="10"
        class="captcha-input"
        @keyup.enter="$emit('enter')"
      >
        <template #suffix>
          <div class="captcha-image-wrapper" @click="refreshCaptcha">
            <img
              v-if="captchaImageUrl"
              :src="captchaImageUrl"
              class="captcha-image"
              :alt="t('auth.captcha')"
            />
            <div v-else class="captcha-placeholder">
              <i class="el-icon-picture"></i>
              <span>{{ t('auth.clickToRefresh') }}</span>
            </div>
          </div>
        </template>
      </ElInput>
    </div>
    <ElButton
      v-if="showRefreshButton"
      @click="refreshCaptcha"
      :loading="loading"
      type="text"
      class="refresh-button"
    >
      <i class="iconfont-sys">&#xe6a7;</i>
      {{ t('auth.refreshCaptcha') }}
    </ElButton>
  </div>
</template>

<script setup lang="ts">
  import { useI18n } from 'vue-i18n'

  defineOptions({ name: 'ArtCaptcha' })

  interface Props {
    /** v-model绑定值 */
    modelValue: string
    /** 验证码UUID */
    uuid: string
    /** 验证码图片 */
    captchaImage: string
    /** 是否禁用 */
    disabled?: boolean
    /** 输入框占位符 */
    placeholder?: string
    /** 是否显示刷新按钮 */
    showRefreshButton?: boolean
    /** 加载状态 */
    loading?: boolean
  }

  interface Emits {
    /** 更新modelValue */
    (e: 'update:modelValue', value: string): void

    /** 刷新验证码 */
    (e: 'refresh'): void

    /** 回车事件 */
    (e: 'enter'): void
  }

  const props = withDefaults(defineProps<Props>(), {
    disabled: false,
    placeholder: '',
    showRefreshButton: false,
    loading: false
  })

  const emit = defineEmits<Emits>()

  const { t } = useI18n()

  /**
   * 计算属性：完整的验证码图片URL
   */
  const captchaImageUrl = computed(() => {
    if (!props.captchaImage) return ''

    // 如果已经是data URL格式，直接返回
    if (props.captchaImage.startsWith('data:')) {
      return props.captchaImage
    }

    // 否则添加base64前缀
    return `data:image/png;base64,${props.captchaImage}`
  })

  /**
   * 处理输入
   * 支持两种验证码类型：
   * 1. 算术题验证码：允许数字和负号（如 -3, 15, 8）
   * 2. 字母数字验证码：允许字母和数字（如 A7k9）
   */
  const handleInput = (value: string) => {
    // 允许输入字母、数字和负号（用于算术题验证码）
    // 负号只能出现在开头
    let filteredValue = value.replace(/[^a-zA-Z0-9-]/g, '')
    
    // 如果有多个负号，只保留第一个，且必须在开头
    if (filteredValue.includes('-')) {
      const firstMinusIndex = filteredValue.indexOf('-')
      // 移除所有负号
      filteredValue = filteredValue.replace(/-/g, '')
      // 如果第一个负号在开头，则保留
      if (firstMinusIndex === 0) {
        filteredValue = '-' + filteredValue
      }
    }
    
    emit('update:modelValue', filteredValue)
  }

  /**
   * 刷新验证码
   */
  const refreshCaptcha = () => {
    if (props.disabled || props.loading) return
    emit('refresh')
  }
</script>

<style lang="scss" scoped>
  .art-captcha {
    display: flex;
    align-items: center;
    gap: 0;
    width: 100%;

    .captcha-input-wrapper {
      flex: 1;
      width: 100%;
      min-width: 0; // 确保可以完全收缩

      .captcha-input {
        width: 100%;

        :deep(.el-input__wrapper) {
          width: 100%;
        }

        :deep(.el-input__suffix) {
          padding-right: 0;
          width: 80px;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0; // 防止被压缩
        }

        :deep(.el-input__inner) {
          padding-right: 88px; // 留出验证码图片的空间
          width: 100%;
        }
      }

      .captcha-image-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 80px;
        height: 32px;
        cursor: pointer;
        border: 1px solid var(--el-border-color);
        border-radius: 4px;
        background: var(--el-fill-color-lighter);
        transition: all 0.2s ease;
        flex-shrink: 0; // 防止被压缩

        &:hover {
          border-color: var(--el-color-primary);
          background: var(--el-color-primary-light-9);
        }

        .captcha-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 3px;
        }

        .captcha-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: var(--el-text-color-placeholder);
          font-size: 12px;

          i {
            font-size: 16px;
            margin-bottom: 2px;
          }

          span {
            font-size: 10px;
            text-align: center;
            line-height: 1.2;
          }
        }
      }
    }

    .refresh-button {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 8px 12px;
      font-size: 12px;
      flex-shrink: 0; // 防止被压缩

      i {
        font-size: 14px;
      }
    }
  }
</style>
