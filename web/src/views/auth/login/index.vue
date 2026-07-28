<template>
  <div class="login">
    <LoginLeftView />
    <div class="right-wrap">
      <div class="top-right-wrap">
        <div v-if="shouldShowThemeToggle" class="btn theme-btn" @click="themeAnimation">
          <i class="iconfont-sys">{{ isDark ? '&#xe6b5;' : '&#xe725;' }}</i>
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
          <h3 class="title">{{ t('login.title') }}</h3>
          <p class="sub-title">{{ t('login.subTitle') }}</p>
          <ElForm
            ref="formRef"
            :model="formData"
            :rules="rules"
            @keyup.enter="handleSubmit"
            :validate-on-rule-change="false"
          >
            <ElFormItem prop="username" :show-message="showValidation">
              <ElInput v-model.trim="formData.username" :placeholder="t('login.username')" />
            </ElFormItem>
            <ElFormItem prop="password" :show-message="showValidation">
              <ElInput
                v-model.trim="formData.password"
                type="password"
                autocomplete="off"
                show-password
                :placeholder="t('login.password')"
              />
            </ElFormItem>
            <ElFormItem v-if="authStore.captcha_enabled" prop="code" :show-message="showValidation">
              <ArtCaptcha
                v-model="formData.code"
                :uuid="authStore.captcha_uuid || ''"
                :captcha-image="authStore.captcha_image || ''"
                :placeholder="t('login.captcha')"
                @refresh="refreshCaptcha"
                class="full-width-captcha"
              />
            </ElFormItem>
            <div class="login-options-row">
              <ElCheckbox v-model="formData.rememberPassword">{{
                t('login.rememberPwd')
              }}</ElCheckbox>
              <div class="login-days-wrapper">
                <span class="login-days-label">{{ t('login.loginDays') }}</span>
                <ElSelect
                  v-model="formData.login_days"
                  :key="locale"
                  class="login-days-select"
                  :teleported="true"
                  popper-class="login-days-dropdown"
                  placement="bottom-end"
                  suffix-icon=""
                  :popper-options="{ strategy: 'fixed' }"
                >
                  <ElOption
                    v-for="option in loginDaysOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </ElSelect>
              </div>
            </div>
            <ElButton
              class="login-btn"
              type="primary"
              @click="handleSubmit"
              :loading="loading"
              v-ripple
              >{{ t('login.btnText') }}</ElButton
            >
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

  const { t, locale } = useI18n()
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
    login_days: 7,
    rememberPassword: true
  })
  const loginDaysOptions = computed(() => [
    { label: t('login.loginDaysOptions.one'), value: 1 },
    { label: t('login.loginDaysOptions.three'), value: 3 },
    { label: t('login.loginDaysOptions.seven'), value: 7 },
    { label: t('login.loginDaysOptions.fifteen'), value: 15 },
    { label: t('login.loginDaysOptions.thirty'), value: 30 }
  ])
  const rules = computed<FormRules>(() => ({
    username: [
      { required: true, message: t('login.validation.usernameRequired'), trigger: 'blur' },
      { min: 3, max: 50, message: t('login.validation.usernameLength'), trigger: 'blur' }
    ],
    password: [
      { required: true, message: t('login.validation.passwordRequired'), trigger: 'blur' },
      { min: 6, message: t('login.validation.passwordLength'), trigger: 'blur' }
    ],
    code: authStore.captcha_enabled
      ? [{ required: true, message: t('login.validation.captchaRequired'), trigger: 'blur' }]
      : []
  }))
  const loading = ref(false)
  const showValidation = ref(false)

  const initCaptcha = async () => {
    try {
      const response = await fetchCaptcha()
      if (!response.success || !response.data) throw new Error(t('login.errors.captchaLoadFailed'))
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
      console.error(error)
    }
  }

  const refreshCaptcha = async () => {
    await initCaptcha()
    formData.code = ''
  }

  onMounted(initCaptcha)

  const handleSubmit = async () => {
    if (!formRef.value) return
    try {
      showValidation.value = true
      if (!(await formRef.value.validate())) return
      loading.value = true
      const loginParams: any = {
        username: formData.username,
        password: formData.password,
        login_days: formData.login_days
      }
      if (authStore.captcha_enabled) {
        loginParams.code = formData.code
        loginParams.uuid = authStore.captcha_uuid || undefined
      }
      const loginResponse = await fetchLogin(loginParams)
      if (!loginResponse.success || !loginResponse.data)
        throw new Error(loginResponse.msg || t('login.errors.loginFailed'))
      const { accessToken, refreshToken, available_tenants = [] } = loginResponse.data
      if (!accessToken) throw new Error(t('login.errors.tokenMissing'))
      userStore.setToken(accessToken, refreshToken)

      if (available_tenants.length > 1) {
        userStore.setAvailableTenants(available_tenants)
        userStore.setNeedSelectTenant(true)
        userStore.setLoginStatus(false)
        ElMessage.info(t('login.errors.multipleTenants'))
        router.push(RoutesAlias.SelectTenant)
        return
      }

      const userInfoResponse = await fetchGetUserInfo()
      if (!userInfoResponse.success || !userInfoResponse.data)
        throw new Error(userInfoResponse.msg || t('login.errors.userInfoFailed'))
      userStore.setUserInfo(userInfoResponse.data)
      userStore.setLoginStatus(true)
      userStore.setAvailableTenants(available_tenants)
      userStore.setNeedSelectTenant(false)
      setTimeout(() => {
        ElNotification({
          title: t('login.success.title'),
          type: 'success',
          duration: 2500,
          zIndex: 10000,
          message: `${t('login.success.message')}, ${useUserStore().info.username}-${useUserStore().info.nickname}!`
        })
      }, 150)
      router.push('/')
    } catch (error) {
      if (authStore.captcha_enabled) await refreshCaptcha()
      if (error instanceof HttpError) {
        console.error('[Login] HttpError:', error.message)
        ElMessage.error(error.message || t('login.errors.loginFailed'))
      } else {
        ElMessage.error((error as Error)?.message || t('login.errors.loginRetry'))
      }
    } finally {
      loading.value = false
    }
  }

  const changeLanguage = (lang: LanguageEnum) => {
    if (locale.value === lang) return
    locale.value = lang
    userStore.setLanguage(lang)
  }
</script>

<style lang="scss" scoped>
  @use './index';
</style>
