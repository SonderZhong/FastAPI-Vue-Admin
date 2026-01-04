<template>
  <div class="login forget-password">
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
          <h3 class="title">{{ $t('forgetPassword.title') }}</h3>
          <p class="sub-title">{{ $t('forgetPassword.subTitle') }}</p>

          <!-- 步骤指示器 -->
          <div class="step-indicator">
            <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
              <div class="step-number">1</div>
              <div class="step-label">{{ $t('forgetPassword.step1') }}</div>
            </div>
            <div class="step-divider"></div>
            <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
              <div class="step-number">2</div>
              <div class="step-label">{{ $t('forgetPassword.step2') }}</div>
            </div>
          </div>

          <!-- 第一步：验证身份 -->
          <ElForm
            v-if="currentStep === 1"
            ref="step1FormRef"
            :model="step1Form"
            :rules="step1Rules"
            @keyup.enter="nextStep"
            :validate-on-rule-change="false"
          >
            <ElFormItem prop="usernameOrEmail" :label="$t('forgetPassword.usernameOrEmail')" :show-message="showValidation">
              <ElInput
                v-model.trim="step1Form.usernameOrEmail"
                :placeholder="$t('forgetPassword.placeholder')"
              />
            </ElFormItem>

            <ElFormItem prop="code" :label="$t('forgetPassword.emailCode')" :show-message="showValidation">
              <div class="email-code-input">
                <ElInput
                  v-model.trim="step1Form.code"
                  :placeholder="$t('register.placeholder[8]')"
                  maxlength="6"
                  class="code-input"
                />
                <ElButton
                  @click="getEmailCode"
                  :loading="emailCodeLoading"
                  :disabled="emailCodeCountdown > 0 || !step1Form.usernameOrEmail"
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

            <div style="margin-top: 30px">
              <ElButton
                class="login-btn"
                type="primary"
                @click="nextStep"
                :loading="loading"
                v-ripple
              >
                {{ $t('forgetPassword.nextStep') }}
              </ElButton>
            </div>
          </ElForm>

          <!-- 第二步：设置新密码 -->
          <ElForm
            v-if="currentStep === 2"
            ref="step2FormRef"
            :model="step2Form"
            :rules="step2Rules"
            @keyup.enter="resetPassword"
            :validate-on-rule-change="false"
          >
            <ElFormItem prop="newPassword" :label="$t('forgetPassword.newPassword')" :show-message="showValidation">
              <ElInput
                v-model.trim="step2Form.newPassword"
                type="password"
                show-password
                autocomplete="new-password"
              />
            </ElFormItem>

            <ElFormItem prop="confirmPassword" :label="$t('forgetPassword.confirmPassword')" :show-message="showValidation">
              <ElInput
                v-model.trim="step2Form.confirmPassword"
                type="password"
                show-password
                autocomplete="new-password"
              />
            </ElFormItem>

            <div style="margin-top: 30px">
              <ElButton
                class="login-btn"
                type="primary"
                @click="resetPassword"
                :loading="loading"
                v-ripple
              >
                {{ $t('forgetPassword.resetPassword') }}
              </ElButton>
            </div>

            <div style="margin-top: 15px">
              <ElButton class="back-btn" plain @click="prevStep">
                {{ $t('forgetPassword.backBtnText') }}
              </ElButton>
            </div>
          </ElForm>

          <!-- 返回登录 -->
          <div class="footer">
            <RouterLink :to="RoutesAlias.Login">
              {{ $t('forgetPassword.backToLogin') }}
            </RouterLink>
          </div>
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
  import { languageOptions } from '@/locales'
  import { LanguageEnum } from '@/enums/appEnum'
  import { themeAnimation } from '@/utils/theme/animation'
  import { fetchEmailCode, fetchForgetPassword } from '@/api/auth'
  import { useI18n } from 'vue-i18n'
  import { useSettingStore } from '@/store/modules/setting'

  defineOptions({ name: 'ForgetPassword' })

  const { t, locale } = useI18n()
  const router = useRouter()

  const userStore = useUserStore()
  const settingStore = useSettingStore()
  const { isDark } = storeToRefs(settingStore)

  const systemName = AppConfig.systemInfo.name
  const loading = ref(false)
  const emailCodeLoading = ref(false)
  const emailCodeCountdown = ref(0)
  const currentStep = ref(1)
  const showValidation = ref(false) // 控制验证提示显示

  const step1FormRef = ref<FormInstance>()
  const step2FormRef = ref<FormInstance>()

  // 第一步表单数据
  const step1Form = reactive({
    usernameOrEmail: '',
    code: ''
  })

  // 第二步表单数据
  const step2Form = reactive({
    newPassword: '',
    confirmPassword: ''
  })

  // 第一步验证规则
  const step1Rules = computed<FormRules>(() => ({
    usernameOrEmail: [
      {
        required: true,
        message: t('forgetPassword.validation.usernameOrEmailRequired'),
        trigger: 'blur'
      }
    ],
    code: [
      {
        required: true,
        message: t('forgetPassword.validation.emailCodeRequired'),
        trigger: 'blur'
      },
      { len: 6, message: t('register.validation.emailCodeLength'), trigger: 'blur' }
    ]
  }))

  // 第二步验证规则
  const validateNewPass = (rule: any, value: string, callback: any) => {
    if (value === '') {
      callback(new Error(t('forgetPassword.validation.newPasswordRequired')))
    } else if (value.length < 6) {
      callback(new Error(t('register.validation.passwordLength')))
    } else {
      if (step2Form.confirmPassword !== '') {
        step2FormRef.value?.validateField('confirmPassword')
      }
      callback()
    }
  }

  const validateConfirmPass = (rule: any, value: string, callback: any) => {
    if (value === '') {
      callback(new Error(t('forgetPassword.validation.confirmPasswordRequired')))
    } else if (value !== step2Form.newPassword) {
      callback(new Error(t('forgetPassword.validation.passwordMismatch')))
    } else {
      callback()
    }
  }

  const step2Rules = computed<FormRules>(() => ({
    newPassword: [{ required: true, validator: validateNewPass, trigger: 'blur' }],
    confirmPassword: [{ required: true, validator: validateConfirmPass, trigger: 'blur' }]
  }))

  /**
   * 获取邮箱验证码
   */
  const getEmailCode = async () => {
    if (!step1Form.usernameOrEmail) {
      ElMessage.error(t('forgetPassword.validation.usernameOrEmailRequired'))
      return
    }

    try {
      emailCodeLoading.value = true

      const response = await fetchEmailCode({
        username: step1Form.usernameOrEmail,
        title: '忘记密码验证码',
        mail: step1Form.usernameOrEmail
      })

      // 检查响应是否成功
      if (!response.success) {
        throw new Error(response.msg || '发送验证码失败')
      }

      ElMessage.success(response.msg || '验证码已发送至您的邮箱，请注意查收')
      startCountdown()
    } catch (error: any) {
      ElMessage.error(error.message || '发送验证码失败，请稍后重试')
      console.error(error)
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
    if (!step1FormRef.value) return

    try {
      // 启用验证提示
      showValidation.value = true
      
      await step1FormRef.value.validate()
      // 这里可以添加验证码校验的API调用
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
   * 重置密码
   */
  const resetPassword = async () => {
    if (!step2FormRef.value) return

    try {
      // 启用验证提示
      showValidation.value = true
      
      await step2FormRef.value.validate()
      loading.value = true

      const resetParams: Auth.ForgetPasswordParams = {
        username: step1Form.usernameOrEmail,
        email: step1Form.usernameOrEmail,
        code: step1Form.code,
        new_password: step2Form.newPassword
      }

      const response = await fetchForgetPassword(resetParams)

      // 检查响应是否成功
      if (!response.success) {
        throw new Error(response.msg || '重置密码失败')
      }

      ElNotification({
        title: t('forgetPassword.success.title'),
        message: response.msg || t('forgetPassword.success.message'),
        type: 'success',
        duration: 3000
      })

      // 重置成功后跳转到登录页
      setTimeout(() => {
        router.push(RoutesAlias.Login)
      }, 2000)
    } catch (error: any) {
      ElMessage.error(error.message || '重置密码失败，请稍后重试')
      console.log('重置密码失败:', error)
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
  @use '../register/index' as register;

  .forget-password {
    .right-wrap {
      .top-right-wrap {
        position: fixed;
        top: 23px;
        right: 30px;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: flex-end;

        .btn {
          display: inline-block;
          padding: 5px;
          margin-left: 15px;
          cursor: pointer;
          user-select: none;
          transition: all 0.3s;

          i {
            font-size: 18px;
          }

          &:hover {
            color: var(--main-color) !important;
          }
        }
      }

      .login-wrap {
        .form {
          .step-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 30px 0;
            gap: 20px;

            .step {
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 8px;

              .step-number {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                border: 2px solid var(--el-border-color);
                background: var(--el-fill-color-lighter);
                color: var(--el-text-color-placeholder);
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
              }

              .step-label {
                font-size: 12px;
                color: var(--el-text-color-placeholder);
                transition: all 0.3s;
              }

              &.active {
                .step-number {
                  border-color: var(--el-color-primary);
                  background: var(--el-color-primary);
                  color: white;
                }

                .step-label {
                  color: var(--el-color-primary);
                  font-weight: 500;
                }
              }

              &.completed {
                .step-number {
                  border-color: var(--el-color-success);
                  background: var(--el-color-success);
                  color: white;
                }

                .step-label {
                  color: var(--el-color-success);
                  font-weight: 500;
                }
              }
            }

            .step-divider {
              flex: 1;
              height: 2px;
              background: var(--el-border-color);
              border-radius: 1px;
              max-width: 60px;
            }
          }

          .email-code-input {
            display: flex;
            gap: 12px;

            .code-input {
              flex: 1;
            }

            .get-code-btn {
              flex-shrink: 0;
              width: 120px;
              height: 40px;
            }
          }

          .login-btn {
            width: 100%;
            height: 40px !important;
          }

          .back-btn {
            width: 100%;
            height: 40px !important;
          }

          .footer {
            margin-top: 30px;
            text-align: center;

            a {
              color: var(--main-color);
              text-decoration: none;
              font-size: 14px;

              &:hover {
                text-decoration: underline;
              }
            }
          }
        }
      }
    }

    @media only screen and (max-width: 768px) {
      .right-wrap {
        .login-wrap {
          .form {
            .step-indicator {
              margin: 20px 0;
              gap: 12px;

              .step {
                gap: 6px;

                .step-number {
                  width: 28px;
                  height: 28px;
                  font-size: 12px;
                }

                .step-label {
                  font-size: 11px;
                }
              }

              .step-divider {
                max-width: 40px;
              }
            }

            .email-code-input {
              flex-direction: column;
              gap: 8px;

              .get-code-btn {
                width: 100%;
              }
            }
          }
        }
      }
    }
  }
</style>
