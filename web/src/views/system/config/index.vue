<template>
  <div class="config-page art-full-height">
    <ElCard class="config-card" shadow="never">
      <!-- 头部操作栏 -->
      <div class="config-header">
        <div class="header-left">
          <ElButton v-auth="'config:btn:add'" @click="handleAddConfig" type="primary" v-ripple>
            <ElIcon><Plus /></ElIcon>
            {{ t('config.addConfig') }}
          </ElButton>
          <ElButton v-auth="'config:btn:update'" @click="handleRefreshCache" type="success" plain v-ripple>
            <ElIcon><Refresh /></ElIcon>
            {{ t('config.refreshCache') }}
          </ElButton>
        </div>
        <div class="header-right">
          <ElInput
            v-model="searchKey"
            :placeholder="t('config.searchPlaceholder')"
            clearable
            style="width: 240px"
            @input="handleSearch"
          >
            <template #prefix>
              <ElIcon><Search /></ElIcon>
            </template>
          </ElInput>
        </div>
      </div>

      <!-- 分组 Tabs -->
      <ElTabs v-model="activeGroup" @tab-change="handleTabChange">
        <ElTabPane
          v-for="group in configGroups"
          :key="group.group"
          :label="group.label"
          :name="group.group"
        >
          <div class="config-list">
            <template v-if="filteredConfigs.length > 0">
              <div
                v-for="config in filteredConfigs"
                :key="config.id"
                class="config-item"
              >
                <div class="config-info">
                  <div class="config-name">
                    <span class="name">{{ config.name }}</span>
                    <ElTag v-if="config.type" type="success" size="small">{{ t('config.systemBuiltIn') }}</ElTag>
                  </div>
                  <div class="config-key">{{ config.key }}</div>
                  <div class="config-remark" v-if="config.remark">{{ config.remark }}</div>
                </div>
                <div class="config-value">
                  <template v-if="isEditing(config.id)">
                    <ElInput
                      v-if="isBooleanConfig(config.key)"
                      v-model="editingValues[config.id]"
                      disabled
                      style="width: 200px"
                    />
                    <ElSwitch
                      v-if="isBooleanConfig(config.key)"
                      v-model="editingBoolValues[config.id]"
                      @change="(val: string | number | boolean) => editingValues[config.id] = val ? 'true' : 'false'"
                      style="margin-left: 10px"
                    />
                    <ElInput
                      v-else
                      v-model="editingValues[config.id]"
                      :type="isLongValue(config.value) ? 'textarea' : 'text'"
                      :rows="2"
                      style="width: 300px"
                    />
                    <ElButton type="primary" size="small" @click="handleSaveConfig(config)" style="margin-left: 10px">
                      {{ t('common.confirm') }}
                    </ElButton>
                    <ElButton size="small" @click="handleCancelEdit(config.id)" style="margin-left: 5px">
                      {{ t('common.cancel') }}
                    </ElButton>
                  </template>
                  <template v-else>
                    <span class="value-text" :class="{ 'value-empty': !config.value }">
                      {{ formatValue(config) }}
                    </span>
                    <div class="config-actions">
                      <ElButton
                        v-auth="'config:btn:update'"
                        type="primary"
                        link
                        size="small"
                        @click="handleEditConfig(config)"
                      >
                        {{ t('buttons.edit') }}
                      </ElButton>
                      <ElButton
                        v-if="!config.type"
                        v-auth="'config:btn:delete'"
                        type="danger"
                        link
                        size="small"
                        @click="handleDeleteConfig(config)"
                      >
                        {{ t('buttons.delete') }}
                      </ElButton>
                    </div>
                  </template>
                </div>
              </div>
            </template>
            <ElEmpty v-else :description="t('config.noConfigs')" />
          </div>
        </ElTabPane>
      </ElTabs>
    </ElCard>

    <!-- 新增配置弹窗 -->
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
  import { ElMessage, ElMessageBox, ElCard, ElTabs, ElTabPane, ElButton, ElIcon, ElInput, ElTag, ElSwitch, ElEmpty } from 'element-plus'
  import { Plus, Refresh, Search } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import ConfigDialog from './modules/config-dialog.vue'
  import {
    fetchConfigGroups,
    fetchDeleteConfig,
    fetchUpdateConfig,
    fetchRefreshConfigCache,
    type ConfigInfo,
    type ConfigGroupData
  } from '@/api/system/config'

  defineOptions({ name: 'Config' })

  const { t } = useI18n()

  // 状态
  const loading = ref(false)
  const configGroups = ref<ConfigGroupData[]>([])
  const activeGroup = ref('system')
  const searchKey = ref('')
  const dialogVisible = ref(false)
  const editData = ref<ConfigInfo | null>(null)

  // 编辑状态
  const editingIds = ref<Set<string>>(new Set())
  const editingValues = ref<Record<string, string>>({})
  const editingBoolValues = ref<Record<string, boolean>>({})

  // 当前分组的配置
  const currentGroupConfigs = computed(() => {
    const group = configGroups.value.find(g => g.group === activeGroup.value)
    return group?.configs || []
  })

  // 过滤后的配置
  const filteredConfigs = computed(() => {
    if (!searchKey.value) return currentGroupConfigs.value
    const key = searchKey.value.toLowerCase()
    return currentGroupConfigs.value.filter(c =>
      c.name.toLowerCase().includes(key) ||
      c.key.toLowerCase().includes(key) ||
      (c.remark && c.remark.toLowerCase().includes(key))
    )
  })

  // 判断是否正在编辑
  const isEditing = (id: string) => editingIds.value.has(id)

  // 判断是否为布尔类型配置
  const isBooleanConfig = (key: string) => {
    const boolKeys = ['email_use_ssl', 'api_status_enabled', 'ip_location_enabled', 'multi_login_allowed', 'account_captcha_enabled', 'account_register_enabled']
    return boolKeys.includes(key) || key.includes('_enabled') || key.includes('_allowed')
  }

  // 判断是否为长文本
  const isLongValue = (value: string) => value && value.length > 50

  // 格式化显示值
  const formatValue = (config: ConfigInfo) => {
    if (!config.value) return t('config.notSet')
    if (isBooleanConfig(config.key)) {
      return config.value === 'true' ? t('common.enabled') : t('common.disabled')
    }
    // 密码类型脱敏
    if (config.key.includes('password') || config.key.includes('secret')) {
      return '••••••••'
    }
    return config.value
  }

  // 加载配置分组
  const loadConfigGroups = async () => {
    try {
      loading.value = true
      const response = await fetchConfigGroups()
      if (response?.success && response.data) {
        configGroups.value = response.data
        if (response.data.length > 0 && !response.data.find(g => g.group === activeGroup.value)) {
          activeGroup.value = response.data[0].group
        }
      }
    } catch (error) {
      console.error('加载配置分组失败:', error)
      ElMessage.error(t('config.loadConfigFailed'))
    } finally {
      loading.value = false
    }
  }

  // Tab 切换
  const handleTabChange = () => {
    // 清除编辑状态
    editingIds.value.clear()
    editingValues.value = {}
    editingBoolValues.value = {}
  }

  // 搜索
  const handleSearch = () => {
    // 搜索时自动过滤
  }

  // 刷新缓存
  const handleRefreshCache = async () => {
    try {
      const response = await fetchRefreshConfigCache()
      if (response?.success) {
        ElMessage.success(t('config.refreshCacheSuccess'))
        loadConfigGroups()
      } else {
        ElMessage.error(response?.msg || t('config.refreshCacheFailed'))
      }
    } catch (error) {
      ElMessage.error(t('config.refreshCacheFailed'))
    }
  }

  // 新增配置
  const handleAddConfig = () => {
    editData.value = null
    dialogVisible.value = true
  }

  // 编辑配置
  const handleEditConfig = (config: ConfigInfo) => {
    editingIds.value.add(config.id)
    editingValues.value[config.id] = config.value || ''
    editingBoolValues.value[config.id] = config.value === 'true'
  }

  // 取消编辑
  const handleCancelEdit = (id: string) => {
    editingIds.value.delete(id)
    delete editingValues.value[id]
    delete editingBoolValues.value[id]
  }

  // 保存配置
  const handleSaveConfig = async (config: ConfigInfo) => {
    const newValue = editingValues.value[config.id]
    if (newValue === config.value) {
      handleCancelEdit(config.id)
      return
    }

    try {
      const response = await fetchUpdateConfig(config.id, {
        name: config.name,
        key: config.key,
        value: newValue,
        type: config.type,
        remark: config.remark || undefined
      })

      if (response?.success) {
        ElMessage.success(t('config.updateConfigSuccess'))
        handleCancelEdit(config.id)
        loadConfigGroups()
      } else {
        ElMessage.error(response?.msg || t('config.updateConfigFailed'))
      }
    } catch (error) {
      ElMessage.error(t('config.updateConfigFailed'))
    }
  }

  // 删除配置
  const handleDeleteConfig = async (config: ConfigInfo) => {
    try {
      await ElMessageBox.confirm(
        t('config.confirmDeleteConfig', { name: config.name }),
        t('common.deleteConfirm'),
        {
          confirmButtonText: t('common.confirm'),
          cancelButtonText: t('common.cancel'),
          type: 'warning'
        }
      )

      const response = await fetchDeleteConfig(config.id)
      if (response?.success) {
        ElMessage.success(t('common.deleteSuccess'))
        loadConfigGroups()
      } else {
        ElMessage.error(response?.msg || t('common.deleteFailed'))
      }
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(t('common.deleteFailed'))
      }
    }
  }

  // 弹窗提交
  const handleSubmit = () => {
    loadConfigGroups()
  }

  onMounted(() => {
    loadConfigGroups()
  })
