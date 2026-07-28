<template>
  <ElDrawer
    v-model="visible"
    :title="dialogType === 'add' ? $t('user.addUser') : $t('user.editUser')"
    size="520px"
    @closed="resetForm"
  >
    <ArtForm
      ref="formRef"
      :model-value="formData"
      @update:model-value="Object.assign(formData, $event)"
      :items="formItems"
      :rules="formRules"
      :show-reset="false"
      :show-submit="false"
      label-width="110px"
    />

    <template #footer>
      <ElButton @click="visible = false">{{ $t('buttons.cancel') }}</ElButton>
      <ElButton type="primary" :loading="submitting" @click="handleSubmit">
        {{ $t('buttons.confirm') }}
      </ElButton>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
  import { computed, nextTick, reactive, ref, watch } from 'vue'
  import { ElMessage, type FormRules } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import ArtForm from '@/components/core/forms/art-form/index.vue'
  import {
    addUser,
    updateUser,
    type AddUserParams,
    type UpdateUserParams,
    type UserInfo
  } from '@/api/system/user'
  import { fetchDepartmentTree, type DepartmentInfo } from '@/api/system/department'

  defineOptions({ name: 'UserEditDrawer' })

  type DepartmentTreeNode = DepartmentInfo & {
    children?: DepartmentTreeNode[]
  }

  interface Props {
    modelValue: boolean
    dialogType: 'add' | 'edit'
    userData?: UserInfo
    departmentId?: string
  }

  interface Emits {
    (e: 'update:modelValue', value: boolean): void
    (e: 'success'): void
  }

  const props = withDefaults(defineProps<Props>(), {
    modelValue: false,
    dialogType: 'add',
    userData: undefined,
    departmentId: undefined
  })

  const emit = defineEmits<Emits>()
  const { t: $t } = useI18n()

  const visible = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value)
  })

  const formRef = ref()
  const submitting = ref(false)
  const departmentOptions = ref<DepartmentTreeNode[]>([])

  const createDefaultForm = () => ({
    username: '',
    password: '',
    nickname: '',
    email: '',
    phone: '',
    department_id: '' as string | number,
    user_type: 3,
    gender: 1,
    status: 1
  })

  const formData = reactive(createDefaultForm())

  const formRules: FormRules = {
    username: [
      { required: true, message: $t('user.usernameRequired'), trigger: 'blur' },
      { min: 2, max: 20, message: $t('user.usernameLength'), trigger: 'blur' }
    ],
    password: [
      { required: true, message: $t('user.passwordRequired'), trigger: 'blur' },
      { min: 6, max: 20, message: $t('user.passwordLength'), trigger: 'blur' }
    ],
    nickname: [{ required: true, message: $t('user.nicknameRequired'), trigger: 'blur' }],
    department_id: [{ required: true, message: $t('user.departmentRequired'), trigger: 'change' }]
  }

  const formItems = computed(() => {
    const items: any[] = [
      {
        key: 'username',
        label: $t('user.username'),
        type: 'input',
        span: 24,
        props: {
          placeholder: $t('user.username'),
          disabled: props.dialogType === 'edit'
        }
      }
    ]

    if (props.dialogType === 'add') {
      items.push({
        key: 'password',
        label: $t('user.password'),
        type: 'input',
        span: 24,
        props: {
          type: 'password',
          showPassword: true,
          placeholder: $t('user.password')
        }
      })
    }

    items.push(
      {
        key: 'nickname',
        label: $t('user.nickname'),
        type: 'input',
        span: 24,
        props: {
          placeholder: $t('user.nickname')
        }
      },
      {
        key: 'email',
        label: $t('user.email'),
        type: 'input',
        span: 24,
        props: {
          placeholder: $t('user.email')
        }
      },
      {
        key: 'phone',
        label: $t('user.phone'),
        type: 'input',
        span: 24,
        props: {
          placeholder: $t('user.phone')
        }
      }
    )

    if (props.dialogType === 'add') {
      items.push({
        key: 'department_id',
        label: $t('common.department'),
        type: 'treeselect',
        span: 24,
        props: {
          data: departmentOptions.value,
          props: { label: 'name', value: 'id', children: 'children' },
          clearable: true,
          checkStrictly: true,
          placeholder: $t('user.selectDepartment')
        }
      })
    }

    items.push(
      {
        key: 'gender',
        label: $t('user.gender'),
        type: 'radiogroup',
        span: 24,
        props: {
          options: [
            { label: $t('user.male'), value: 1 },
            { label: $t('user.female'), value: 0 }
          ]
        }
      },
      {
        key: 'status',
        label: $t('common.status'),
        type: 'radiogroup',
        span: 24,
        props: {
          options: [
            { label: $t('common.enabled'), value: 1 },
            { label: $t('common.disabled'), value: 0 }
          ]
        }
      }
    )

    return items
  })

  const resetForm = () => {
    Object.assign(formData, createDefaultForm())
    formRef.value?.ref?.clearValidate?.()
  }

  const loadDepartments = async () => {
    const res = await fetchDepartmentTree()
    departmentOptions.value = (res.data?.result || []) as DepartmentTreeNode[]
  }

  const fillForm = () => {
    resetForm()

    if (props.dialogType === 'edit' && props.userData) {
      Object.assign(formData, {
        username: props.userData.username,
        nickname: props.userData.nickname || '',
        email: props.userData.email || '',
        phone: props.userData.phone || '',
        gender: props.userData.gender ?? 1,
        status: props.userData.status ?? 1,
        department_id: props.userData.department_id ? String(props.userData.department_id) : ''
      })
      return
    }

    if (props.departmentId) {
      formData.department_id = String(props.departmentId)
    }
  }

  watch(
    () => visible.value,
    async (opened) => {
      if (!opened) {
        return
      }

      if (props.dialogType === 'add') {
        await loadDepartments()
      }

      await nextTick()
      fillForm()
    }
  )

  const handleSubmit = async () => {
    const valid = await formRef.value?.validate?.().catch(() => false)
    if (!valid) {
      return
    }

    submitting.value = true
    try {
      if (props.dialogType === 'add') {
        const payload: AddUserParams = {
          username: formData.username,
          password: formData.password,
          nickname: formData.nickname,
          email: formData.email || undefined,
          phone: formData.phone || undefined,
          gender: formData.gender,
          status: formData.status,
          user_type: 3,
          department_id: String(formData.department_id)
        }
        await addUser(payload)
        ElMessage.success($t('common.addSuccess'))
      } else if (props.userData?.id) {
        const payload: UpdateUserParams = {
          username: formData.username,
          nickname: formData.nickname || undefined,
          email: formData.email || undefined,
          phone: formData.phone || undefined,
          gender: formData.gender,
          status: formData.status,
          user_type: props.userData.user_type ?? 3,
          department_id: props.userData.department_id
        }
        await updateUser(props.userData.id, payload)
        ElMessage.success($t('common.editSuccess'))
      }

      emit('success')
      visible.value = false
    } finally {
      submitting.value = false
    }
  }
</script>
