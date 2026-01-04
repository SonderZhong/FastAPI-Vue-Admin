<template>
  <ElDialog
    v-model="dialogVisible"
    :title="type === 'add' ? $t('user.addUser', '新增用户') : $t('user.editUser', '编辑用户')"
    width="600px"
    :before-close="handleClose"
  >
    <ElForm ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="right">
      <ElRow :gutter="20">
        <ElCol :span="12">
          <ElFormItem :label="$t('user.username', '用户名')" prop="username">
            <ElInput
              v-model="form.username"
              :placeholder="$t('user.username', '用户名')"
              :disabled="type === 'edit'"
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.nickname', '昵称')" prop="nickname">
            <ElInput v-model="form.nickname" :placeholder="$t('user.nickname', '昵称')" />
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" v-if="type === 'add'">
        <ElCol :span="12">
          <ElFormItem :label="$t('user.password', '密码')" prop="password">
            <ElInput
              v-model="form.password"
              type="password"
              :placeholder="$t('user.password', '密码')"
              show-password
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.gender', '性别')" prop="gender">
            <ElRadioGroup v-model="form.gender">
              <ElRadio :value="1">{{ $t('user.male', '男') }}</ElRadio>
              <ElRadio :value="0">{{ $t('user.female', '女') }}</ElRadio>
            </ElRadioGroup>
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" v-else>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.gender', '性别')" prop="gender">
            <ElRadioGroup v-model="form.gender">
              <ElRadio :value="1">{{ $t('user.male', '男') }}</ElRadio>
              <ElRadio :value="0">{{ $t('user.female', '女') }}</ElRadio>
            </ElRadioGroup>
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('common.status', '状态')" prop="status">
            <ElSwitch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
              :active-text="$t('common.enabled', '启用')"
              :inactive-text="$t('common.disabled', '禁用')"
            />
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20">
        <ElCol :span="12">
          <ElFormItem :label="$t('user.email', '邮箱')" prop="email">
            <ElInput v-model="form.email" :placeholder="$t('user.email', '邮箱')" />
          </ElFormItem>
        </ElCol>
        <ElCol :span="12">
          <ElFormItem :label="$t('user.phone', '手机')" prop="phone">
            <ElInput v-model="form.phone" :placeholder="$t('user.phone', '手机')" />
          </ElFormItem>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20">
        <ElCol :span="12">
          <ElFormItem :label="$t('common.department', '部门')" prop="department_id">
            <ElSelect
              v-model="form.department_id"
              :placeholder="$t('common.department', '部门')"
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
        <ElCol :span="12">
          <ElFormItem :label="$t('user.userType', '用户身份')" prop="user_type">
            <ElSelect
              v-model="form.user_type"
              :placeholder="$t('user.selectUserType', '请选择用户身份')"
              style="width: 100%"
            >
              <ElOption
                v-for="option in userTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </ElSelect>
          </ElFormItem>
        </ElCol>
      </ElRow>
    </ElForm>

    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">{{ $t('common.cancel', '取消') }}</ElButton>
        <ElButton type="primary" @click="handleSubmit" :loading="loading">
          {{ $t('common.confirm', '确定') }}
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
  import { getAssignableUserTypes } from '@/utils/permission'
  import { useUserStore } from '@/store/modules/user'

  const { t: $t } = useI18n()
  const userStore = useUserStore()

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

  // 响应式数据
  const loading = ref(false)
  const formRef = ref<FormInstance>()
  const departmentOptions = ref<{ label: string; value: string }[]>([])

  // 根据当前用户身份获取可分配的用户身份选项
  const userTypeOptions = computed(() => {
    const currentUserType = userStore.info?.user_type ?? 3
    return getAssignableUserTypes(currentUserType)
  })

  // 表单数据
  const form = ref<{
    username: string
    password?: string
    nickname: string
    email: string
    phone: string
    gender: number
    status: number
    user_type: number
    department_id: string
  }>({
    username: '',
    password: '',
    nickname: '',
    email: '',
    phone: '',
    gender: 1,
    status: 1,
    user_type: 3,
    department_id: ''
  })

  // 弹窗显示状态
  const dialogVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  // 表单验证规则
  const rules = computed<FormRules>(() => ({
    username: [
      { required: true, message: $t('user.usernameRequired', '请输入用户名'), trigger: 'blur' },
      {
        min: 2,
        max: 20,
        message: $t('user.usernameLength', '用户名长度在 2 到 20 个字符'),
        trigger: 'blur'
      }
    ],
    password:
      props.type === 'add'
        ? [
            { required: true, message: $t('user.passwordRequired', '请输入密码'), trigger: 'blur' },
            {
              min: 6,
              max: 20,
              message: $t('user.passwordLength', '密码长度在 6 到 20 个字符'),
              trigger: 'blur'
            }
          ]
        : [],
    nickname: [
      { required: true, message: $t('user.nicknameRequired', '请输入昵称'), trigger: 'blur' },
      {
        min: 2,
        max: 20,
        message: $t('user.nicknameLength', '昵称长度在 2 到 20 个字符'),
        trigger: 'blur'
      }
    ],
    email: [
      { type: 'email', message: $t('user.emailFormat', '请输入正确的邮箱格式'), trigger: 'blur' }
    ],
    phone: [
      {
        pattern: /^1[3-9]\d{9}$/,
        message: $t('user.phoneFormat', '请输入正确的手机号格式'),
        trigger: 'blur'
      }
    ],
    department_id: [
      { required: true, message: $t('user.departmentRequired', '请选择部门'), trigger: 'change' }
    ],
    user_type: [
      { required: true, message: $t('user.userTypeRequired', '请选择用户身份'), trigger: 'change' }
    ]
  }))

  /**
   * 监听弹窗显示状态
   */
  watch(
    () => props.visible,
    (newVal) => {
      if (newVal) {
        resetForm()
        loadDepartmentOptions()
        if (props.type === 'edit' && props.userData) {
          // 编辑模式，填充表单数据
          form.value = {
            username: props.userData.username,
            nickname: props.userData.nickname || '',
            email: props.userData.email || '',
            phone: props.userData.phone || '',
            gender: props.userData.gender || 1,
            status: props.userData.status || 1,
            user_type: props.userData.user_type ?? 3,
            department_id: props.userData.department_id || ''
          }
        } else if (props.type === 'add' && props.departmentId) {
          // 新增模式，设置默认部门
          form.value.department_id = props.departmentId
        }
      }
    }
  )

  /**
   * 重置表单
   */
  const resetForm = () => {
    form.value = {
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
    formRef.value?.resetFields()
  }

  /**
   * 加载部门选项
   */
  const loadDepartmentOptions = async () => {
    try {
      const response = await fetchDepartmentTree()
      // 由于部门API尚未更新，暂时使用旧的响应格式
      if (response.success && response.data) {
        departmentOptions.value = flattenDepartmentTree(response.data.result || [])
      }
    } catch (error) {
      console.error('加载部门选项失败:', error)
    }
  }

  /**
   * 扁平化部门树为选项列表
   */
  const flattenDepartmentTree = (
    departments: DepartmentTree[],
    prefix = ''
  ): { label: string; value: string }[] => {
    const options: { label: string; value: string }[] = []

    departments.forEach((dept) => {
      const label = prefix ? `${prefix} / ${dept.name}` : dept.name
      options.push({
        label,
        value: dept.id
      })

      if (dept.children && dept.children.length > 0) {
        options.push(...flattenDepartmentTree(dept.children, label))
      }
    })

    return options
  }

  /**
   * 关闭弹窗
   */
  const handleClose = () => {
    dialogVisible.value = false
  }

  /**
   * 提交表单
   */
  const handleSubmit = async () => {
    if (!formRef.value) return

    try {
      await formRef.value.validate()
      loading.value = true

      if (props.type === 'add') {
        // 新增用户
        const params: AddUserParams = {
          username: form.value.username,
          password: form.value.password!,
          nickname: form.value.nickname,
          email: form.value.email,
          phone: form.value.phone,
          gender: form.value.gender,
          status: form.value.status,
          user_type: form.value.user_type,
          department_id: form.value.department_id
        }

        await addUser(params)
        ElMessage.success($t('user.addUserSuccess', '新增用户成功'))
        emit('submit')
        handleClose()
      } else {
        // 编辑用户
        const params: UpdateUserParams = {
          username: form.value.username,
          nickname: form.value.nickname || undefined,
          email: form.value.email || undefined,
          phone: form.value.phone || undefined,
          gender: form.value.gender,
          status: form.value.status,
          user_type: form.value.user_type,
          department_id: form.value.department_id || undefined
        }

        await updateUser(props.userData!.id, params)
        ElMessage.success($t('user.updateUserSuccess', '更新用户成功'))
        emit('submit')
        handleClose()
      }
    } catch (error) {
      console.error('表单验证失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 页面初始化
  onMounted(() => {
    loadDepartmentOptions()
  })
</script>

<style scoped>
  .dialog-footer {
    text-align: right;
  }
</style>