</script>

<style lang="scss" scoped>
  .config-page {
    .config-card {
      height: 100%;
      
      :deep(.el-card__body) {
        height: calc(100% - 20px);
        display: flex;
        flex-direction: column;
      }
    }

    .config-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--el-border-color-lighter);

      .header-left {
        display: flex;
        gap: 10px;
      }
    }

    :deep(.el-tabs) {
      flex: 1;
      display: flex;
      flex-direction: column;

      .el-tabs__content {
        flex: 1;
        overflow: auto;
      }
    }

    .config-list {
      .config-item {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 16px;
        border-bottom: 1px solid var(--el-border-color-lighter);
        transition: background-color 0.2s;

        &:hover {
          background-color: var(--el-fill-color-light);
        }

        &:last-child {
          border-bottom: none;
        }

        .config-info {
          flex: 1;
          min-width: 0;

          .config-name {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;

            .name {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
            }
          }

          .config-key {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            font-family: monospace;
            margin-bottom: 4px;
          }

          .config-remark {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
          }
        }

        .config-value {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-shrink: 0;

          .value-text {
            font-size: 14px;
            color: var(--el-text-color-regular);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;

            &.value-empty {
              color: var(--el-text-color-placeholder);
              font-style: italic;
            }
          }

          .config-actions {
            display: flex;
            gap: 5px;
          }
        }
      }
    }
  }
</style>
