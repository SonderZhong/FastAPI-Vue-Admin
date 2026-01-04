<template>
  <ElDialog
    :title="dialogTitle"
    :model-value="visible"
    @update:model-value="handleCancel"
    width="500px"
    align-center
    class="config-dialog"
    @closed="handleClosed"
  >
    <ElForm ref="formRef" :model="form" :rules="rules" label-width="100px">
      <ElFormItem :label="t('config.configName')" prop="name">
        <ElInput
          v-model="form.name"
          :placeholder="t('config.configNamePlaceholder')"
          :disabled="isView"
        />
      </ElFormItem>

      <ElFormItem :label="t('config.configKey')" prop="key">
        <ElInput
          v-model="form.key"
          :placeholder="t('config.configKeyPlaceholder')"
          :disabled="isView || isEdit"
        />
      </ElFormItem>

      <ElFormItem :label="t('config.configGroup')" prop="group">
        <ElSelect
          v-model="form.group"
          :placeholder="t('config.selectGroup')"
          :disabled="isView"
          style="width: 100%"
        >
          <ElOption
            v-for="group in groups"
            :key="group.group"
            :label="group.label"
            :value="group.group"
          />
        </ElSelect>
      </ElFormItem>

      <ElFormItem :label="t('config.configValue')" prop="value">
        <ElInput
          v-model="form.value"
          type="textarea"
          :rows="3"
          :placeholder="t('config.configValuePlaceholder')"
          :disabled="isView"
        />
      </ElFormItem>

      <ElFormItem :label="t('config.configType')" prop="type">
        <ElSwitch
          v-model="form.type"
          :active-text="t('config.systemBuiltIn')"
          :inactive-text="t('config.userDefined')"
          :disabled="isView"
        />
      </ElFormItem>

      <ElFormItem :label="t('common.description')" prop="remark">
        <ElInput
          v-model="form.remark"
          type="textarea"
          :rows="2"
          :placeholder="t('config.configRemarkPlaceholder')"
          :disabled="isView"
        />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <span class="dialog-footer">
        <ElButton @click="handleCancel">{{ t('common.cancel') }}</ElButton>
        <ElButton v-if="!isView" type="primary" @click="handleSubmit">
          {{ t('common.confirm') }}
        </ElButton>
      </span>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import type { FormInstance, FormRules } from 'element-plus'
  import {
    ElDialog,
    ElForm,
    ElFormItem,
    ElInput,
    ElSwitch,
    ElSelect,
    ElOption,
    ElButton,
    ElMessage
  } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import {
    fetchAddConfig,
    fetchUpdateConfig,
    type ConfigInfo,
    type ConfigFormParams,
    type ConfigGroupData
  } from '@/api/system/config'

  interface ConfigFormData {
    name: string
    key: string
    value: string
    group: string
    type: boolean
    remark: string
  }

  interface Props {
    visible: boolean
    editData?: ConfigInfo | null
    isViewMode?: boolean
    groups?: ConfigGroupData[]
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'submit'): void
  }

  const props = withDefaults(defineProps<Props>(), {
    visible: false,
    editData: null,
    isViewMode: false,
    groups: () => []
  })

  const emit = defineEmits<Emits>()
  const { t } = useI18n()

  const formRef = ref<FormInstance>()
  const isEdit = ref(false)
  const isView = computed(() => props.isViewMode)

  const form = reactive<ConfigFormData>({
    name: '',
    key: '',
    value: '',
    group: 'system',
    type: false,
    remark: ''
  })

  const rules = reactive<FormRules>({
    name: [
      { required: true, message: t('config.configNameRequired'), trigger: 'blur' },
      { min: 2, max: 100, message: t('config.configNameLength'), trigger: 'blur' }
    ],
    key: [
      { required: true, message: t('config.configKeyRequired'), trigger: 'blur' },
      { min: 2, max: 100, message: t('config.configKeyLength'), trigger: 'blur' }
    ],
    value: [
      { required: true, message: t('config.configValueRequired'), trigger: 'blur' }
    ],
    group: [
      { required: true, message: t('config.selectGroup'), trigger: 'change' }
    ]
  })

  const dialogTitle = computed(() => {
    if (isView.value) return t('config.viewConfig')
    return isEdit.value ? t('config.editConfig') : t('config.addConfig')
  })

  const resetForm = () => {
    formRef.value?.resetFields()
    Object.assign(form, {
      name: '',
      key: '',
      value: '',
      group: 'system',
      type: false,
      remark: ''
    })
  }

  const loadFormData = () => {
    if (!props.editData) return

    isEdit.value = !props.isViewMode

    form.name = props.editData.name
    form.key = props.editData.key
    form.value = props.editData.value
    form.group = props.editData.group || 'system'
    form.type = props.editData.type
    form.remark = props.editData.remark || ''
  }

  const handleSubmit = async () => {
    if (!formRef.value || isView.value) return

    await formRef.value.validate(async (valid) => {
      if (valid) {
        try {
          const params: ConfigFormParams = {
            name: form.name,
            key: form.key,
            value: form.value,
            group: form.group,
            type: form.type,
            remark: form.remark || undefined
          }

          let response
          if (isEdit.value && props.editData) {
            response = await fetchUpdateConfig(props.editData.id, params)
          } else {
            response = await fetchAddConfig(params)
          }

          if (response?.success) {
            ElMessage.success(
              isEdit.value ? t('config.updateConfigSuccess') : t('config.addConfigSuccess')
            )
            emit('submit')
            handleCancel()
          } else {
            ElMessage.error(
              response?.msg ||
                (isEdit.value ? t('config.updateConfigFailed') : t('config.addConfigFailed'))
            )
          }
        } catch (error) {
          console.error('配置操作失败:', error)
          ElMessage.error(
            isEdit.value ? t('config.updateConfigFailed') : t('config.addConfigFailed')
          )
        }
      }
    })
  }

  const handleCancel = () => {
    emit('update:visible', false)
  }

  const handleClosed = () => {
    resetForm()
    isEdit.value = false
  }

  watch(
    () => props.visible,
    (newVal) => {
      if (newVal) {
        nextTick(() => {
          if (props.editData) {
            loadFormData()
          }
        })
      }
    }
  )

  watch(
    () => props.editData,
    (newData) => {
      if (props.visible && newData) {
        loadFormData()
      }
    }
  )
</script>

<style lang="scss" scoped>
  .config-dialog {
    :deep(.el-dialog__body) {
      padding-top: 10px;
    }
  }
</style>
