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
      label: '鐢ㄦ埛鍚?',
      key: 'username',
      type: 'input',
      placeholder: '璇疯緭鍏ョ敤鎴峰悕',
      clearable: true
    },
    {
      label: '鏄电О',
      key: 'nickname',
      type: 'input',
      placeholder: '璇疯緭鍏ユ樀绉?',
      clearable: true
    },
    {
      label: '閭',
      key: 'email',
      type: 'input',
      placeholder: '璇疯緭鍏ラ偖绠?',
      clearable: true
    },
    {
      label: '鎵嬫満鍙?',
      key: 'phone',
      type: 'input',
      placeholder: '璇疯緭鍏ユ墜鏈哄彿',
      clearable: true
    },
    {
      label: '鎬у埆',
      key: 'gender',
      type: 'select',
      placeholder: '璇烽€夋嫨鎬у埆',
      clearable: true,
      options: genderDict.options.value
    },
    {
      label: '鐘舵€?',
      key: 'status',
      type: 'select',
      placeholder: '璇烽€夋嫨鐘舵€?,
      clearable: true,
      options: statusDict.options.value
    }
  ])

  async function handleReset() {
    emit('reset')
  }

  async function handleSearch() {
    await searchBarRef.value.validate()
    emit('search', formData.value)
  }

  onMounted(async () => {
    await Promise.all([genderDict.load(), statusDict.load()])
  })
</script>
