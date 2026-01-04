<template>
  <ElDrawer
    :model-value="modelValue"
    :title="drawerTitle"
    size="700px"
    :before-close="handleClose"
    @open="handleOpen"
    @update:model-value="emit('update:modelValue', $event)"
    class="notification-drawer"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      :disabled="formLoading"
    >
      <ElFormItem label="通知标题" prop="title">
        <ElInput v-model="formData.title" placeholder="请输入通知标题" maxlength="100" show-word-limit />
      </ElFormItem>

      <ElFormItem label="通知类型" prop="type">
        <ElSelect v-model="formData.type" placeholder="请选择通知类型" style="width: 100%">
          <ElOption label="全局公告" :value="1" />
          <ElOption label="系统消息" :value="2" />
        </ElSelect>
      </ElFormItem>

      <ElFormItem label="通知范围" prop="scope">
        <ElSelect v-model="formData.scope" placeholder="请选择通知范围" style="width: 100%" @change="handleScopeChange">
          <ElOption label="全部用户" :value="0" />
          <ElOption label="指定部门" :value="1" />
          <ElOption label="指定用户" :value="2" />
        </ElSelect>
      </ElFormItem>

      <ElFormItem v-if="formData.scope === 1" label="选择部门" prop="scope_ids">
        <ElTreeSelect
          v-model="formData.scope_ids"
          :data="departmentTree"
          :props="{ label: 'name', value: 'id', children: 'children' }"
          multiple
          filterable
          check-strictly
          placeholder="请选择部门"
          style="width: 100%"
        />
      </ElFormItem>

      <ElFormItem v-if="formData.scope === 2" label="选择用户" prop="scope_ids">
        <ElSelect
          v-model="formData.scope_ids"
          multiple
          filterable
          remote
          :remote-method="searchUsers"
          :loading="userLoading"
          placeholder="请输入用户名搜索"
          style="width: 100%"
        >
          <ElOption
            v-for="user in userOptions"
            :key="user.id"
            :label="`${user.nickname} (${user.username})`"
            :value="user.id"
          />
        </ElSelect>
      </ElFormItem>

      <ElFormItem label="优先级" prop="priority">
        <ElRadioGroup v-model="formData.priority">
          <ElRadio :value="0">普通</ElRadio>
          <ElRadio :value="1">重要</ElRadio>
          <ElRadio :value="2">紧急</ElRadio>
        </ElRadioGroup>
      </ElFormItem>

      <ElFormItem label="过期时间" prop="expire_time">
        <ElDatePicker
          v-model="formData.expire_time"
          type="datetime"
          placeholder="选择过期时间（可选）"
          style="width: 100%"
          :disabled-date="disabledDate"
        />
      </ElFormItem>

      <ElFormItem label="通知内容" prop="content">
        <ArtWangEditor
          v-model="formData.content"
          height="300px"
          placeholder="请输入通知内容..."
          :exclude-keys="['fullScreen', 'group-video']"
        />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <ElButton round @click="handleClose">取消</ElButton>
      <ElButton round type="primary" :loading="submitLoading" @click="handleSubmit">保存</ElButton>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { fetchDepartmentTree } from '@/api/system/department'
import { fetchUserList } from '@/api/system/user'
import {
  createNotification,
  updateNotification,
  type NotificationInfo,
  type CreateNotificationParams
} from '@/api/system/notification'

interface Props {
  modelValue: boolean
  dialogType: 'add' | 'edit'
  notificationData?: NotificationInfo
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const formLoading = ref(false)
const submitLoading = ref(false)
const departmentTree = ref<any[]>([])
const userOptions = ref<any[]>([])
const userLoading = ref(false)

const formData = ref<CreateNotificationParams>({
  title: '',
  content: '',
  type: 1,
  scope: 0,
  scope_ids: [],
  priority: 0,
  expire_time: undefined
})

const formRules = {
  title: [{ required: true, message: '请输入通知标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入通知内容', trigger: 'blur' }],
  type: [{ required: true, message: '请选择通知类型', trigger: 'change' }],
  scope: [{ required: true, message: '请选择通知范围', trigger: 'change' }],
  scope_ids: [{
    validator: (_: any, value: string[], callback: Function) => {
      if ((formData.value.scope === 1 || formData.value.scope === 2) && (!value || value.length === 0)) {
        callback(new Error(formData.value.scope === 1 ? '请选择部门' : '请选择用户'))
      } else {
        callback()
      }
    },
    trigger: 'change'
  }]
}

const drawerTitle = computed(() => props.dialogType === 'add' ? '新建通知' : '编辑通知')

const disabledDate = (date: Date) => {
  return date.getTime() < Date.now() - 24 * 60 * 60 * 1000
}

const loadDepartmentTree = async () => {
  try {
    const res = await fetchDepartmentTree()
    if (res.success && res.data) {
      departmentTree.value = res.data.result || []
    }
  } catch (e) {
    console.error('加载部门树失败:', e)
  }
}

const searchUsers = async (query: string) => {
  if (!query) {
    userOptions.value = []
    return
  }
  try {
    userLoading.value = true
    const res = await fetchUserList({ username: query, pageSize: 20 })
    if (res.success && res.data) {
      userOptions.value = res.data.result || []
    }
  } catch (e) {
    console.error('搜索用户失败:', e)
  } finally {
    userLoading.value = false
  }
}

const handleScopeChange = () => {
  formData.value.scope_ids = []
}

const handleOpen = () => {
  loadDepartmentTree()
  
  if (props.dialogType === 'edit' && props.notificationData) {
    formData.value = {
      title: props.notificationData.title,
      content: props.notificationData.content,
      type: props.notificationData.type,
      scope: props.notificationData.scope,
      scope_ids: props.notificationData.scope_ids || [],
      priority: props.notificationData.priority,
      expire_time: props.notificationData.expire_time
    }
  } else {
    resetForm()
  }
}

const resetForm = () => {
  formData.value = {
    title: '',
    content: '',
    type: 1,
    scope: 0,
    scope_ids: [],
    priority: 0,
    expire_time: undefined
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

    const submitData = { ...formData.value }
    if (submitData.expire_time) {
      submitData.expire_time = new Date(submitData.expire_time).toISOString()
    }

    let res
    if (props.dialogType === 'add') {
      res = await createNotification(submitData)
    } else {
      res = await updateNotification(props.notificationData!.id, submitData)
    }

    if (res.success) {
      ElMessage.success('保存成功')
      emit('success')
      handleClose()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    submitLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.notification-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
  
  :deep(.editor-wrapper) {
    width: 100%;
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    overflow: hidden;
  }
}
</style>
