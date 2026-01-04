<template>
  <ElDrawer
    v-model="visible"
    :title="dialogType === 'add' ? $t('role.addRole', '新增角色') : $t('buttons.edit', '编辑角色')"
    size="400px"
    :destroy-on-close="false"
    class="edit-drawer"
    @close="handleClose"
  >
    <ElForm ref="formRef" :model="form" :rules="rules" label-width="80px" label-position="left">
      <ElFormItem :label="$t('role.roleName', '角色名称')" prop="name">
        <ElInput v-model="form.name" :placeholder="$t('common.pleaseInput', '请输入') + $t('role.roleName', '角色名称')" />
      </ElFormItem>
      <ElFormItem :label="$t('role.roleCode', '角色编码')" prop="code">
        <ElInput v-model="form.code" :placeholder="$t('common.pleaseInput', '请输入') + $t('role.roleCode', '角色编码')" />
      </ElFormItem>
      <ElFormItem :label="$t('common.department', '所属部门')" prop="department_id">
        <ElInput v-model="form.department_name" disabled />
      </ElFormItem>
      <ElFormItem :label="$t('common.description', '描述')" prop="description">
        <ElInput v-model="form.description" type="textarea" :rows="3" :placeholder="$t('common.pleaseInput', '请输入') + $t('common.description', '描述')" />
      </ElFormItem>
      <ElFormItem :label="$t('common.status', '状态')">
        <ElSwitch v-model="form.status" :active-value="1" :inactive-value="0" />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <div class="drawer-footer">
        <ElButton round @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" round :loading="submitting" @click="handleSubmit">{{ $t('buttons.confirm', '确定') }}</ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { addRole, updateRole, type RoleInfo } from '@/api/system/role'

const { t } = useI18n()

interface Props {
  modelValue: boolean
  dialogType: 'add' | 'edit'
  roleData?: RoleInfo
  departmentId?: string
  departmentName?: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  dialogType: 'add',
  roleData: undefined,
  departmentId: undefined,
  departmentName: undefined
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref<FormInstance>()
const submitting = ref(false)

const rules = reactive<FormRules>({
  name: [
    { required: true, message: t('common.pleaseInput', '请输入') + t('role.roleName', '角色名称'), trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: t('common.pleaseInput', '请输入') + t('role.roleCode', '角色编码'), trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
})

const defaultForm = {
  id: '',
  name: '',
  code: '',
  description: '',
  status: 1,
  department_id: '',
  department_name: '',
  created_at: '',
  updated_at: ''
}

const form = reactive<RoleInfo>({ ...defaultForm })

watch(visible, (newVisible) => {
  if (newVisible) {
    nextTick(() => {
      resetForm()
      if (props.dialogType === 'edit' && props.roleData) {
        Object.assign(form, props.roleData)
      } else if (props.departmentId) {
        form.department_id = props.departmentId
        form.department_name = props.departmentName || ''
      }
    })
  }
})

const resetForm = () => {
  Object.assign(form, defaultForm)
  formRef.value?.clearValidate()
}

const handleClose = () => {
  visible.value = false
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    const submitData = {
      name: form.name,
      code: form.code,
      description: form.description || '',
      status: form.status,
      department_id: form.department_id
    }

    if (props.dialogType === 'add' && !submitData.department_id) {
      ElMessage.error('请先选择部门')
      return
    }

    let response
    if (props.dialogType === 'add') {
      response = await addRole(submitData)
    } else {
      response = await updateRole(form.id!, { ...submitData, id: form.id! })
    }

    if (response.success) {
      ElMessage.success(props.dialogType === 'add' ? t('common.addSuccess', '新增成功') : t('common.updateSuccess', '修改成功'))
      emit('success')
      handleClose()
    } else {
      ElMessage.error(response.msg || t('common.operationFailed', '操作失败'))
    }
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.edit-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
  
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  :deep(.el-drawer__body) {
    padding: 20px;
  }
  
  :deep(.el-drawer__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

.drawer-footer {
  display: flex;
  gap: 12px;
  
  .el-button {
    flex: 1;
  }
}
</style>
