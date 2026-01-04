<template>
  <ElDrawer
    :model-value="modelValue"
    :title="drawerTitle"
    size="500px"
    :before-close="handleClose"
    @open="handleOpen"
    @update:model-value="emit('update:modelValue', $event)"
    class="api-permission-drawer"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      :disabled="formLoading"
    >
      <ElFormItem :label="$t('common.displayName')" prop="title">
        <ElInput v-model="formData.title" :placeholder="$t('common.pleaseInput')" />
      </ElFormItem>

      <ElFormItem :label="$t('permission.apiPath')" prop="api_path">
        <ElInput v-model="formData.api_path" placeholder="/user/list, /user/*" />
        <template #extra>
          <div class="text-xs text-gray-500 mt-1">
            {{ $t('permission.apiPathTip') }}
          </div>
        </template>
      </ElFormItem>

      <ElFormItem :label="$t('permission.requestMethod')" prop="api_method">
        <ElCheckboxGroup v-model="formData.api_method">
          <ElCheckbox label="GET">
            <ElTag type="success" size="small">GET</ElTag>
          </ElCheckbox>
          <ElCheckbox label="POST">
            <ElTag type="primary" size="small">POST</ElTag>
          </ElCheckbox>
          <ElCheckbox label="PUT">
            <ElTag type="warning" size="small">PUT</ElTag>
          </ElCheckbox>
          <ElCheckbox label="DELETE">
            <ElTag type="danger" size="small">DELETE</ElTag>
          </ElCheckbox>
        </ElCheckboxGroup>
      </ElFormItem>

      <ElFormItem :label="$t('permission.dataScope')" prop="data_scope">
        <ElSelect v-model="formData.data_scope" :placeholder="$t('common.pleaseSelect')" style="width: 100%">
          <ElOption :label="$t('permission.dataScopeAll')" :value="1">
            <div class="flex items-center justify-between">
              <span>{{ $t('permission.dataScopeAll') }}</span>
              <ElTag type="danger" size="small">{{ $t('permission.highest') }}</ElTag>
            </div>
          </ElOption>
          <ElOption :label="$t('permission.dataScopeDeptAndChild')" :value="2">
            <div class="flex items-center justify-between">
              <span>{{ $t('permission.dataScopeDeptAndChild') }}</span>
              <ElTag type="warning" size="small">{{ $t('common.department') }}</ElTag>
            </div>
          </ElOption>
          <ElOption :label="$t('permission.dataScopeDeptOnly')" :value="3">
            <div class="flex items-center justify-between">
              <span>{{ $t('permission.dataScopeDeptOnly') }}</span>
              <ElTag type="primary" size="small">{{ $t('permission.currentDept') }}</ElTag>
            </div>
          </ElOption>
          <ElOption :label="$t('permission.dataScopeSelfOnly')" :value="4">
            <div class="flex items-center justify-between">
              <span>{{ $t('permission.dataScopeSelfOnly') }}</span>
              <ElTag type="info" size="small">{{ $t('permission.default') }}</ElTag>
            </div>
          </ElOption>
        </ElSelect>
      </ElFormItem>

      <ElFormItem :label="$t('permission.minUserType')" prop="min_user_type">
        <ElSelect v-model="formData.min_user_type" :placeholder="$t('common.pleaseSelect')" style="width: 100%">
          <ElOption :label="$t('login.roles.super')" :value="0">
            <div class="flex items-center justify-between">
              <span>{{ $t('login.roles.super') }}</span>
              <ElTag type="danger" size="small">{{ $t('permission.superOnly') }}</ElTag>
            </div>
          </ElOption>
          <ElOption :label="$t('login.roles.admin')" :value="1">
            <div class="flex items-center justify-between">
              <span>{{ $t('login.roles.admin') }}</span>
              <ElTag type="warning" size="small">{{ $t('permission.adminPlus') }}</ElTag>
            </div>
          </ElOption>
          <ElOption :label="$t('permission.deptAdmin')" :value="2">
            <div class="flex items-center justify-between">
              <span>{{ $t('permission.deptAdmin') }}</span>
              <ElTag type="primary" size="small">{{ $t('permission.deptAdminPlus') }}</ElTag>
            </div>
          </ElOption>
          <ElOption :label="$t('permission.allUsers')" :value="3">
            <div class="flex items-center justify-between">
              <span>{{ $t('permission.allUsers') }}</span>
              <ElTag type="info" size="small">{{ $t('permission.default') }}</ElTag>
            </div>
          </ElOption>
        </ElSelect>
      </ElFormItem>

      <ElFormItem :label="$t('common.remark')" prop="remark">
        <ElInput v-model="formData.remark" type="textarea" :rows="2" :placeholder="$t('common.pleaseInput')" />
      </ElFormItem>

      <ElDivider>{{ $t('permission.apiTemplates') }}</ElDivider>

      <div class="api-templates">
        <ElButton
          v-for="tpl in apiTemplates"
          :key="tpl.path + tpl.methods.join(',')"
          size="small"
          round
          @click="applyTemplate(tpl)"
        >
          <span class="mr-1">
            <ElTag v-for="m in tpl.methods" :key="m" :type="getMethodTagType(m)" size="small" class="mr-0.5">{{ m }}</ElTag>
          </span>
          {{ tpl.label }}
        </ElButton>
      </div>
    </ElForm>

    <template #footer>
      <ElButton round @click="handleClose">{{ $t('common.cancel') }}</ElButton>
      <ElButton round type="primary" :loading="submitLoading" @click="handleSubmit">{{ $t('common.confirm') }}</ElButton>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { addApiPermission, updateApiPermission } from '@/api/system/permission'
