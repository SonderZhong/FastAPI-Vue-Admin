<template>
  <ElDialog
    v-model="dialogVisible"
    :title="type === 'add' ? $t('user.addUser') : $t('user.editUser')"
    width="600px"
    :before-close="handleClose"
  >
    <ElForm ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="right">
      <ElRow :gutter="20">
        <ElCol :span="12">
          <ElFormItem :label="$t('user.username')" prop="username">
            <ElInput
              v-model="form.username"
              :placeholder="$t('user.username')"
              :disabled="type === 'edit'"
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.nickname')" prop="nickname">
            <ElInput v-model="form.nickname" :placeholder="$t('user.nickname')" />
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" v-if="type === 'add'">
        <ElCol :span="12">
          <ElFormItem :label="$t('user.password')" prop="password">
            <ElInput
              v-model="form.password"
              type="password"
              :placeholder="$t('user.password')"
              show-password
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.gender')" prop="gender">
            <ElRadioGroup v-model="form.gender">
              <ElRadio :value="1">{{ $t('user.male') }}</ElRadio>
              <ElRadio :value="0">{{ $t('user.female') }}</ElRadio>
            </ElRadioGroup>
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" v-else>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.gender')" prop="gender">
            <ElRadioGroup v-model="form.gender">
              <ElRadio :value="1">{{ $t('user.male') }}</ElRadio>
              <ElRadio :value="0">{{ $t('user.female') }}</ElRadio>
            </ElRadioGroup>
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('common.status')" prop="status">
            <ElSwitch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
              :active-text="$t('common.enabled')"
              :inactive-text="$t('common.disabled')"
            />
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20">
        <ElCol :span="12">
          <ElFormItem :label="$t('user.email')" prop="email">
            <ElInput v-model="form.email" :placeholder="$t('user.email')" />
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.phone')" prop="phone">
            <ElInput v-model="form.phone" :placeholder="$t('user.phone')" />
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20">
        <ElCol :span="12">
          <ElFormItem :label="$t('common.department')" prop="department_id">
            <ElSelect
              v-model="form.department_id"
              :placeholder="$t('common.department')"
              style="width: 100%"
              clearable
            >
              <ElOption
                v-for="dept in departmentOptions"
                :key="dept.value"
                :label="dept.label"
                :value="dept.value"
              />
            </ElSelect>
          </ElFormItem>
        </ElCol>
      </ElRow>
    </ElForm>

    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" @click="handleSubmit" :loading="loading">
          {{ $t('common.confirm') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, computed, watch, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import type { FormInstance, FormRules } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { fetchDepartmentTree } from '@/api/system/department'
  import type { DepartmentTree } from '@/typings/department'
  import {
    addUser,
    updateUser,
    type UserInfo,
    type AddUserParams,
    type UpdateUserParams
  } from '@/api/system/user'

  const { t: $t } = useI18n()

  interface Props {
    visible: boolean
    type: 'add' | 'edit'
    userData?: UserInfo
    departmentId?: string
    departmentName?: string
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'submit'): void
  }

  const props = withDefaults(defineProps<Props>(), {
    visible: false,
    type: 'add'
  })

  const emit = defineEmits<Emits>()

  const loading = ref(false)
  const formRef = ref<FormInstance>()
  const departmentOptions = ref<{ label: string; value: string }[]>([])

  const form = ref<{
    username: string
    password?: string
    nickname: string
    email: string
    phone: string
    gender: number
    status: number
    department_id: string
  }>({
    username: '',
    password: '',
    nickname: '',
    email: '',
    phone: '',
    gender: 1,
    status: 1,
    department_id: ''
  })

  const dialogVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  const rules = computed<FormRules>(() => ({
    username: [
      { required: true, message: $t('user.usernameRequired'), trigger: 'blur' },
      { min: 2, max: 20, message: $t('user.usernameLength'), trigger: 'blur' }
    ],
    password:
      props.type === 'add'
        ? [
            { required: true, message: $t('user.passwordRequired'), trigger: 'blur' },
            { min: 6, max: 20, message: $t('user.passwordLength'), trigger: 'blur' }
          ]
        : [],
    nickname: [
      { required: true, message: $t('user.nicknameRequired'), trigger: 'blur' },
      { min: 2, max: 20, message: $t('user.nicknameLength'), trigger: 'blur' }
    ],
    email: [{ type: 'email', message: $t('user.emailFormat'), trigger: 'blur' }],
    phone: [{ pattern: /^1[3-9]\d{9}$/, message: $t('user.phoneFormat'), trigger: 'blur' }],
    department_id: [{ required: true, message: $t('user.departmentRequired'), trigger: 'change' }]
  }))

  watch(
    () => props.visible,
    (newVal) => {
      if (newVal) {
        resetForm()
        loadDepartmentOptions()
        if (props.type === 'edit' && props.userData) {
          form.value = {
            username: props.userData.username,
            nickname: props.userData.nickname || '',
            email: props.userData.email || '',
            phone: props.userData.phone || '',
            gender: props.userData.gender || 1,
            status: props.userData.status || 1,
            department_id: props.userData.department_id ? String(props.userData.department_id) : ''
          }
        } else if (props.type === 'add' && props.departmentId) {
          form.value.department_id = String(props.departmentId)
        }
      }
    }
  )

  const resetForm = () => {
    form.value = {
      username: '',
      password: '',
      nickname: '',
      email: '',
      phone: '',
      gender: 1,
      status: 1,
      department_id: ''
    }
    formRef.value?.resetFields()
  }

  const loadDepartmentOptions = async () => {
    try {
      const response = await fetchDepartmentTree()
      if (response.success && response.data) {
        departmentOptions.value = flattenDepartmentTree(response.data.result || [])
      }
    } catch (error) {
      console.error('加载部门选项失败:', error)
    }
  }

  const flattenDepartmentTree = (
    departments: DepartmentTree[],
    prefix = ''
  ): { label: string; value: string }[] => {
    const options: { label: string; value: string }[] = []
    departments.forEach((dept) => {
      const label = prefix ? `${prefix} / ${dept.name}` : dept.name
      options.push({ label, value: String(dept.id) })
      if (dept.children && dept.children.length > 0) {
        options.push(...flattenDepartmentTree(dept.children, label))
      }
    })
    return options
  }

  const handleClose = () => {
    dialogVisible.value = false
  }

  const handleSubmit = async () => {
    if (!formRef.value) return
    try {
      await formRef.value.validate()
      loading.value = true

      if (props.type === 'add') {
        const params: AddUserParams = {
          username: form.value.username,
          password: form.value.password || '',
          nickname: form.value.nickname,
          email: form.value.email || undefined,
          phone: form.value.phone || undefined,
          gender: form.value.gender,
          status: form.value.status,
          user_type: 3,
          department_id: String(form.value.department_id)
        }
        await addUser(params)
        ElMessage.success($t('user.addUserSuccess'))
      } else if (props.userData?.id) {
        const params: UpdateUserParams = {
          username: form.value.username,
          nickname: form.value.nickname || undefined,
          email: form.value.email || undefined,
          phone: form.value.phone || undefined,
          gender: form.value.gender,
          status: form.value.status,
          user_type: props.userData.user_type ?? 3,
          department_id: form.value.department_id || undefined
        }
        await updateUser(props.userData.id, params)
        ElMessage.success($t('common.editSuccess'))
      }

      emit('submit')
      handleClose()
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadDepartmentOptions()
  })
</script>
