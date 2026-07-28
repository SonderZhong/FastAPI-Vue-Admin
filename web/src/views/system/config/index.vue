<template>
  <div v-loading="loading" class="config-page art-full-height">
    <div class="config-shell">
      <section class="layout">
        <aside class="group-side">
          <div class="side-panel">
            <div class="panel-kicker">{{ pageTexts.title }}</div>
            <div class="panel-title-row">
              <div class="panel-title">{{ pageTexts.pageTitle }}</div>
              <ElTag size="small" effect="plain" type="primary">{{ configGroups.length }}</ElTag>
            </div>
            <div class="panel-desc">{{ pageTexts.pageDesc }}</div>
          </div>

          <div class="overview-card">
            <div class="overview-item">
              <span class="overview-label">{{ pageTexts.lastUpdate }}</span>
              <span class="overview-value">{{ lastUpdateText }}</span>
              <span class="overview-sub">{{ lastUpdateUser }}</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">{{ pageTexts.defaultLang }}</span>
              <span class="overview-value">{{ defaultLanguage }}</span>
              <span class="overview-sub">{{ pageTexts.langHint }}</span>
            </div>
          </div>

          <ElMenu :default-active="activeGroup" class="group-menu" @select="handleGroupSelect">
            <ElMenuItem v-for="group in configGroups" :key="group.group" :index="group.group">
              <div class="group-item">
                <div class="group-item-main">
                  <span
                    class="group-item-icon"
                    :style="{
                      background: getGroupMeta(group.group).softColor,
                      color: getGroupMeta(group.group).accentColor
                    }"
                  >
                    <ElIcon><component :is="getGroupMeta(group.group).icon" /></ElIcon>
                  </span>
                  <div class="group-item-copy">
                    <span class="group-item-label">{{ group.label }}</span>
                    <span class="group-item-sub">{{ getGroupMeta(group.group).description }}</span>
                  </div>
                </div>
                <span class="group-item-count">{{ group.configs.length }}</span>
              </div>
            </ElMenuItem>
          </ElMenu>
        </aside>

        <main class="main-panel">
          <div class="main-head">
            <div class="main-head-copy">
              <div class="main-head-title">{{ currentGroupLabel }}</div>
              <div class="main-head-desc">{{ getGroupMeta(activeGroup).description }}</div>
              <div class="main-head-meta">
                <span class="main-head-badge">{{ activeGroup }}</span>
                <span class="main-head-badge"
                  >{{ currentGroupConfigs.length }} {{ pageTexts.itemsUnit }}</span
                >
                <span class="main-head-badge">{{ builtInCount }} {{ pageTexts.builtInShort }}</span>
              </div>
            </div>
            <div class="toolbar-actions">
              <ElButton
                v-auth="'config:btn:add'"
                type="primary"
                :icon="Plus"
                @click="handleAddConfig"
              >
                {{ pageTexts.addConfig }}
              </ElButton>
              <ElButton v-auth="'config:btn:update'" :icon="Refresh" @click="handleRefreshCache">
                {{ pageTexts.refreshCache }}
              </ElButton>
            </div>
          </div>

          <div class="toolbar">
            <div class="stat-row">
              <div class="stat-card stat-card-primary">
                <div class="stat-label">{{ pageTexts.totalCount }}</div>
                <div class="stat-value">{{ currentGroupConfigs.length }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">{{ pageTexts.visibleCount }}</div>
                <div class="stat-value">{{ filteredConfigs.length }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">{{ pageTexts.builtInCount }}</div>
                <div class="stat-value">{{ builtInCount }}</div>
              </div>
            </div>

            <ElInput
              v-model="searchKey"
              class="search-input"
              :placeholder="pageTexts.searchPlaceholder"
              clearable
            >
              <template #prefix>
                <ElIcon><Search /></ElIcon>
              </template>
            </ElInput>
          </div>

          <ElCard class="list-card" shadow="never">
            <div v-if="filteredConfigs.length" class="config-list">
              <div v-for="config in filteredConfigs" :key="config.id" class="config-row">
                <div class="config-left">
                  <div class="config-name-line">
                    <span class="config-name">{{ config.name }}</span>
                    <ElTag v-if="config.type" size="small" effect="light" type="success">{{
                      pageTexts.systemBuiltIn
                    }}</ElTag>
                    <ElTag
                      v-if="isBooleanConfig(config.key)"
                      size="small"
                      effect="light"
                      :type="config.value === 'true' ? 'primary' : 'info'"
                    >
                      {{ config.value === 'true' ? pageTexts.enabled : pageTexts.disabled }}
                    </ElTag>
                  </div>
                  <div class="config-meta">
                    <span class="config-key">{{ config.key }}</span>
                    <span class="config-dot" />
                    <span class="config-updated">{{ formatDateTime(config.updated_at) }}</span>
                  </div>
                  <div v-if="config.remark" class="config-remark">{{ config.remark }}</div>
                </div>

                <div class="config-right">
                  <template v-if="isEditing(config.id)">
                    <div class="edit-panel">
                      <ElSwitch
                        v-if="isBooleanConfig(config.key)"
                        v-model="editingBoolValues[config.id]"
                        @change="
                          (val: boolean | string | number) =>
                            (editingValues[config.id] = val ? 'true' : 'false')
                        "
                      />
                      <ElInput
                        v-else
                        v-model="editingValues[config.id]"
                        class="value-input"
                        :type="isLongValue(config.value) ? 'textarea' : 'text'"
                        :rows="isLongValue(config.value) ? 3 : 1"
                      />
                      <div class="action-row">
                        <ElButton type="primary" :icon="Check" @click="handleSaveConfig(config)">
                          {{ pageTexts.confirm }}
                        </ElButton>
                        <ElButton :icon="Close" @click="handleCancelEdit(config.id)">
                          {{ pageTexts.cancel }}
                        </ElButton>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="value-panel">
                      <div class="value-panel-label">{{ pageTexts.currentValue }}</div>
                      <span class="value-text" :class="{ empty: !config.value }">{{
                        formatValue(config)
                      }}</span>
                    </div>
                    <div class="action-row">
                      <ElButton
                        v-auth="'config:btn:update'"
                        link
                        type="primary"
                        :icon="Edit"
                        @click="handleEditConfig(config)"
                      >
                        {{ pageTexts.edit }}
                      </ElButton>
                      <ElButton
                        v-if="!config.type"
                        v-auth="'config:btn:delete'"
                        link
                        type="danger"
                        :icon="Delete"
                        @click="handleDeleteConfig(config)"
                      >
                        {{ pageTexts.delete }}
                      </ElButton>
                    </div>
                  </template>
                </div>
              </div>
            </div>
            <ElEmpty v-else :description="pageTexts.noConfigs" />
          </ElCard>
        </main>
      </section>
    </div>

    <ConfigDialog
      v-model:visible="dialogVisible"
      :editData="editData"
      :isViewMode="false"
      :groups="configGroups"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import {
    ElButton,
    ElCard,
    ElEmpty,
    ElIcon,
    ElInput,
    ElMenu,
    ElMenuItem,
    ElMessage,
    ElMessageBox,
    ElSwitch,
    ElTag
  } from 'element-plus'
  import {
    Check,
    Close,
    Delete,
    Edit,
    Location,
    Lock,
    Message,
    Plus,
    Refresh,
    Search,
    Setting,
    UploadFilled,
    User
  } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { LanguageEnum } from '@/enums/appEnum'
  import { useUserStore } from '@/store/modules/user'
  import ConfigDialog from './modules/config-dialog.vue'
  import {
    fetchConfigGroups,
    fetchDeleteConfig,
    fetchRefreshConfigCache,
    fetchUpdateConfig,
    type ConfigGroupData,
    type ConfigInfo
  } from '@/api/system/config'

  defineOptions({ name: 'Config' })

  const { locale } = useI18n()
  const userStore = useUserStore()
  const loading = ref(false)
  const configGroups = ref<ConfigGroupData[]>([])
  const activeGroup = ref('system')
  const searchKey = ref('')
  const dialogVisible = ref(false)
  const editData = ref<ConfigInfo | null>(null)
  const editingIds = ref<Set<string>>(new Set())
  const editingValues = ref<Record<string, string>>({})
  const editingBoolValues = ref<Record<string, boolean>>({})

  const currentGroupConfigs = computed(
    () => configGroups.value.find((g) => g.group === activeGroup.value)?.configs || []
  )
  const currentGroupLabel = computed(
    () =>
      configGroups.value.find((g) => g.group === activeGroup.value)?.label ||
      pageTexts.value.groupTitle
  )
  const allConfigs = computed(() => configGroups.value.flatMap((group) => group.configs || []))
  const groupMetaMap = computed(() => {
    const isEn = locale.value === LanguageEnum.EN
    return {
      system: {
        icon: Setting,
        accentColor: '#2563eb',
        softColor: '#eff6ff',
        description: isEn ? 'Brand identity and basic runtime settings' : '系统标识与基础运行配置'
      },
      email: {
        icon: Message,
        accentColor: '#7c3aed',
        softColor: '#f5f3ff',
        description: isEn
          ? 'SMTP delivery, sender and notification defaults'
          : '邮件投递、发件人与通知默认项'
      },
      map: {
        icon: Location,
        accentColor: '#0f766e',
        softColor: '#ecfeff',
        description: isEn
          ? 'Map service provider and geolocation behavior'
          : '地图服务提供方与定位行为'
      },
      upload: {
        icon: UploadFilled,
        accentColor: '#ea580c',
        softColor: '#fff7ed',
        description: isEn
          ? 'Storage, upload policy and media limits'
          : '存储方式、上传策略与资源限制'
      },
      security: {
        icon: Lock,
        accentColor: '#dc2626',
        softColor: '#fef2f2',
        description: isEn
          ? 'Password, session and verification protection'
          : '密码、会话与验证保护策略'
      },
      account: {
        icon: User,
        accentColor: '#0891b2',
        softColor: '#ecfeff',
        description: isEn
          ? 'Registration, login and account-related switches'
          : '注册、登录与账号相关开关'
      }
    }
  })
  const getGroupMeta = (group: string) =>
    groupMetaMap.value[group as keyof typeof groupMetaMap.value] || {
      icon: Setting,
      accentColor: '#2563eb',
      softColor: '#eff6ff',
      description: locale.value === LanguageEnum.EN ? 'Grouped configuration items' : '分组配置项'
    }
  const lastUpdatedConfig = computed(
    () =>
      [...allConfigs.value]
        .filter((item) => item.updated_at)
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0]
  )
  const filteredConfigs = computed(() => {
    const list = currentGroupConfigs.value
    if (!searchKey.value) return list
    const key = searchKey.value.toLowerCase()
    return list.filter(
      (c) =>
        c.name.toLowerCase().includes(key) ||
        c.key.toLowerCase().includes(key) ||
        (c.remark || '').toLowerCase().includes(key)
    )
  })
  const builtInCount = computed(() => currentGroupConfigs.value.filter((item) => item.type).length)
  const lastUpdateText = computed(() => formatDateTime(lastUpdatedConfig.value?.updated_at))
  const lastUpdateUser = computed(
    () => lastUpdatedConfig.value?.group || pageTexts.value.groupTitle
  )
  const defaultLanguage = computed(() =>
    userStore.language === LanguageEnum.EN ? 'English' : '\u7b80\u4f53\u4e2d\u6587'
  )
  const pageTexts = computed(() =>
    locale.value === LanguageEnum.EN
      ? {
          title: 'Configuration Management',
          pageTitle: 'Site Settings',
          pageDesc:
            'Manage system identity, login experience, registration, captcha, storage and security policies in one place.',
          lastUpdate: 'Last Update',
          defaultLang: 'Default Language',
          langHint: 'Default language for login and public pages',
          groupTitle: 'Config Groups',
          groupHint: 'Supports grouped browsing, filtering and inline editing',
          itemsUnit: 'items',
          builtInShort: 'built-in',
          addConfig: 'Add Configuration',
          refreshCache: 'Refresh Cache',
          totalCount: 'Total Items',
          visibleCount: 'Visible Now',
          builtInCount: 'Built-in Items',
          searchPlaceholder: 'Search config name or key',
          systemBuiltIn: 'System Built-in',
          noConfigs: 'No configurations',
          currentValue: 'Current Value',
          enabled: 'Enabled',
          disabled: 'Disabled',
          confirm: 'Confirm',
          cancel: 'Cancel',
          edit: 'Edit',
          delete: 'Delete'
        }
      : {
          title: '\u914d\u7f6e\u7ba1\u7406',
          pageTitle: '\u7ad9\u70b9\u8bbe\u7f6e',
          pageDesc:
            '\u96c6\u4e2d\u7ba1\u7406\u7cfb\u7edf\u6807\u8bc6\u3001\u767b\u5f55\u4f53\u9a8c\u3001\u6ce8\u518c\u3001\u9a8c\u8bc1\u7801\u3001\u5b58\u50a8\u4e0e\u5b89\u5168\u7b56\u7565\u3002',
          lastUpdate: '\u6700\u8fd1\u66f4\u65b0',
          defaultLang: '\u9ed8\u8ba4\u8bed\u8a00',
          langHint:
            '\u7528\u4e8e\u767b\u5f55\u9875\u548c\u516c\u5171\u9875\u9762\u7684\u9ed8\u8ba4\u8bed\u8a00',
          groupTitle: '\u914d\u7f6e\u5206\u7ec4',
          groupHint:
            '\u652f\u6301\u5206\u7ec4\u6d4f\u89c8\u3001\u641c\u7d22\u7b5b\u9009\u4e0e\u884c\u5185\u7f16\u8f91',
          itemsUnit: '\u9879',
          builtInShort: '\u5185\u7f6e',
          addConfig: '\u65b0\u589e\u914d\u7f6e',
          refreshCache: '\u5237\u65b0\u7f13\u5b58',
          totalCount: '\u914d\u7f6e\u603b\u6570',
          visibleCount: '\u5f53\u524d\u663e\u793a',
          builtInCount: '\u5185\u7f6e\u914d\u7f6e',
          searchPlaceholder: '\u641c\u7d22\u914d\u7f6e\u540d\u79f0\u6216\u952e\u540d',
          systemBuiltIn: '\u7cfb\u7edf\u5185\u7f6e',
          noConfigs: '\u6682\u65e0\u914d\u7f6e',
          currentValue: '\u5f53\u524d\u503c',
          enabled: '\u542f\u7528',
          disabled: '\u505c\u7528',
          confirm: '\u786e\u5b9a',
          cancel: '\u53d6\u6d88',
          edit: '\u7f16\u8f91',
          delete: '\u5220\u9664'
        }
  )

  const isEditing = (id: string) => editingIds.value.has(id)
  const isBooleanConfig = (key: string) =>
    [
      'email_use_ssl',
      'api_status_enabled',
      'ip_location_enabled',
      'multi_login_allowed',
      'account_captcha_enabled',
      'account_register_enabled'
    ].includes(key) ||
    key.includes('_enabled') ||
    key.includes('_allowed')
  const isLongValue = (value: string) => Boolean(value && value.length > 50)
  const formatDateTime = (value?: string) => {
    if (!value) return '--'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    const pad = (num: number) => `${num}`.padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
  }
  const formatValue = (config: ConfigInfo) => {
    if (!config.value) return locale.value === LanguageEnum.EN ? 'Not set' : '\u672a\u8bbe\u7f6e'
    if (isBooleanConfig(config.key)) {
      return config.value === 'true'
        ? locale.value === LanguageEnum.EN
          ? 'Enabled'
          : '\u542f\u7528'
        : locale.value === LanguageEnum.EN
          ? 'Disabled'
          : '\u505c\u7528'
    }
    if (config.key.includes('password') || config.key.includes('secret')) return '******'
    return config.value
  }

  const loadConfigGroups = async () => {
    try {
      loading.value = true
      const response = await fetchConfigGroups()
      if (response?.success && response.data) {
        configGroups.value = response.data
        if (!response.data.find((g) => g.group === activeGroup.value) && response.data.length > 0) {
          activeGroup.value = response.data[0].group
        }
      }
    } catch (error) {
      console.error(error)
      ElMessage.error(
        locale.value === LanguageEnum.EN
          ? 'Failed to load configuration list'
          : '\u83b7\u53d6\u914d\u7f6e\u5217\u8868\u5931\u8d25'
      )
    } finally {
      loading.value = false
    }
  }

  const handleGroupSelect = (group: string) => {
    activeGroup.value = group
    editingIds.value.clear()
    editingValues.value = {}
    editingBoolValues.value = {}
  }

  const handleRefreshCache = async () => {
    const response = await fetchRefreshConfigCache()
    if (response?.success) {
      ElMessage.success(
        locale.value === LanguageEnum.EN
          ? 'Cache refreshed successfully'
          : '\u5237\u65b0\u7f13\u5b58\u6210\u529f'
      )
      await loadConfigGroups()
    } else {
      ElMessage.error(
        response?.msg ||
          (locale.value === LanguageEnum.EN
            ? 'Failed to refresh cache'
            : '\u5237\u65b0\u7f13\u5b58\u5931\u8d25')
      )
    }
  }

  const handleAddConfig = () => {
    editData.value = null
    dialogVisible.value = true
  }

  const handleEditConfig = (config: ConfigInfo) => {
    editingIds.value.add(config.id)
    editingValues.value[config.id] = config.value || ''
    editingBoolValues.value[config.id] = config.value === 'true'
  }

  const handleCancelEdit = (id: string) => {
    editingIds.value.delete(id)
    delete editingValues.value[id]
    delete editingBoolValues.value[id]
  }

  const handleSaveConfig = async (config: ConfigInfo) => {
    const value = isBooleanConfig(config.key)
      ? editingBoolValues.value[config.id]
        ? 'true'
        : 'false'
      : editingValues.value[config.id] || ''
    const response = await fetchUpdateConfig(config.id, {
      name: config.name,
      key: config.key,
      value,
      group: config.group,
      type: config.type,
      remark: config.remark ?? undefined
    })
    if (response?.success) {
      ElMessage.success(
        locale.value === LanguageEnum.EN
          ? 'Configuration updated successfully'
          : '\u66f4\u65b0\u914d\u7f6e\u6210\u529f'
      )
      handleCancelEdit(config.id)
      await loadConfigGroups()
    } else {
      ElMessage.error(
        response?.msg ||
          (locale.value === LanguageEnum.EN
            ? 'Failed to update configuration'
            : '\u66f4\u65b0\u914d\u7f6e\u5931\u8d25')
      )
    }
  }

  const handleDeleteConfig = async (config: ConfigInfo) => {
    await ElMessageBox.confirm(
      locale.value === LanguageEnum.EN
        ? `Are you sure you want to delete configuration "${config.name}"?`
        : `\u786e\u5b9a\u8981\u5220\u9664\u914d\u7f6e\u201c${config.name}\u201d\u5417\uff1f`,
      locale.value === LanguageEnum.EN ? 'Tips' : '\u63d0\u793a',
      { type: 'warning' }
    )
    const response = await fetchDeleteConfig(config.id)
    if (response?.success) {
      ElMessage.success(
        locale.value === LanguageEnum.EN
          ? 'Configuration deleted successfully'
          : '\u5220\u9664\u914d\u7f6e\u6210\u529f'
      )
      await loadConfigGroups()
    } else {
      ElMessage.error(
        response?.msg ||
          (locale.value === LanguageEnum.EN
            ? 'Failed to delete configuration'
            : '\u5220\u9664\u914d\u7f6e\u5931\u8d25')
      )
    }
  }

  const handleSubmit = async () => {
    await loadConfigGroups()
  }

  onMounted(loadConfigGroups)
</script>

<style scoped lang="scss">
  .config-page {
    min-height: 100%;
    padding: 16px;
    background: #f5f7fb;
  }

  .config-shell {
    min-height: calc(100vh - 132px);
  }

  .layout {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    gap: 16px;
    min-height: 100%;
    overflow: hidden;
  }

  .group-side {
    display: grid;
    gap: 14px;
    padding: 18px;
    border: 1px solid #e6ebf5;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.04);
  }

  .side-panel {
    display: grid;
    gap: 10px;
  }

  .panel-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .panel-kicker {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
  }

  .panel-title {
    font-size: 22px;
    font-weight: 700;
    line-height: 1.3;
    color: #0f172a;
  }

  .panel-desc {
    color: #64748b;
    line-height: 1.6;
    font-size: 13px;
  }

  .overview-card {
    display: grid;
    gap: 10px;
    padding: 16px;
    border: 1px solid #e7eefb;
    border-radius: 8px;
    background: linear-gradient(180deg, #fbfdff 0%, #f4f8ff 100%);
  }

  .overview-item {
    display: grid;
    gap: 4px;
  }

  .overview-label,
  .stat-label,
  .config-key,
  .config-remark {
    color: #64748b;
  }

  .overview-value,
  .stat-value {
    color: #0f172a;
    font-weight: 700;
  }

  .overview-sub {
    color: #94a3b8;
    font-size: 12px;
  }

  .group-menu {
    border-right: 0;
    background: transparent;
  }

  .group-menu :deep(.el-menu-item) {
    height: auto;
    margin-bottom: 8px;
    padding: 0 !important;
    border-radius: 8px;
  }

  .group-menu :deep(.el-menu-item.is-active) {
    background: #f3f7ff;
  }

  .group-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 13px 14px;
  }

  .group-item-main,
  .toolbar-actions,
  .main-head,
  .toolbar,
  .stat-row,
  .config-name-line,
  .config-meta,
  .action-row {
    display: flex;
    align-items: center;
  }

  .group-item-main {
    gap: 10px;
    min-width: 0;
  }

  .group-item-copy {
    min-width: 0;
    display: grid;
    gap: 3px;
  }

  .group-item-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    font-size: 16px;
    flex: 0 0 auto;
  }

  .group-item-label {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #0f172a;
    font-size: 13px;
    font-weight: 600;
  }

  .group-item-sub {
    color: #94a3b8;
    font-size: 12px;
    line-height: 1.4;
  }

  .group-item-count {
    min-width: 28px;
    height: 28px;
    padding: 0 8px;
    border-radius: 999px;
    background: #eff6ff;
    color: #2563eb;
    font-size: 12px;
    line-height: 28px;
    text-align: center;
  }

  .main-panel {
    min-width: 0;
    display: grid;
    gap: 16px;
    padding: 20px;
    border: 1px solid #e6ebf5;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.05);
  }

  .main-head {
    justify-content: space-between;
    gap: 16px;
    padding: 20px 22px;
    border: 1px solid #dbeafe;
    border-radius: 8px;
    background: linear-gradient(135deg, #eef5ff 0%, #f8fbff 100%);
  }

  .main-head-copy {
    min-width: 0;
    display: grid;
    gap: 8px;
  }

  .main-head-title {
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
  }

  .main-head-desc {
    color: #64748b;
    font-size: 13px;
  }

  .main-head-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .main-head-badge {
    display: inline-flex;
    align-items: center;
    height: 28px;
    padding: 0 10px;
    border: 1px solid #d7e5ff;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.78);
    color: #47607d;
    font-size: 12px;
  }

  .toolbar {
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    padding: 16px;
    border: 1px solid #edf2f7;
    border-radius: 8px;
    background: #fbfcfe;
  }

  .toolbar-actions {
    gap: 10px;
    flex-wrap: wrap;
  }

  .search-input {
    width: min(320px, 100%);
  }

  .stat-row {
    gap: 10px;
    flex-wrap: wrap;
  }

  .stat-card {
    min-width: 112px;
    padding: 14px 16px;
    border: 1px solid #e8eef7;
    border-radius: 8px;
    background: #fff;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  }

  .stat-card-primary {
    background: linear-gradient(180deg, #eff6ff 0%, #f8fbff 100%);
    border-color: #cfe0ff;
  }

  .stat-value {
    margin-top: 4px;
    font-size: 20px;
  }

  .list-card {
    border: 0;
    background: transparent;
  }

  .list-card :deep(.el-card__body) {
    padding: 0;
  }

  .config-list {
    display: grid;
    gap: 12px;
  }

  .config-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(340px, 420px);
    gap: 16px;
    padding: 18px;
    border: 1px solid #e8eef7;
    border-radius: 8px;
    background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%);
    transition:
      border-color 0.2s ease,
      box-shadow 0.2s ease,
      transform 0.2s ease;
  }

  .config-row:hover {
    border-color: #d4e3ff;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
    transform: translateY(-1px);
  }

  .config-left {
    min-width: 0;
    display: grid;
    align-content: start;
  }

  .config-name-line {
    gap: 8px;
  }

  .config-name {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
  }

  .config-meta {
    gap: 8px;
    margin-top: 4px;
    flex-wrap: wrap;
    min-width: 0;
  }

  .config-key {
    font-size: 12px;
    word-break: break-all;
  }

  .config-dot {
    width: 4px;
    height: 4px;
    border-radius: 999px;
    background: #cbd5e1;
  }

  .config-updated {
    color: #94a3b8;
    font-size: 12px;
  }

  .config-remark {
    margin-top: 6px;
    line-height: 1.5;
    font-size: 13px;
  }

  .config-right {
    display: grid;
    gap: 10px;
    justify-items: end;
  }

  .value-panel,
  .edit-panel {
    width: 100%;
    padding: 14px 16px;
    border: 1px solid #edf2f7;
    border-radius: 8px;
    background: #f8fafc;
  }

  .edit-panel {
    display: grid;
    gap: 12px;
  }

  .value-text {
    display: block;
    width: 100%;
    color: #334155;
    line-height: 1.6;
    word-break: break-all;
  }

  .value-panel-label {
    margin-bottom: 6px;
    color: #94a3b8;
    font-size: 12px;
    line-height: 1;
  }

  .value-text.empty {
    opacity: 0.6;
  }

  .value-input {
    width: 100%;
  }

  .action-row {
    gap: 8px;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  @media (max-width: 1200px) {
    .layout {
      grid-template-columns: 1fr;
    }

    .group-side {
      padding: 18px;
    }

    .config-row {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 768px) {
    .config-page {
      padding: 12px;
    }

    .group-side,
    .main-panel {
      padding: 16px;
      border-radius: 8px;
    }

    .main-head {
      padding: 16px;
    }

    .main-head,
    .toolbar,
    .stat-row,
    .action-row,
    .config-right {
      align-items: stretch;
      justify-items: stretch;
      flex-direction: column;
    }

    .search-input,
    .stat-card,
    .value-input,
    .group-item-count {
      width: 100%;
    }

    .group-item-count {
      min-width: 0;
    }
  }
</style>