import type { PermissionInfo } from '@/api/system/permission'

interface Props {
  modelValue: boolean
  dialogType: 'add' | 'edit'
  permissionData?: Partial<PermissionInfo>
  parentId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const { t } = useI18n()

const formRef = ref<FormInstance>()
const formLoading = ref(false)
const submitLoading = ref(false)

const formData = ref({
  title: '',
  api_path: '',
  api_method: [] as string[],
  data_scope: 4,
  min_user_type: 3,
  remark: ''
})

const formRules = computed(() => ({
  title: [{ required: true, message: t('common.pleaseInput'), trigger: 'blur' }],
  api_path: [{ required: true, message: t('permission.apiPathRequired'), trigger: 'blur' }],
  api_method: [{ required: true, message: t('permission.apiMethodRequired'), trigger: 'change', type: 'array' as const }]
}))

const apiTemplates = computed(() => [
  { label: t('permission.tplList'), path: '/xxx/list', methods: ['GET'] },
  { label: t('permission.tplDetail'), path: '/xxx/info/*', methods: ['GET'] },
  { label: t('permission.tplAdd'), path: '/xxx/add', methods: ['POST'] },
  { label: t('permission.tplUpdate'), path: '/xxx/update/*', methods: ['PUT', 'POST'] },
  { label: t('permission.tplDelete'), path: '/xxx/delete/*', methods: ['DELETE', 'POST'] },
  { label: t('permission.tplBatchDelete'), path: '/xxx/deleteList', methods: ['DELETE', 'POST'] },
  { label: t('permission.tplAll'), path: '/xxx/*', methods: ['GET', 'POST', 'PUT', 'DELETE'] }
])

const drawerTitle = computed(() => props.dialogType === 'add' ? t('permission.addApiPermission') : t('permission.editApiPermission'))

const getMethodTagType = (method: string) => {
  switch (method) {
    case 'GET': return 'success'
    case 'POST': return 'primary'
    case 'PUT': return 'warning'
    case 'DELETE': return 'danger'
    case 'PATCH': return 'info'
    default: return 'info'
  }
}

const applyTemplate = (tpl: { path: string; methods: string[]; label: string }) => {
  formData.value.api_path = tpl.path
  formData.value.api_method = [...tpl.methods]
  if (!formData.value.title) {
    formData.value.title = tpl.label
  }
}

const handleOpen = () => {
  if (props.dialogType === 'edit' && props.permissionData) {
    const apiMethod = props.permissionData.api_method
    formData.value = {
      title: props.permissionData.title || '',
      api_path: props.permissionData.api_path || '',
      api_method: Array.isArray(apiMethod) ? apiMethod : (apiMethod ? [apiMethod] : []),
      data_scope: props.permissionData.data_scope ?? 4,
      min_user_type: props.permissionData.min_user_type ?? 3,
      remark: props.permissionData.remark || ''
    }
  } else {
    resetForm()
  }
}

const resetForm = () => {
  formData.value = {
    title: '',
    api_path: '',
    api_method: [],
    data_scope: 4,
    min_user_type: 3,
    remark: ''
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    submitLoading.value = true

    const submitData = {
      title: formData.value.title,
      api_path: formData.value.api_path,
      api_method: formData.value.api_method,
      data_scope: formData.value.data_scope,
      min_user_type: formData.value.min_user_type,
      remark: formData.value.remark,
      parent_id: props.parentId
    }

    let res
    if (props.dialogType === 'add') {
      res = await addApiPermission(submitData)
    } else {
      res = await updateApiPermission(props.permissionData!.id!, submitData)
    }

    if (res.success) {
      ElMessage.success(t('common.operationSuccess'))
      emit('success')
      handleClose()
    } else {
      ElMessage.error(res.msg || t('common.updateFailed'))
    }
  } catch (e) {
    console.error('提交失败:', e)
  } finally {
    submitLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.api-permission-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
}

.api-templates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
