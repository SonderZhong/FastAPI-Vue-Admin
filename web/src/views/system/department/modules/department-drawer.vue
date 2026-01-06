<template>
  <ElDrawer
    v-model="visible"
    :title="dialogType === 'add' ? $t('department.addDepartment', '新增部门') : $t('department.editDepartment', '编辑部门')"
    size="480px"
    :destroy-on-close="false"
    class="dept-drawer"
    @open="handleOpen"
    @close="handleClose"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="90px"
      label-position="left"
      :disabled="formLoading"
    >
      <ElFormItem :label="$t('department.name', '部门名称')" prop="name">
        <ElInput v-model="formData.name" :placeholder="$t('common.pleaseInput', '请输入') + $t('department.name', '部门名称')" />
      </ElFormItem>

      <ElFormItem :label="$t('department.parent', '上级部门')" prop="parent_id">
        <ElTreeSelect
          v-model="formData.parent_id"
          :data="departmentTree"
          :props="({ label: 'name', value: 'id', children: 'children' } as any)"
          :placeholder="$t('common.pleaseSelect', '请选择') + $t('department.parent', '上级部门')"
          check-strictly
          clearable
          style="width: 100%"
        />
      </ElFormItem>

      <ElFormItem :label="$t('department.principal', '负责人')" prop="principal">
        <ElInput v-model="formData.principal" :placeholder="$t('common.pleaseInput', '请输入') + $t('department.principal', '负责人')" />
      </ElFormItem>

      <ElFormItem :label="$t('department.phone', '联系电话')" prop="phone">
        <ElInput v-model="formData.phone" :placeholder="$t('common.pleaseInput', '请输入') + $t('department.phone', '联系电话')" />
      </ElFormItem>

      <ElFormItem :label="$t('department.email', '邮箱')" prop="email">
        <ElInput v-model="formData.email" :placeholder="$t('common.pleaseInput', '请输入') + $t('department.email', '邮箱')" />
      </ElFormItem>

      <ElFormItem :label="$t('department.sort', '排序')" prop="sort">
        <ElInputNumber v-model="formData.sort" :min="0" controls-position="right" style="width: 100%" />
      </ElFormItem>

      <ElFormItem :label="$t('common.status', '状态')" prop="status">
        <ElSwitch
          v-model="formData.status"
          :active-value="0"
          :inactive-value="1"
          :active-text="$t('common.normal', '正常')"
          :inactive-text="$t('common.disabled', '停用')"
        />
      </ElFormItem>

      <ElFormItem :label="$t('common.remark', '备注')" prop="remark">
        <ElInput v-model="formData.remark" type="textarea" :placeholder="$t('common.pleaseInput', '请输入') + $t('common.remark', '备注')" :rows="3" />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <div class="drawer-footer">
        <ElButton round @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" round :loading="submitLoading" @click="handleSubmit">{{ $t('buttons.confirm', '确定') }}</ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { fetchDepartmentTree, addDepartment, updateDepartment } from '@/api/system/department'
import type { DepartmentInfo, DepartmentTree } from '@/typings/department'

const { t } = useI18n()

interface Props {
  modelValue: boolean
  dialogType: 'add' | 'edit'
  departmentData?: Partial<DepartmentInfo>
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  dialogType: 'add',
  departmentData: undefined
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref<FormInstance>()
const formLoading = ref(false)
const submitLoading = ref(false)
const departmentTree = ref<DepartmentTree[]>([])

const formData = ref({
  name: '',
  parent_id: undefined as string | undefined,
  sort: 0,
  phone: null as string | null,
  principal: '',
  email: null as string | null,
  remark: null as string | null,
  status: 0 as number
})

const formRules: FormRules = {
  name: [{ required: true, message: t('department.nameRequired', '请输入部门名称'), trigger: 'blur' }],
  principal: [{ required: true, message: t('department.principalRequired', '请输入负责人'), trigger: 'blur' }]
}

const handleOpen = async () => {
  await loadDepartments()
  
  if (props.dialogType === 'edit' && props.departmentData) {
    formData.value = {
      name: props.departmentData.name || '',
      parent_id: props.departmentData.parent_id || undefined,
      sort: props.departmentData.sort || 0,
      phone: props.departmentData.phone || null,
      principal: props.departmentData.principal || '',
      email: props.departmentData.email || null,
      remark: props.departmentData.remark || null,
      status: props.departmentData.status || 0
    }
  } else {
    resetForm()
    if (props.departmentData?.parent_id) {
      formData.value.parent_id = props.departmentData.parent_id
    }
  }
}

const resetForm = () => {
  formData.value = {
    name: '',
    parent_id: undefined,
    sort: 0,
    phone: null,
    principal: '',
    email: null,
    remark: null,
    status: 0
  }
  formRef.value?.clearValidate()
}

const loadDepartments = async () => {
  try {
    formLoading.value = true
    const response = await fetchDepartmentTree()
    if (response.success && response.data) {
      const departments = response.data.result || []
      departmentTree.value = filterTree(departments, props.dialogType === 'edit' ? props.departmentData?.id : undefined)
    }
  } catch (error) {
    console.error('加载部门数据失败:', error)
    ElMessage.error('加载部门数据失败')
  } finally {
    formLoading.value = false
  }
}

const filterTree = (treeData: DepartmentTree[], excludeId?: string): DepartmentTree[] => {
  const processNode = (node: DepartmentTree): DepartmentTree | null => {
    if (excludeId && node.id === excludeId) return null
    
    const processedNode: DepartmentTree = { ...node, children: [] }
    
    if (node.children && node.children.length > 0) {
      const validChildren = node.children
        .map((child) => processNode(child))
        .filter((child) => child !== null) as DepartmentTree[]
      if (validChildren.length > 0) {
        processedNode.children = validChildren
      }
    }
    
    return processedNode
  }
  
  return treeData.map((node) => processNode(node)).filter((node) => node !== null) as DepartmentTree[]
}

const handleClose = () => {
  visible.value = false
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    const submitData = {
      ...formData.value,
      parent_id: formData.value.parent_id || null
    }

    if (props.dialogType === 'add') {
      const response = await addDepartment(submitData)
      if (response.success) {
        ElMessage.success(t('department.addSuccess', '新增部门成功'))
        emit('success')
        handleClose()
      } else {
        ElMessage.error(response.msg || t('department.addFailed', '新增部门失败'))
      }
    } else {
      if (props.departmentData?.id) {
        const response = await updateDepartment(props.departmentData.id, submitData)
        if (response.success) {
          ElMessage.success(t('department.updateSuccess', '编辑部门成功'))
          emit('success')
          handleClose()
        } else {
          ElMessage.error(response.msg || t('department.updateFailed', '编辑部门失败'))
        }
      }
    }
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.message || t('common.operationFailed', '操作失败'))
  } finally {
    submitLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.dept-drawer {
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
