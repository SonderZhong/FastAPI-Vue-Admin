<template>
  <div class="login register">
    <LoginLeftView></LoginLeftView>
    <div class="right-wrap">
      <div class="top-right-wrap">
        <div class="btn theme-btn" @click="themeAnimation">
          <i class="iconfont-sys">
            {{ isDark ? '&#xe6b5;' : '&#xe725;' }}
          </i>
        </div>
        <ElDropdown @command="changeLanguage" popper-class="langDropDownStyle">
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
          <h3 class="title">{{ $t('register.title') }}</h3>
          <p class="sub-title">{{ $t('register.subTitle') }}</p>

          <!-- 检查注册是否启用 -->
          <div v-if="!authStore.register_enabled" class="register-disabled">
            <ElAlert
              :title="$t('auth.registerDisabled')"
              type="warning"
              :closable="false"
              show-icon
            />
            <div class="footer" style="margin-top: 20px">
              <p>
                {{ $t('register.hasAccount') }}
                <RouterLink :to="RoutesAlias.Login">{{ $t('register.toLogin') }}</RouterLink>
              </p>
            </div>
            <RouterLink :to="RoutesAlias.Login" class="back-to-login">
              <ElButton class="login-btn" type="primary">
                {{ $t('register.toLogin') }}
              </ElButton>
            </RouterLink>
          </div>

          <ElForm
            v-else
            ref="formRef"
            :model="formData"
            :rules="rules"
            label-position="top"
            @keyup.enter="handleSubmit"
            :validate-on-rule-change="false"
          >
            <!-- 步骤指示器 -->
            <div class="step-indicator">
              <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
                <div class="step-number">1</div>
                <div class="step-label">基本信息</div>
              </div>
              <div class="step-divider"></div>
              <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
                <div class="step-number">2</div>
                <div class="step-label">附加信息</div>
              </div>
            </div>

            <!-- 第一步：基本信息 -->
            <div v-if="currentStep === 1" class="step-content">
              <!-- 用户名 -->
              <ElFormItem
                prop="username"
                :label="$t('register.username')"
                :show-message="showValidation"
              >
                <ElInput
                  v-model.trim="formData.username"
                  :placeholder="$t('register.placeholder[0]')"
                />
              </ElFormItem>

              <!-- 密码 -->
              <ElFormItem
                prop="password"
                :label="$t('register.password')"
                :show-message="showValidation"
              >
                <ElInput
                  v-model.trim="formData.password"
                  :placeholder="$t('register.placeholder[1]')"
                  type="password"
                  autocomplete="off"
                  show-password
                />
              </ElFormItem>

              <!-- 确认密码 -->
              <ElFormItem
                prop="confirmPassword"
                :label="$t('register.confirmPassword')"
                :show-message="showValidation"
              >
                <ElInput
                  v-model.trim="formData.confirmPassword"
                  :placeholder="$t('register.placeholder[2]')"
                  type="password"
                  autocomplete="off"
                  show-password
                />
              </ElFormItem>

              <!-- 邮箱 -->
              <ElFormItem prop="email" :label="$t('register.email')" :show-message="showValidation">
                <ElInput
                  v-model.trim="formData.email"
                  :placeholder="$t('register.placeholder[3]')"
                  type="email"
                />
              </ElFormItem>

              <div class="step-actions">
                <ElButton class="next-btn" type="primary" @click="nextStep"> 下一步 </ElButton>
              </div>
            </div>

            <!-- 第二步：附加信息 -->
            <div v-if="currentStep === 2" class="step-content">
              <!-- 手机号 (可选) -->
              <ElFormItem prop="phone" :label="$t('register.phone')" :show-message="showValidation">
                <ElInput
                  v-model.trim="formData.phone"
                  :placeholder="$t('register.placeholder[4]')"
                />
              </ElFormItem>

              <!-- 昵称 (可选) -->
              <ElFormItem
                prop="nickname"
                :label="$t('register.nickname')"
                :show-message="showValidation"
              >
                <ElInput
                  v-model.trim="formData.nickname"
                  :placeholder="$t('register.placeholder[5]')"
                />
              </ElFormItem>

              <!-- 性别 (可选) -->
              <ElFormItem
                prop="gender"
                :label="$t('register.gender')"
                :show-message="showValidation"
              >
                <ElSelect
                  v-model="formData.gender"
                  :placeholder="$t('register.placeholder[6]')"
                  class="gender-select"
                >
                  <ElOption :label="$t('auth.genderOptions.male')" :value="1" />
                  <ElOption :label="$t('auth.genderOptions.female')" :value="2" />
                  <ElOption :label="$t('auth.genderOptions.unknown')" :value="0" />
                </ElSelect>
              </ElFormItem>

              <!-- 邮箱验证码 -->
              <ElFormItem
                prop="code"
                :label="$t('register.emailCode')"
                :show-message="showValidation"
              >
                <div class="email-code-input">
                  <ElInput
                    v-model.trim="formData.code"
                    :placeholder="$t('register.placeholder[8]')"
                    maxlength="6"
                    class="code-input"
                  />
                  <ElButton
                    @click="getEmailCode"
                    :loading="emailCodeLoading"
                    :disabled="emailCodeCountdown > 0 || !formData.email"
                    class="get-code-btn"
                  >
                    {{
                      emailCodeCountdown > 0
                        ? $t('register.getCodeCountdown', { 0: emailCodeCountdown })
                        : $t('register.getCode')
                    }}
                  </ElButton>
                </div>
              </ElFormItem>

              <!-- 协议同意 -->
              <ElFormItem prop="agreement" :show-message="showValidation">
                <ElCheckbox v-model="formData.agreement">
                  {{ $t('register.agreeText') }}
                  <router-link
                    style="color: var(--main-color); text-decoration: none"
                    to="/privacy-policy"
                    >{{ $t('register.privacyPolicy') }}
                  </router-link>
                </ElCheckbox>
              </ElFormItem>

              <div class="step-actions">
                <ElButton class="back-btn" @click="prevStep"> 上一步 </ElButton>
                <ElButton
                  class="register-btn"
                  type="primary"
                  @click="register"
                  :loading="loading"
                  v-ripple
                >
                  {{ $t('register.submitBtnText') }}
                </ElButton>
              </div>
            </div>

            <div class="footer" v-if="currentStep === 1">
              <p>
                {{ $t('register.hasAccount') }}
                <RouterLink :to="RoutesAlias.Login" class="to-login-link">{{
                  $t('register.toLogin')
                }}</RouterLink>
              </p>
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
  import { useAuthStore } from '@/store/modules/auth'
  import { useUserStore } from '@/store/modules/user'
  import { languageOptions } from '@/locales'
  import { LanguageEnum } from '@/enums/appEnum'
  import { themeAnimation } from '@/utils/theme/animation'
  import { fetchCaptcha, fetchEmailCode, fetchRegister } from '@/api/auth'
  import { useI18n } from 'vue-i18n'
  import { useSettingStore } from '@/store/modules/setting'

  defineOptions({ name: 'Register' })

  const { t, locale } = useI18n()

  const router = useRouter()
  const formRef = ref<FormInstance>()

  const authStore = useAuthStore()
  const userStore = useUserStore()
  const settingStore = useSettingStore()
  const { isDark } = storeToRefs(settingStore)

  const systemName = AppConfig.systemInfo.name
  const loading = ref(false)
  const emailCodeLoading = ref(false)
  const emailCodeCountdown = ref(0)
  const currentStep = ref(1)
  const showValidation = ref(false) // 控制验证提示显示

  const formData = reactive({
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    phone: '',
    nickname: '',
    gender: 0,
    code: '',
    agreement: false
  })

  // 验证规则
  const validatePass = (rule: any, value: string, callback: any) => {
    if (value === '') {
      callback(new Error(t('register.validation.passwordRequired')))
    } else if (value.length < 6) {
      callback(new Error(t('register.validation.passwordLength')))
    } else {
      if (formData.confirmPassword !== '') {
        formRef.value?.validateField('confirmPassword')
      }
      callback()
    }
  }

  const validatePass2 = (rule: any, value: string, callback: any) => {
    if (value === '') {
      callback(new Error(t('register.validation.confirmPasswordRequired')))
    } else if (value !== formData.password) {
      callback(new Error(t('register.validation.passwordMismatch')))
    } else {
      callback()
    }
  }

  const validateEmail = (rule: any, value: string, callback: any) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (value === '') {
      callback(new Error(t('register.validation.emailRequired')))
    } else if (!emailRegex.test(value)) {
      callback(new Error(t('register.validation.emailFormat')))
    } else {
      callback()
    }
  }

  const validatePhone = (rule: any, value: string, callback: any) => {
    if (value && !/^1[3-9]\d{9}$/.test(value)) {
      callback(new Error(t('register.validation.phoneFormat')))
    } else {
      callback()
    }
  }

  const rules = computed<FormRules>(() => ({
    username: [
      { required: true, message: t('register.validation.usernameRequired'), trigger: 'blur' },
      { min: 3, max: 20, message: t('register.validation.usernameLength'), trigger: 'blur' }
    ],
    password: [{ required: true, validator: validatePass, trigger: 'blur' }],
    confirmPassword: [{ required: true, validator: validatePass2, trigger: 'blur' }],
    email: [{ required: true, validator: validateEmail, trigger: 'blur' }],
    phone: [{ validator: validatePhone, trigger: 'blur' }],
    code: [
      { required: true, message: t('register.validation.emailCodeRequired'), trigger: 'blur' },
      { len: 6, message: t('register.validation.emailCodeLength'), trigger: 'blur' }
    ],
    agreement: [
      {
        validator: (rule: any, value: boolean, callback: any) => {
          if (!value) {
            callback(new Error(t('register.rule[4]')))
          } else {
            callback()
          }
        },
        trigger: 'change'
      }
    ]
  }))

  onMounted(async () => {
    // 初始化系统配置
    await initSystemConfig()
  })

  /**
   * 初始化系统配置
   */
  const initSystemConfig = async () => {
    try {
      const response = await fetchCaptcha()

      // 检查响应是否成功
      if (!response.success || !response.data) {
        throw new Error(response.msg || '获取系统配置失败')
      }

      const captchaData = response.data
      authStore.setSystemConfig({
        captcha_enabled: captchaData.captcha_enabled,
        register_enabled: captchaData.register_enabled
      })
    } catch (error) {
      console.error('Failed to load system config:', error)
    }
  }

  /**
   * 获取邮箱验证码
   */
  const getEmailCode = async () => {
    if (!formData.email) {
      ElMessage.error(t('register.validation.emailRequired'))
      return
    }

    // 验证邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      ElMessage.error(t('register.validation.emailFormat'))
      return
    }

    try {
      emailCodeLoading.value = true

      const response = await fetchEmailCode({
        username: formData.username || formData.email,
        title: '注册验证码',
        mail: formData.email
      })

      // 检查响应是否成功
      if (!response.success) {
        throw new Error(response.msg || '发送验证码失败')
      }

      ElMessage.success(response.msg || '验证码已发送至您的邮箱，请注意查收')
      startCountdown()
    } catch (error: any) {
      ElMessage.error(error.message || '发送验证码失败，请稍后重试')
      console.error('Failed to send email code:', error)
    } finally {
      emailCodeLoading.value = false
    }
  }

  /**
   * 开始倒计时
   */
  const startCountdown = () => {
    emailCodeCountdown.value = 60
    const timer = setInterval(() => {
      emailCodeCountdown.value--
      if (emailCodeCountdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  }

  /**
   * 下一步
   */
  const nextStep = async () => {
    if (!formRef.value) return

    try {
      // 启用验证提示
      showValidation.value = true

      // 验证第一步的字段
      await formRef.value.validateField(['username', 'password', 'confirmPassword', 'email'])
      currentStep.value = 2
    } catch (error) {
      console.log('第一步验证失败:', error)
    }
  }

  /**
   * 上一步
   */
  const prevStep = () => {
    currentStep.value = 1
  }

  /**
   * 处理提交
   */
  const handleSubmit = () => {
    if (currentStep.value === 1) {
      nextStep()
    } else {
      register()
    }
  }

  /**
   * 注册函数
   */
  const register = async () => {
    if (!formRef.value) return

    try {
      // 启用验证提示
      showValidation.value = true

      await formRef.value.validate()
      loading.value = true

      const registerParams: any = {
        username: formData.username,
        password: formData.password,
        email: formData.email,
        code: formData.code
      }

      // 添加可选字段
      if (formData.phone) registerParams.phone = formData.phone
      if (formData.nickname) registerParams.nickname = formData.nickname
      if (formData.gender !== undefined) registerParams.gender = formData.gender

      const response = await fetchRegister(registerParams)

      // 检查响应是否成功
      if (!response.success) {
        throw new Error(response.msg || '注册失败')
      }

      ElNotification({
        title: t('register.success.title'),
        message: response.msg || t('register.success.message'),
        type: 'success',
        duration: 3000
      })

      // 注册成功后跳转到登录页
      setTimeout(() => {
        router.push(RoutesAlias.Login)
      }, 1500)
    } catch (error: any) {
      ElMessage.error(error.message || '注册失败，请稍后重试')
      console.log('注册失败:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 切换语言
   */
  const changeLanguage = (lang: LanguageEnum) => {
    if (locale.value === lang) return
    locale.value = lang
    userStore.setLanguage(lang)
  }
</script>

<style lang="scss" scoped>
  @use '../login/index' as login;
  @use './index' as register;
</style>
