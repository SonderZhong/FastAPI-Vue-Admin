import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 认证状态管理
 * 管理验证码、注册配置等认证相关状态
 */
export const useAuthStore = defineStore(
  'authStore',
  () => {
    // 验证码是否启用
    const captcha_enabled = ref(false)
    // 注册是否启用
    const register_enabled = ref(false)
    // 验证码UUID
    const captcha_uuid = ref<string | null>(null)
    // 验证码图片
    const captcha_image = ref<string | null>(null)
    // 验证码类型：0=算术题，1=字母数字
    const captcha_type = ref<string>('0')
    /**
     * 设置验证码数据
     * @param data 验证码数据
     */
    const setCaptchaData = (data: {
      uuid: string | null
      captcha: string | null
      type?: string
    }) => {
      captcha_uuid.value = data.uuid
      captcha_image.value = data.captcha
      if (data.type !== undefined) {
        captcha_type.value = data.type
      }
    }

    /**
     * 设置系统配置
     * @param config 系统配置
     */
    const setSystemConfig = (config: {
      captcha_enabled: boolean
      register_enabled: boolean
      captcha_type?: string
    }) => {
      captcha_enabled.value = config.captcha_enabled
      register_enabled.value = config.register_enabled
      if (config.captcha_type !== undefined) {
        captcha_type.value = config.captcha_type
      }
    }

    /**
     * 清空验证码数据
     */
    const clearCaptchaData = () => {
      captcha_uuid.value = null
      captcha_image.value = null
    }

    return {
      captcha_enabled,
      register_enabled,
      captcha_uuid,
      captcha_image,
      captcha_type,
      setCaptchaData,
      setSystemConfig,
      clearCaptchaData
    }
  },
  {
    persist: false // 认证相关状态不需要持久化
  }
)
