<template>
  <ElDrawer
    v-model="visible"
    :title="dialogType === 'add' ? $t('user.addUser', '新增用户') : $t('user.editUser', '编辑用户')"
    size="480px"
    :destroy-on-close="false"
    class="edit-drawer"
    @close="handleClose"
  >
    <ElForm ref="formRef" :model="form" :rules="rules" label-width="90px" label-position="left">
      <ElFormItem :label="$t('user.username', '用户名')" prop="username">
        <ElInput
          v-model="form.username"
          :placeholder="$t('common.pleaseInput', '请输入') + $t('user.username', '用户名')"
          :disabled="dialogType === 'edit'"
        />
      </ElFormItem>
      
      <ElFormItem v-if="dialogType === 'add'" :label="$t('user.password', '密码')" prop="password">
        <ElInput
          v-model="form.password"
          type="password"
          :placeholder="$t('common.pleaseInput', '请输入') + $t('user.password', '密码')"
          show-password
        />
      </ElFormItem>
      
      <ElFormItem :label="$t('user.nickname', '昵称')" prop="nickname">
        <ElInput v-model="form.nickname" :placeholder="$t('common.pleaseInput', '请输入') + $t('user.nickname', '昵称')" />
      </ElFormItem>
      
      <ElFormItem :label="$t('user.email', '邮箱')" prop="email">
        <ElInput v-model="form.email" :placeholder="$t('common.pleaseInput', '请输入') + $t('user.email', '邮箱')" />
      </ElFormItem>
      
      <ElFormItem :label="$t('user.phone', '手机')" prop="phone">
        <ElInput v-model="form.phone" :placeholder="$t('common.pleaseInput', '请输入') + $t('user.phone', '手机')" />
      </ElFormItem>
      
      <ElFormItem :label="$t('common.department', '部门')" prop="department_id">
        <ElTreeSelect
          v-model="form.department_id"
          :data="departmentTree"
          :props="{ label: 'name', value: 'id', children: 'children' }"
          :placeholder="$t('common.pleaseSelect', '请选择') + $t('common.department', '部门')"
          check-strictly
          clearable
          style="width: 100%"
        />
      </ElFormItem>
      
      <ElFormItem :label="$t('user.userType', '用户身份')" prop="user_type">
        <ElSelect v-model="form.user_type" :placeholder="$t('user.selectUserType', '请选择用户身份')" style="width: 100%">
          <ElOption
            v-for="option in userTypeOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </ElSelect>
      </ElFormItem>
      
      <ElFormItem :label="$t('user.gender', '性别')" prop="gender">
        <ElRadioGroup v-model="form.gender">
          <ElRadio :value="1">{{ $t('user.male', '男') }}</ElRadio>
          <ElRadio :value="0">{{ $t('user.female', '女') }}</ElRadio>
        </ElRadioGroup>
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
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { fetchDepartmentTree } from '@/api/system/department'
import type { DepartmentTree } from '@/typings/department'
import { addUser, updateUser, type UserInfo, type AddUserParams, type UpdateUserParams } from '@/api/system/user'
import { getAssignableUserTypes } from '@/utils/permission'
import { useUserStore } from '@/store/modules/user'

const { t } = useI18n()
const userStore = useUserStore()

interface Props {
  modelValue: boolean
  dialogType: 'add' | 'edit'
  userData?: UserInfo
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
  userData: undefined,
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
const departmentTree = ref<DepartmentTree[]>([])

// 根据当前用户身份获取可分配的用户身份选项
const userTypeOptions = computed(() => {
  const currentUserType = userStore.info?.user_type ?? 3
  return getAssignableUserTypes(currentUserType)
})

const rules = reactive<FormRules>({
  username: [
    { required: true, message: t('user.usernameRequired', '请输入用户名'), trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('user.passwordRequired', '请输入密码'), trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: t('user.nicknameRequired', '请输入昵称'), trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: t('user.emailFormat', '请输入正确的邮箱格式'), trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: t('user.phoneFormat', '请输入正确的手机号格式'), trigger: 'blur' }
  ],
  department_id: [
    { required: true, message: t('user.departmentRequired', '请选择部门'), trigger: 'change' }
  ],
  user_type: [
    { required: true, message: t('user.userTypeRequired', '请选择用户身份'), trigger: 'change' }
  ]
})

interface FormData {
  username: string
  password: string
  nickname: string
  email: string
  phone: string
  gender: number
  status: number
  user_type: number
  department_id: string
}

const defaultForm: FormData = {
  username: '',
  password: '',
  nickname: '',
  email: '',
  phone: '',
  gender: 1,
  status: 1,
  user_type: 3,
  department_id: ''
}

const form = reactive<FormData>({ ...defaultForm })

watch(visible, (newVisible) => {
  if (newVisible) {
    nextTick(() => {
      resetForm()
      if (props.dialogType === 'edit' && props.userData) {
        Object.assign(form, {
          username: props.userData.username,
          nickname: props.userData.nickname || '',
          email: props.userData.email || '',
          phone: props.userData.phone || '',
          gender: props.userData.gender || 1,
          status: props.userData.status || 1,
          user_type: props.userData.user_type ?? 3,
          department_id: props.userData.department_id || ''
        })
      } else if (props.departmentId) {
        form.department_id = props.departmentId
      }
    })
  }
})

const loadDepartmentTree = async () => {
  try {
    const response = await fetchDepartmentTree()
    if (response.success && response.data) {
      departmentTree.value = response.data.result || []
    }
  } catch (error) {
    console.error('加载部门选项失败:', error)
  }
}

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

    if (props.dialogType === 'add') {
      const params: AddUserParams = {
        username: form.username,
        password: form.password,
        nickname: form.nickname,
        email: form.email || undefined,
        phone: form.phone || undefined,
        gender: form.gender,
        status: form.status,
        user_type: form.user_type,
        department_id: form.department_id
      }
      await addUser(params)
      ElMessage.success(t('user.addUserSuccess', '新增用户成功'))
    } else {
      const params: UpdateUserParams = {
        username: form.username,
        nickname: form.nickname || undefined,
        email: form.email || undefined,
        phone: form.phone || undefined,
        gender: form.gender,
        status: form.status,
        user_type: form.user_type,
        department_id: form.department_id || undefined
      }
      await updateUser(props.userData!.id, params)
      ElMessage.success(t('user.updateUserSuccess', '更新用户成功'))
    }

    emit('success')
    handleClose()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadDepartmentTree()
})
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
