<template>
  <ArtSearchBar
    ref="searchBarRef"
    v-model="formData"
    :items="formItems"
    :rules="rules"
    @reset="handleReset"
    @search="handleSearch"
  >
  </ArtSearchBar>
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

  // 校验规则
  const rules = {
    // name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
  }

  // 表单配置
  const formItems = computed(() => [
    {
      label: '部门名称',
      key: 'name',
      type: 'input',
      placeholder: '请输入部门名称',
      clearable: true
    },
    {
      label: '负责人',
      key: 'principal',
      type: 'input',
      placeholder: '请输入负责人',
      clearable: true
    },
    {
      label: '电话',
      key: 'phone',
      type: 'input',
      placeholder: '请输入电话',
      clearable: true
    },
    {
      label: '邮箱',
      key: 'email',
      type: 'input',
      placeholder: '请输入邮箱',
      clearable: true
    }
  ])

  // 事件
  function handleReset() {
    console.log('重置表单')
    emit('reset')
  }

  async function handleSearch() {
    await searchBarRef.value.validate()
    emit('search', formData.value)
    console.log('表单数据', formData.value)
  }
</script>
