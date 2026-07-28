<template>
  <div class="select-tenant-page">
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
    <div class="select-tenant-panel">
      <div class="panel-header">
        <h1>{{ t('selectTenant.title') }}</h1>
        <p>{{ t('selectTenant.subTitle') }}</p>
      </div>
      <ElRadioGroup v-model="selectedTenantId" class="tenant-list">
        <div
          v-for="tenant in tenantList"
          :key="tenant.id"
          class="tenant-item"
          :class="{ 'is-active': selectedTenantId === tenant.id }"
        >
          <ElRadio :label="tenant.id" size="large">
            <div class="tenant-meta">
              <span class="tenant-name">{{ tenant.name }}</span>
              <span v-if="tenant.code" class="tenant-code">{{ tenant.code }}</span>
            </div>
          </ElRadio>
        </div>
      </ElRadioGroup>
      <div class="panel-footer">
        <ElButton text @click="handleBackToLogin">{{ t('selectTenant.backToLogin') }}</ElButton>
        <ElButton type="primary" :loading="submitting" @click="handleConfirm">{{
          t('selectTenant.enterSystem')
        }}</ElButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { fetchGetUserInfo, fetchSelectTenant } from '@/api/auth'
  import { resetRouterState } from '@/router/guards/beforeEach'
  import { RoutesAlias } from '@/router/routesAlias'
  import { useUserStore } from '@/store/modules/user'
  import { useSettingStore } from '@/store/modules/setting'
  import { languageOptions } from '@/locales'
  import { LanguageEnum } from '@/enums/appEnum'
  import { themeAnimation } from '@/utils/theme/animation'
  import { useHeaderBar } from '@/composables/useHeaderBar'

  defineOptions({ name: 'SelectTenant' })

  const router = useRouter()
  const userStore = useUserStore()
  const settingStore = useSettingStore()
  const { t, locale } = useI18n()
  const { isDark } = storeToRefs(settingStore)
  const { shouldShowThemeToggle, shouldShowLanguage } = useHeaderBar()
  const submitting = ref(false)
  const tenantList = computed(() => userStore.availableTenants || [])
  const selectedTenantId = ref('')

  watch(
    tenantList,
    (list) => {
      if (!selectedTenantId.value && list.length > 0) {
        selectedTenantId.value = list[0].id
      }
    },
    { immediate: true }
  )

  onMounted(() => {
    if (!userStore.accessToken) {
      router.replace(RoutesAlias.Login)
      return
    }

    if (!tenantList.value.length) {
      userStore.setNeedSelectTenant(false)
      router.replace(RoutesAlias.Login)
    }
  })

  const handleBackToLogin = () => userStore.logOut()

  const changeLanguage = (lang: LanguageEnum) => {
    if (locale.value === lang) return
    locale.value = lang
    userStore.setLanguage(lang)
  }

  const handleConfirm = async () => {
    if (!selectedTenantId.value) {
      ElMessage.warning(t('selectTenant.selectRequired'))
      return
    }

    submitting.value = true
    try {
      const response = await fetchSelectTenant(selectedTenantId.value)
      if (!response.success) {
        throw new Error(response.msg || t('selectTenant.switchFailed'))
      }

      const userInfoResponse = await fetchGetUserInfo()
      if (!userInfoResponse.success || !userInfoResponse.data) {
        throw new Error(userInfoResponse.msg || t('selectTenant.userInfoFailed'))
      }

      userStore.setUserInfo(userInfoResponse.data)
      userStore.setNeedSelectTenant(false)
      userStore.setLoginStatus(true)
      resetRouterState()
      ElMessage.success(t('selectTenant.switchSuccess'))
      router.replace('/')
    } catch (error: any) {
      ElMessage.error(error?.message || t('selectTenant.switchFailed'))
    } finally {
      submitting.value = false
    }
  }
</script>

<style scoped lang="scss">
  .select-tenant-page {
    position: relative;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: var(--el-bg-color-page);
  }

  .top-right-wrap {
    position: absolute;
    top: 24px;
    right: 24px;
    display: flex;
    gap: 10px;
  }

  .btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: var(--el-text-color-primary);
  }

  .language-btn,
  .theme-btn {
    border-radius: 50%;
    transition: all 0.2s ease;
  }

  .language-btn:hover,
  .theme-btn:hover {
    background: rgb(59 130 246 / 8%);
    color: var(--el-color-primary);
  }

  .select-tenant-panel {
    width: min(640px, 100%);
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color-light);
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 18px 40px rgb(15 23 42 / 8%);
  }

  .panel-header {
    margin-bottom: 24px;
  }

  .panel-header h1 {
    margin: 0;
    font-size: 24px;
    color: var(--el-text-color-primary);
  }

  .panel-header p {
    margin: 10px 0 0;
    color: var(--el-text-color-secondary);
    line-height: 1.6;
  }

  .tenant-list {
    display: grid;
    gap: 12px;
    width: 100%;
  }

  .tenant-item {
    border: 1px solid var(--el-border-color);
    border-radius: 10px;
    padding: 16px 18px;
    transition: all 0.2s ease;
  }

  .tenant-item.is-active {
    border-color: var(--el-color-primary);
    background: rgb(59 130 246 / 6%);
  }

  .tenant-item :deep(.el-radio) {
    width: 100%;
    margin-right: 0;
  }

  .tenant-item :deep(.el-radio__label) {
    width: 100%;
    padding-left: 12px;
  }

  .tenant-meta {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    width: 100%;
  }

  .tenant-name {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .tenant-code {
    color: var(--el-text-color-secondary);
  }

  .panel-footer {
    display: flex;
    justify-content: space-between;
    margin-top: 24px;
  }
</style>
