<template>
  <ElDialog
    v-model="visible"
    :title="dialogType === 'add' ? '新增角色' : '编辑角色'"
    width="30%"
    align-center
    @close="handleClose"
  >
    <ElForm ref="formRef" :model="form" :rules="rules" label-width="120px">
      <ElFormItem label="角色名称" prop="name">
        <ElInput v-model="form.name" />
      </ElFormItem>
      <ElFormItem label="角色编码" prop="code">
        <ElInput v-model="form.code" />
      </ElFormItem>
      <ElFormItem label="所属部门" prop="department_id">
        <ElInput v-model="form.department_name" disabled />
      </ElFormItem>
      <ElFormItem label="描述" prop="description">
        <ElInput v-model="form.description" type="textarea" :rows="3" />
      </ElFormItem>
      <ElFormItem label="状态">
        <ElSwitch v-model="form.status" :active-value="1" :inactive-value="0" />
      </ElFormItem>
    </ElForm>
    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">取消</ElButton>
        <ElButton type="primary" @click="handleSubmit">提交</ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, reactive, computed, watch, nextTick } from 'vue'
  import { ElMessage } from 'element-plus'
  import type { FormInstance, FormRules } from 'element-plus'
  import { addRole, updateRole, type RoleInfo } from '@/api/system/role'

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

  const rules = reactive<FormRules>({
    name: [
      { required: true, message: '请输入角色名称', trigger: 'blur' },
      { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
    ],
    code: [
      { required: true, message: '请输入角色编码', trigger: 'blur' },
      { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    department_id: [{ required: true, message: '请选择所属部门', trigger: 'change' }],
    description: [{ required: false, message: '请输入角色描述', trigger: 'blur' }]
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

  // 监听对话框打开
  watch(visible, (newVisible) => {
    if (newVisible) {
      nextTick(() => {
        resetForm()
        if (props.dialogType === 'edit' && props.roleData) {
          Object.assign(form, props.roleData)
        } else if (props.departmentId) {
          form.department_id = props.departmentId
          form.department_name = props.departmentName || '未知部门'
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

      const submitData = {
        name: form.name,
        code: form.code,
        description: form.description || '',
        status: form.status,
        department_id: form.department_id
      }

      console.log('提交角色数据:', submitData)
      console.log('对话框类型:', props.dialogType)
      console.log('部门ID:', props.departmentId)

      // 确保添加角色时有department_id
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
        ElMessage.success(props.dialogType === 'add' ? '新增成功' : '修改成功')
        emit('success')
        handleClose()
      } else {
        ElMessage.error(response.msg || '操作失败')
      }
    } catch (error) {
      console.error('提交失败:', error)
      ElMessage.error('操作失败')
    }
  }
</script>

<style lang="scss" scoped>
  .dialog-footer {
    text-align: right;
  }
</style>
