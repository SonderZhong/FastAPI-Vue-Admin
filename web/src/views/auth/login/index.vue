<template>
  <div class="login">
    <LoginLeftView></LoginLeftView>

    <div class="right-wrap">
      <div class="top-right-wrap">
        <div v-if="shouldShowThemeToggle" class="btn theme-btn" @click="themeAnimation">
          <i class="iconfont-sys">
            {{ isDark ? '&#xe6b5;' : '&#xe725;' }}
          </i>
        </div>
        <ElDropdown
          v-if="shouldShowLanguage"
          @command="changeLanguage"
          popper-class="langDropDownStyle"
        >
          <div class="btn language-btn">
            <i class="iconfont-sys icon-language">&#xe611;</i>
          </div>
          <template #dropdown>
            <ElDropdownMenu>
              <div v-for="lang in languageOptions" :key="lang.value" class="lang-btn-item">
                <ElDropdownItem
                  :command="lang.value"
                  :class="{ 'is-selected': locale === lang.value }"
                >
                  <span class="menu-txt">{{ lang.label }}</span>
                  <i v-if="locale === lang.value" class="iconfont-sys icon-check">&#xe621;</i>
                </ElDropdownItem>
              </div>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
      <div class="header">
        <ArtLogo class="icon" />
        <h1>{{ systemName }}</h1>
      </div>
      <div class="login-wrap">
        <div class="form">
          <h3 class="title">{{ $t('login.title') }}</h3>
          <p class="sub-title">{{ $t('login.subTitle') }}</p>
          <ElForm
            ref="formRef"
            :model="formData"
            :rules="rules"
            @keyup.enter="handleSubmit"
            style="margin-top: 25px"
            :validate-on-rule-change="false"
          >
            <ElFormItem prop="username" :show-message="showValidation">
              <ElInput :placeholder="$t('login.username')" v-model.trim="formData.username" />
            </ElFormItem>
            <ElFormItem prop="password" :show-message="showValidation">
              <ElInput
                :placeholder="$t('login.password')"
                v-model.trim="formData.password"
                type="password"
                radius="8px"
                autocomplete="off"
                show-password
              />
            </ElFormItem>

            <!-- 验证码 -->
            <ElFormItem v-if="authStore.captcha_enabled" prop="code" :show-message="showValidation">
              <ArtCaptcha
                v-model="formData.code"
                :uuid="authStore.captcha_uuid || ''"
                :captcha-image="authStore.captcha_image || ''"
                :placeholder="$t('login.captcha')"
                @refresh="refreshCaptcha"
                class="full-width-captcha"
              />
            </ElFormItem>

            <!-- 记住密码和登录有效期 -->
            <div class="login-options-row">
              <ElCheckbox v-model="formData.rememberPassword">
                {{ $t('login.rememberPwd') }}
              </ElCheckbox>
              <div class="login-days-wrapper">
                <span class="login-days-label">{{ $t('login.loginDays') }}</span>
                <ElSelect
                  v-model="formData.login_days"
                  class="login-days-select"
                  ref="daysSelectRef"
                  :teleported="true"
                  popper-class="login-days-dropdown"
                  placement="bottom-end"
                  suffix-icon=""
                  :popper-options="{ strategy: 'fixed' }"
                >
                  <ElOption
                    v-for="option in authStore.login_days_options"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </ElSelect>
              </div>
            </div>

            <div style="margin-top: 30px">
              <ElButton
                class="login-btn"
                type="primary"
                @click="handleSubmit"
                :loading="loading"
                v-ripple
              >
                {{ $t('login.btnText') }}
              </ElButton>
            </div>

            <div class="footer">
              <div class="auth-links" :class="{ 'single-link': !authStore.register_enabled }">
                <!-- 注册相关链接，仅在注册开启时显示 -->
                <div v-if="authStore.register_enabled" class="register-section">
                  <span>{{ $t('login.noAccount') }}</span>
                  <RouterLink :to="RoutesAlias.Register" class="register-link">
                    {{ $t('login.register') }}
                  </RouterLink>
                </div>
                <!-- 忘记密码链接，始终显示 -->
                <RouterLink :to="RoutesAlias.ForgetPassword" class="forget-link">
                  {{ $t('login.forgetPwd') }}
                </RouterLink>
              </div>
            </div>
          </ElForm>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import AppConfig from '@/config'
  import { RoutesAlias } from '@/router/routesAlias'
  import type { FormInstance, FormRules } from 'element-plus'
  import { ElMessage, ElNotification } from 'element-plus'
  import { useUserStore } from '@/store/modules/user'
  import { useAuthStore } from '@/store/modules/auth'
  import { languageOptions } from '@/locales'
  import { LanguageEnum } from '@/enums/appEnum'
  import { useI18n } from 'vue-i18n'
  import { HttpError } from '@/utils/http/error'
  import { themeAnimation } from '@/utils/theme/animation'
  import { fetchCaptcha, fetchGetUserInfo, fetchLogin } from '@/api/auth'
  import { useSettingStore } from '@/store/modules/setting'
  import { useHeaderBar } from '@/composables/useHeaderBar'

  defineOptions({ name: 'Login' })

  const { t } = useI18n()

  const settingStore = useSettingStore()
  const { isDark } = storeToRefs(settingStore)
  const { shouldShowThemeToggle, shouldShowLanguage } = useHeaderBar()

  const userStore = useUserStore()
  const authStore = useAuthStore()
  const router = useRouter()

  const systemName = AppConfig.systemInfo.name
  const formRef = ref<FormInstance>()

  const formData = reactive({
    username: '',
    password: '',
    code: '',
    login_days: 7, // 默认7天
    rememberPassword: true
  })

  const rules = computed<FormRules>(() => {
    // 根据验证码类型动态设置验证规则
    const getCaptchaRules = () => {
      if (!authStore.captcha_enabled) return []

      const baseRules = [
        { required: true, message: t('login.validation.captchaRequired'), trigger: 'blur' }
      ]

      // 验证码类型：0=算术题，1=字母数字
      if (authStore.captcha_type === '0') {
        // 算术题验证码：验证是否为数字（可能是负数）
        baseRules.push({
          pattern: /^-?\d+$/,
          message: t('login.validation.captchaMathResult'),
          trigger: 'blur'
        } as any)
      } else {
        // 字母数字验证码：固定4位长度
        baseRules.push({
          len: 4,
          message: t('login.validation.captchaLength'),
          trigger: 'blur'
        } as any)
      }

      return baseRules
    }

    return {
      username: [
        { required: true, message: t('login.validation.usernameRequired'), trigger: 'blur' },
        { min: 3, max: 50, message: t('login.validation.usernameLength'), trigger: 'blur' }
      ],
      password: [
        { required: true, message: t('login.validation.passwordRequired'), trigger: 'blur' },
        { min: 6, message: t('login.validation.passwordLength'), trigger: 'blur' }
      ],
      code: getCaptchaRules()
    }
  })

  const loading = ref(false)
  const daysSelectRef = ref<any>(null)
  const showValidation = ref(false) // 控制验证提示显示

  onMounted(async () => {
    // 初始化验证码
    await initCaptcha()
  })

  /**
   * 初始化验证码
   */
  const initCaptcha = async () => {
    try {
      const response = await fetchCaptcha()

      // 检查响应是否成功
      if (!response.success || !response.data) {
        throw new Error(response.msg || '获取验证码失败')
      }

      const captchaData = response.data
      authStore.setSystemConfig({
        captcha_enabled: captchaData.captcha_enabled,
        register_enabled: captchaData.register_enabled,
        captcha_type: captchaData.captcha_type
      })
      if (captchaData.captcha_enabled) {
        authStore.setCaptchaData({
          uuid: captchaData.uuid,
          captcha: captchaData.captcha,
          type: captchaData.captcha_type
        })
      }
    } catch (error) {
      console.error('Failed to load captcha:', error)
    }
  }

  /**
   * 刷新验证码
   */
  const refreshCaptcha = async () => {
    await initCaptcha()
    formData.code = '' // 清空验证码输入
  }

  // 登录
  const handleSubmit = async () => {
    if (!formRef.value) return

    try {
      // 启用验证提示
      showValidation.value = true

      // 表单验证
      const valid = await formRef.value.validate()
      if (!valid) return

      loading.value = true

      // 登录请求
      const { username, password, code, login_days } = formData
      const loginParams: any = {
        username,
        password,
        login_days
      }

      // 如果验证码启用，添加验证码参数
      if (authStore.captcha_enabled) {
        loginParams.code = code
        loginParams.uuid = authStore.captcha_uuid || undefined
      }

      const loginResponse = await fetchLogin(loginParams)

      // 检查响应是否成功
      if (!loginResponse.success || !loginResponse.data) {
        throw new Error(loginResponse.msg || 'Login failed')
      }

      const { accessToken, refreshToken } = loginResponse.data

      // 验证token
      if (!accessToken) {
        throw new Error('Login failed - no token received')
      }

      // 存储token和用户信息
      userStore.setToken(accessToken, refreshToken)
      const userInfoResponse = await fetchGetUserInfo()

      // 检查用户信息响应是否成功
      if (!userInfoResponse.success || !userInfoResponse.data) {
        throw new Error(userInfoResponse.msg || 'Failed to get user info')
      }

      userStore.setUserInfo(userInfoResponse.data)
      userStore.setLoginStatus(true)

      // 登录成功处理
      showLoginSuccessNotice()
      router.push('/')
    } catch (error) {
      // 登录失败时刷新验证码
      if (authStore.captcha_enabled) {
        refreshCaptcha()
      }
      
      // 处理 HttpError
      if (error instanceof HttpError) {
        // HttpError 已经在拦截器中处理了消息提示
        console.error('[Login] HttpError:', error.message)
      } else {
        // 处理非 HttpError
        ElMessage.error('登录失败，请稍后重试')
        console.error('[Login] Unexpected error:', error)
      }
    } finally {
      loading.value = false
    }
  }

  // 登录成功提示
  const showLoginSuccessNotice = () => {
    setTimeout(() => {
      ElNotification({
        title: t('login.success.title'),
        type: 'success',
        duration: 2500,
        zIndex: 10000,
        message: `${t('login.success.message')}, ${useUserStore().info.username}-${useUserStore().info.nickname}!`
      })
    }, 150)
  }

  // 监听表单输入，用户开始输入后才显示验证提示
  watch(
    () => [formData.username, formData.password, formData.code],
    () => {
      // 用户开始输入后，启用验证提示
      if ((formData.username || formData.password || formData.code) && !showValidation.value) {
        showValidation.value = true
      }
    },
    { deep: true }
  )

  // 切换语言
  const { locale } = useI18n()

  const changeLanguage = (lang: LanguageEnum) => {
    if (locale.value === lang) return
    locale.value = lang
    userStore.setLanguage(lang)
  }
</script>

<style lang="scss" scoped>
  @use './index';
</style>
