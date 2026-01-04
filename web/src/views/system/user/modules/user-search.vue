<template>
  <ArtSearchBar
    ref="searchBarRef"
    v-model="formData"
    :items="formItems"
    @reset="handleReset"
    @search="handleSearch"
  />
</template>

<script setup lang="ts">
  interface Props {
    modelValue: Record<string, any>
  }

  interface Emits {
    (e: 'update:modelValue', value: Record<string, any>): void
    (e: 'search', params: Record<string, any>): void
    (e: 'reset'): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()

  // 表单数据双向绑定
  const searchBarRef = ref()
  const formData = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
  })

  // 表单配置
  const formItems = computed(() => [
    {
      label: '用户名',
      key: 'username',
      type: 'input',
      placeholder: '请输入用户名',
      clearable: true
    },
    {
      label: '昵称',
      key: 'nickname',
      type: 'input',
      placeholder: '请输入昵称',
      clearable: true
    },
    {
      label: '邮箱',
      key: 'email',
      type: 'input',
      placeholder: '请输入邮箱',
      clearable: true
    },
    {
      label: '手机号',
      key: 'phone',
      type: 'input',
      placeholder: '请输入手机号',
      clearable: true
    },
    {
      label: '性别',
      key: 'gender',
      type: 'select',
      placeholder: '请选择性别',
      clearable: true,
      options: [
        { label: '男', value: 1 },
        { label: '女', value: 2 }
      ]
    },
    {
      label: '状态',
      key: 'status',
      type: 'select',
      placeholder: '请选择状态',
      clearable: true,
      options: [
        { label: '启用', value: 1 },
        { label: '禁用', value: 0 }
      ]
    }
  ])

  // 事件处理
  function handleReset() {
    emit('reset')
  }

  async function handleSearch() {
    await searchBarRef.value.validate()
    emit('search', formData.value)
  }
</script>
