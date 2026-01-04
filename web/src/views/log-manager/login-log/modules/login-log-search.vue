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
  import { computed, ref, onMounted } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { fetchDepartmentList } from '@/api/system/department'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'

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

  const { t } = useI18n()

  // 表单数据双向绑定
  const searchBarRef = ref()
  const formData = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
  })

  // 部门选项
  const departmentOptions = ref<Array<{ label: string; value: string }>>([])

  // 获取部门列表
  const getDepartmentOptions = async () => {
    try {
      const response = await fetchDepartmentList({})
      departmentOptions.value =
        response.data.result?.map((dept: any) => ({
          label: dept.name,
          value: dept.id
        })) || []
    } catch (error) {
      console.error('获取部门列表失败:', error)
    }
  }

  // 表单配置
  const formItems = computed(() => [
    {
      label: t('logManager.loginLog.username'),
      key: 'username',
      type: 'input',
      placeholder: t('common.pleaseInput') + t('logManager.loginLog.username'),
      clearable: true
    },
    {
      label: t('logManager.loginLog.nickname'),
      key: 'nickname',
      type: 'input',
      placeholder: t('common.pleaseInput') + t('logManager.loginLog.nickname'),
      clearable: true
    },
    {
      label: t('logManager.loginLog.department'),
      key: 'department_id',
      type: 'select',
      placeholder: t('common.pleaseSelect') + t('logManager.loginLog.department'),
      clearable: true,
      options: departmentOptions.value,
      filterable: true
    },
    {
      label: t('logManager.loginLog.status'),
      key: 'status',
      type: 'select',
      placeholder: t('common.pleaseSelect') + t('logManager.loginLog.status'),
      clearable: true,
      options: [
        { label: t('logManager.loginLog.success'), value: '1' },
        { label: t('logManager.loginLog.failed'), value: '0' }
      ]
    },
    {
      label: t('logManager.loginLog.loginTime'),
      key: 'timeRange',
      type: 'datetime',
      props: {
        type: 'datetimerange',
        startPlaceholder: t('common.startTime'),
        endPlaceholder: t('common.endTime'),
        format: 'YYYY-MM-DD HH:mm:ss',
        valueFormat: 'x'
      }
    }
  ])

  // 事件处理
  function handleReset() {
    emit('reset')
  }

  async function handleSearch() {
    await searchBarRef.value.validate()
    const params = { ...formData.value }

    // 处理时间范围
    if (params.timeRange && params.timeRange.length === 2) {
      params.startTime = params.timeRange[0]
      params.endTime = params.timeRange[1]
      delete params.timeRange
    }

    emit('search', params)
  }

  // 初始化
  onMounted(() => {
    getDepartmentOptions()
  })
</script>
