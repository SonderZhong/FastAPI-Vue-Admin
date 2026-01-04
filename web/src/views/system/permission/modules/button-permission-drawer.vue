<template>
  <ElDrawer
    :model-value="modelValue"
    :title="drawerTitle"
    size="450px"
    :before-close="handleClose"
    @open="handleOpen"
    @update:model-value="emit('update:modelValue', $event)"
    class="button-permission-drawer"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      :disabled="formLoading"
    >
      <ElFormItem :label="$t('permission.buttonName')" prop="authTitle">
        <ElInput v-model="formData.authTitle" :placeholder="$t('common.pleaseInput')" />
      </ElFormItem>

      <ElFormItem :label="$t('permission.permissionMark')" prop="authMark">
        <ElInput v-model="formData.authMark" placeholder="user:btn:add" />
        <template #extra>
          <div class="text-xs text-gray-500 mt-1">
            {{ $t('permission.authMarkTip') }}
          </div>
        </template>
      </ElFormItem>

      <ElFormItem :label="$t('common.permissionName')" prop="name">
        <ElInput v-model="formData.name" :placeholder="$t('common.pleaseInput')" />
        <template #extra>
          <div class="text-xs text-gray-500 mt-1">{{ $t('permission.nameEnglishTip') }}</div>
        </template>
      </ElFormItem>

      <ElFormItem :label="$t('common.displayName')" prop="title">
        <ElInput v-model="formData.title" :placeholder="$t('common.pleaseInput')" />
      </ElFormItem>

      <ElFormItem :label="$t('common.sort')" prop="order">
        <ElInputNumber v-model="formData.order" :min="0" :max="9999" style="width: 100%" />
      </ElFormItem>

      <ElFormItem :label="$t('permission.minUserType')" prop="min_user_type">
        <ElSelect v-model="formData.min_user_type" :placeholder="$t('common.pleaseSelect')" style="width: 100%">
          <ElOption :label="$t('login.roles.super')" :value="0" />
          <ElOption :label="$t('login.roles.admin')" :value="1" />
          <ElOption :label="$t('permission.deptAdmin')" :value="2" />
          <ElOption :label="$t('permission.allUsers')" :value="3" />
        </ElSelect>
      </ElFormItem>
    </ElForm>

    <template #footer>
      <ElButton round @click="handleClose">{{ $t('common.cancel') }}</ElButton>
      <ElButton round type="primary" :loading="submitLoading" @click="handleSubmit">{{ $t('common.confirm') }}</ElButton>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { addButtonPermission, updateButtonPermission } from '@/api/system/permission'
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
  name: '',
  title: '',
  authTitle: '',
  authMark: '',
  order: 999,
  min_user_type: 3
})

const formRules = computed(() => ({
  authTitle: [{ required: true, message: t('permission.authTitleRequired'), trigger: 'blur' }],
  authMark: [
    { required: true, message: t('permission.authMarkRequired'), trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_:]*$/, message: t('permission.authMarkPattern'), trigger: 'blur' }
  ],
  name: [
    { required: true, message: t('common.pleaseInput'), trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: t('permission.namePattern'), trigger: 'blur' }
  ]
}))

const drawerTitle = computed(() => props.dialogType === 'add' ? t('permission.addButtonPermission') : t('permission.editButtonPermission'))

const handleOpen = () => {
  if (props.dialogType === 'edit' && props.permissionData) {
    formData.value = {
      name: props.permissionData.name || '',
      title: props.permissionData.title || '',
      authTitle: props.permissionData.authTitle || '',
      authMark: props.permissionData.authMark || '',
      order: props.permissionData.order || 999,
      min_user_type: props.permissionData.min_user_type ?? 3
    }
  } else {
    resetForm()
  }
}

const resetForm = () => {
  formData.value = {
    name: '',
    title: '',
    authTitle: '',
    authMark: '',
    order: 999,
    min_user_type: 3
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

    const submitData: any = {
      ...formData.value,
      menu_type: 1,
      parent_id: props.parentId
    }

    // 清理空值
    Object.keys(submitData).forEach(key => {
      if (submitData[key] === '' || submitData[key] === null || submitData[key] === undefined) {
        delete submitData[key]
      }
    })

    let res
    if (props.dialogType === 'add') {
      res = await addButtonPermission(submitData)
    } else {
      res = await updateButtonPermission(props.permissionData!.id!, submitData)
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

// 自动生成权限名称
watch(() => formData.value.authMark, (newVal) => {
  if (newVal && !formData.value.name) {
    const parts = newVal.split(':')
    if (parts.length >= 3) {
      formData.value.name = parts.join('_')
    }
  }
})
</script>

<style lang="scss" scoped>
.button-permission-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
}
</style>
