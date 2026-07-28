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
  import { computed, onMounted, ref } from 'vue'
  import { useDictionary } from '@/composables/useDictionary'

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

  const searchBarRef = ref()
  const formData = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
  })

  const genderDict = useDictionary('user_gender')
  const statusDict = useDictionary('common_status')

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
      options: genderDict.options.value
    },
    {
      label: '状态',
      key: 'status',
      type: 'select',
      placeholder: '请选择状态',
      clearable: true,
      options: statusDict.options.value
    }
  ])

  function handleReset() {
    emit('reset')
  }

  function handleSearch() {
    emit('search', formData.value)
  }

  onMounted(async () => {
    await Promise.all([genderDict.load(), statusDict.load()])
  })
</script>
