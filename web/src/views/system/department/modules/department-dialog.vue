<template>
  <ElDialog
    :model-value="props.visible"
    :title="dialogTitle"
    width="600px"
    :before-close="handleClose"
    @open="handleOpen"
    @update:model-value="(val) => emit('update:visible', val)"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      :disabled="formLoading"
    >
      <ElRow :gutter="20">
        <ElCol :span="24">
          <ElFormItem label="部门名称" prop="name">
            <ElInput v-model="formData.name" placeholder="请输入部门名称" />
          </ElFormItem>
        </ElCol>

        <ElCol :span="24">
          <ElFormItem label="上级部门" prop="parent_id">
            <ElCascader
              v-model="formData.parent_id"
              :options="departmentTree"
              :props="cascaderProps"
              placeholder="请选择上级部门"
              clearable
              style="width: 100%"
            />
          </ElFormItem>
        </ElCol>

        <ElCol :span="12">
          <ElFormItem label="负责人" prop="principal">
            <ElInput v-model="formData.principal" placeholder="请输入负责人" />
          </ElFormItem>
        </ElCol>

        <ElCol :span="12">
          <ElFormItem label="电话" prop="phone">
            <ElInput v-model="formData.phone" placeholder="请输入电话" />
          </ElFormItem>
        </ElCol>

        <ElCol :span="12">
          <ElFormItem label="邮箱" prop="email">
            <ElInput v-model="formData.email" placeholder="请输入邮箱" />
          </ElFormItem>
        </ElCol>

        <ElCol :span="12">
          <ElFormItem label="排序" prop="sort">
            <ElInputNumber
              v-model="formData.sort"
              :min="0"
              controls-position="right"
              style="width: 100%"
            />
          </ElFormItem>
        </ElCol>

        <ElCol :span="12">
          <ElFormItem label="状态" prop="status">
            <ElSwitch
              v-model="formData.status"
              :active-value="0"
              :inactive-value="1"
              active-text="正常"
              inactive-text="停用"
            />
          </ElFormItem>
        </ElCol>

        <ElCol :span="24">
          <ElFormItem label="备注" prop="remark">
            <ElInput v-model="formData.remark" type="textarea" placeholder="请输入备注" :rows="3" />
          </ElFormItem>
        </ElCol>
      </ElRow>
    </ElForm>

    <template #footer>
      <ElButton @click="handleClose">取消</ElButton>
      <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">确定</ElButton>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ElMessage, FormInstance } from 'element-plus'
  import { fetchDepartmentTree, addDepartment, updateDepartment } from '@/api/system/department'
  import type { DepartmentInfo, DepartmentTree } from '@/typings/department'

  interface Props {
    visible: boolean
    type: Form.DialogType
    departmentData?: Partial<DepartmentInfo>
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'submit'): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()

  // 表单相关
  const formRef = ref<FormInstance>()
  const formLoading = ref(false)
  const submitLoading = ref(false)

  // 表单数据
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

  // 表单验证规则
  const formRules = ref({
    name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
    principal: [{ required: true, message: '请输入负责人', trigger: 'blur' }]
  })

  // 级联选择器配置
  const cascaderProps = {
    value: 'id',
    label: 'name',
    children: 'children',
    emitPath: false,
    checkStrictly: true
  }

  // 部门树形结构
  const departmentTree = ref<DepartmentTree[]>([])

  // 对话框标题
  const dialogTitle = computed(() => {
    return props.type === 'add' ? '新增部门' : '编辑部门'
  })

  // 监听visible变化
  watch(
    () => props.visible,
    (val) => {
      if (val) {
        loadDepartments()
      }
    }
  )

  // 处理对话框打开
  const handleOpen = () => {
    if (props.type === 'edit' && props.departmentData) {
      // 编辑模式，填充表单数据
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
      // 新增模式，重置表单并设置预设值
      resetForm()

      // 如果有预设的上级部门，设置parent_id
      if (props.departmentData?.parent_id) {
        formData.value.parent_id = props.departmentData.parent_id
      }
    }
  }

  // 重置表单
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

  // 加载部门数据
  const loadDepartments = async () => {
    try {
      formLoading.value = true
      const response = await fetchDepartmentTree()

      // 检查响应是否成功
      if (!response.success || !response.data) {
        throw new Error(response.msg || '加载部门数据失败')
      }

      const departments = response.data?.result || []

      // 将树形数据转换为级联选择器的格式，并排除当前编辑的部门
      departmentTree.value = convertTreeToCascader(
        departments,
        props.type === 'edit' ? props.departmentData?.id : undefined
      )
    } catch (error) {
      console.error('加载部门数据失败:', error)
      ElMessage.error('加载部门数据失败')
    } finally {
      formLoading.value = false
    }
  }

  // 将树形数据转换为级联选择器的格式
  const convertTreeToCascader = (
    treeData: DepartmentTree[],
    excludeId?: string
  ): DepartmentTree[] => {
    const processNode = (node: DepartmentTree): DepartmentTree | null => {
      // 如果是编辑模式，排除当前部门
      if (excludeId && node.id === excludeId) {
        return null
      }

      const processedNode: DepartmentTree = {
        ...node,
        children: []
      }

      // 递归处理子节点
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

    return treeData
      .map((node) => processNode(node))
      .filter((node) => node !== null) as DepartmentTree[]
  }

  // 处理对话框关闭
  const handleClose = () => {
    emit('update:visible', false)
  }

  // 处理表单提交
  const handleSubmit = async () => {
    if (!formRef.value) return

    try {
      await formRef.value.validate()
      submitLoading.value = true

      // 转换数据格式
      const submitData = {
        ...formData.value,
        parent_id: formData.value.parent_id || null
      }

      // 根据类型调用不同的API
      if (props.type === 'add') {
        const response = await addDepartment(submitData)

        // 检查响应是否成功
        if (!response.success) {
          throw new Error(response.msg || '新增部门失败')
        }

        ElMessage.success(response.msg || '新增部门成功')
      } else {
        if (props.departmentData?.id) {
          const response = await updateDepartment(props.departmentData.id, submitData)

          // 检查响应是否成功
          if (!response.success) {
            throw new Error(response.msg || '编辑部门失败')
          }

          ElMessage.success(response.msg || '编辑部门成功')
        }
      }

      // 关闭对话框并触发submit事件
      handleClose()
      emit('submit')
    } catch (error: any) {
      console.error('提交失败:', error)
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitLoading.value = false
    }
  }
</script>

<style lang="scss" scoped>
  .el-dialog__body {
    padding: 20px;
  }
</style>
