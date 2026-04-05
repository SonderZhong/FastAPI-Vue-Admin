<template>
  <div class="art-full-height">
    <ElRow :gutter="16" class="h-full">
      <!-- 左侧：字典列表 -->
      <ElCol :xs="24" :sm="24" :md="10" :lg="8" :xl="6" class="h-full">
        <ElCard class="art-table-card h-full" shadow="never">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="text-base font-medium">{{ $t('dictionary.dictionaryList') }}</span>
              <div class="flex items-center gap-2">
                <ElButton
                  v-auth="'dictionary:btn:add'"
                  type="primary"
                  size="small"
                  :icon="Plus"
                  @click="handleAdd"
                >
                  {{ $t('buttons.add') }}
                </ElButton>
                <ElButton
                  :icon="Refresh"
                  size="small"
                  circle
                  @click="refreshDictionaryList"
                />
              </div>
            </div>
          </template>

          <!-- 搜索框 -->
          <div class="mb-3">
            <ElInput
              v-model="searchKeyword"
              :placeholder="$t('dictionary.searchPlaceholder')"
              clearable
              :prefix-icon="Search"
              @input="handleSearchDictionary"
            />
          </div>

          <!-- 字典列表 -->
          <div class="dictionary-list">
            <div
              v-for="dict in filteredDictionaryList"
              :key="dict.id"
              class="dictionary-item"
              :class="{ active: selectedDictionary?.id === dict.id }"
              @click="handleSelectDictionary(dict)"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-medium text-sm truncate">{{ dict.dict_name }}</span>
                    <ElTag
                      :type="dict.status === 1 ? 'success' : 'info'"
                      size="small"
                    >
                      {{ dict.status === 1 ? '启用' : '禁用' }}
                    </ElTag>
                  </div>
                  <div class="text-xs text-gray-500 truncate">{{ dict.dict_code }}</div>
                  <div v-if="dict.dict_type" class="text-xs text-gray-400 truncate mt-1">
                    类型: {{ dict.dict_type }}
                  </div>
                </div>
                <div class="flex items-center gap-1 ml-2">
                  <ElButton
                    v-auth="'dictionary:btn:update'"
                    type="primary"
                    link
                    size="small"
                    :icon="Edit"
                    @click.stop="handleEdit(dict)"
                  />
                  <ElButton
                    v-auth="'dictionary:btn:delete'"
                    type="danger"
                    link
                    size="small"
                    :icon="Delete"
                    @click.stop="handleDelete(dict)"
                  />
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <ElEmpty
              v-if="!filteredDictionaryList.length && !dictionaryLoading"
              :description="$t('dictionary.noDictionary')"
              :image-size="80"
            />
          </div>

          <!-- 加载状态 -->
          <div v-if="dictionaryLoading" class="flex justify-center py-8">
            <ElIcon class="is-loading" :size="24">
              <Loading />
            </ElIcon>
          </div>
        </ElCard>
      </ElCol>

      <!-- 右侧：字典项列表 -->
      <ElCol :xs="24" :sm="24" :md="14" :lg="16" :xl="18" class="h-full">
        <ElCard class="art-table-card h-full" shadow="never">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="text-base font-medium">{{ $t('dictionary.dictionaryItemList') }}</span>
                <ElTag v-if="selectedDictionary" type="primary">
                  {{ selectedDictionary.dict_name }}
                </ElTag>
              </div>
              <div v-if="selectedDictionary" class="flex items-center gap-2">
                <ElButton
                  v-auth="'dictionaryitem:btn:add'"
                  type="primary"
                  size="small"
                  :icon="Plus"
                  @click="handleAddItem"
                >
                  {{ $t('dictionary.addDictionaryItem') }}
                </ElButton>
                <ElButton
                  v-auth="'dictionaryitem:btn:delete'"
                  type="danger"
                  size="small"
                  :icon="Delete"
                  :disabled="!selectedItemIds.length"
                  @click="handleBatchDeleteItems"
                >
                  {{ $t('buttons.batchDelete') }}
                </ElButton>
                <ElButton
                  :icon="Refresh"
                  size="small"
                  circle
                  @click="refreshItemList"
                />
              </div>
            </div>
          </template>

          <!-- 未选择字典提示 -->
          <div v-if="!selectedDictionary" class="flex items-center justify-center h-full">
            <ElEmpty :description="$t('dictionary.selectDictionaryTip')" :image-size="120" />
          </div>

          <!-- 字典项表格 -->
          <div v-else class="flex flex-col h-full">
            <ArtTable
              :data="itemTableData"
              :columns="itemColumns"
              :pagination="itemPagination"
              :loading="itemLoading"
              fit
              @selection-change="handleItemSelectionChange"
              @pagination:current-change="handleItemPageChange"
              @pagination:size-change="handleItemSizeChange"
            >
              <!-- 状态列 -->
              <template #status="{ row }">
                <ElTag :type="row.status === 1 ? 'success' : 'info'">
                  {{ row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
                </ElTag>
              </template>

              <!-- 标签颜色列 -->
              <template #tag_color="{ row }">
                <ElTag v-if="row.tag_color" :color="row.tag_color" class="text-white">
                  {{ row.label }}
                </ElTag>
                <span v-else>-</span>
              </template>

              <!-- 操作列 -->
              <template #action="{ row }">
                <ElButton
                  v-auth="'dictionaryitem:btn:update'"
                  type="primary"
                  link
                  size="small"
                  @click="handleEditItem(row)"
                >
                  {{ $t('buttons.edit') }}
                </ElButton>
                <ElButton
                  v-auth="'dictionaryitem:btn:delete'"
                  type="danger"
                  link
                  size="small"
                  @click="handleDeleteItem(row)"
                >
                  {{ $t('buttons.delete') }}
                </ElButton>
              </template>
            </ArtTable>
          </div>
        </ElCard>
      </ElCol>
    </ElRow>

    <!-- 新增/编辑字典对话框 -->
    <ElDialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? $t('dictionary.addDictionary') : $t('dictionary.editDictionary')"
      width="600px"
      @close="handleDialogClose"
    >
      <ElForm
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <ElFormItem :label="$t('dictionary.dictName')" prop="dict_name">
          <ElInput v-model="formData.dict_name" :placeholder="$t('dictionary.dictNamePlaceholder')" />
        </ElFormItem>
        <ElFormItem :label="$t('dictionary.dictCode')" prop="dict_code">
          <ElInput
            v-model="formData.dict_code"
            :placeholder="$t('dictionary.dictCodePlaceholder')"
            :disabled="dialogType === 'edit'"
          />
        </ElFormItem>
        <ElFormItem :label="$t('dictionary.dictType')" prop="dict_type">
          <ElInput v-model="formData.dict_type" :placeholder="$t('dictionary.dictTypePlaceholder')" />
        </ElFormItem>
        <ElFormItem :label="$t('common.status')" prop="status">
          <ElRadioGroup v-model="formData.status">
            <ElRadio :label="1">{{ $t('common.enabled') }}</ElRadio>
            <ElRadio :label="0">{{ $t('common.disabled') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem :label="$t('common.sort')" prop="sort">
          <ElInputNumber v-model="formData.sort" :min="0" :max="9999" />
        </ElFormItem>
        <ElFormItem :label="$t('common.remark')" prop="remark">
          <ElInput
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            :placeholder="$t('common.pleaseInput')"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="dialogVisible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </ElButton>
      </template>
    </ElDialog>

    <!-- 新增/编辑字典项对话框 -->
    <ElDialog
      v-model="itemDialogVisible"
      :title="itemDialogType === 'add' ? $t('dictionary.addDictionaryItem') : $t('dictionary.editDictionaryItem')"
      width="600px"
      @close="handleItemDialogClose"
    >
      <ElForm
        ref="itemFormRef"
        :model="itemFormData"
        :rules="itemFormRules"
        label-width="100px"
      >
        <ElFormItem :label="$t('dictionary.itemLabel')" prop="label">
          <ElInput v-model="itemFormData.label" :placeholder="$t('dictionary.itemLabelPlaceholder')" />
        </ElFormItem>
        <ElFormItem :label="$t('dictionary.itemValue')" prop="value">
          <ElInput v-model="itemFormData.value" :placeholder="$t('dictionary.itemValuePlaceholder')" />
        </ElFormItem>
        <ElFormItem :label="$t('common.status')" prop="status">
          <ElRadioGroup v-model="itemFormData.status">
            <ElRadio :label="1">{{ $t('common.enabled') }}</ElRadio>
            <ElRadio :label="0">{{ $t('common.disabled') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem :label="$t('common.sort')" prop="sort">
          <ElInputNumber v-model="itemFormData.sort" :min="0" :max="9999" />
        </ElFormItem>
        <ElFormItem :label="$t('dictionary.tagColor')" prop="tag_color">
          <ElColorPicker v-model="itemFormData.tag_color" show-alpha />
        </ElFormItem>
        <ElFormItem :label="$t('common.remark')" prop="remark">
          <ElInput
            v-model="itemFormData.remark"
            type="textarea"
            :rows="3"
            :placeholder="$t('common.pleaseInput')"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="itemDialogVisible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" :loading="itemSubmitLoading" @click="handleItemSubmit">
          {{ $t('common.confirm') }}
        </ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete, Refresh, Edit, Search, Loading } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import ArtTable from '@/components/core/tables/art-table/index.vue'
import type { ColumnOption } from '@/types'
import {
  fetchDictionaryList,
  addDictionary,
  updateDictionary,
  deleteDictionary,
  fetchDictionaryItemList,
  addDictionaryItem,
  updateDictionaryItem,
  deleteDictionaryItem,
  deleteDictionaryItemList,
  type DictionaryInfo,
  type DictionaryItemInfo
} from '@/api/system/dictionary'

defineOptions({ name: 'Dictionary' })

const { t } = useI18n()

// ==================== 字典相关 ====================
const dictionaryLoading = ref(false)
const dictionaryList = ref<DictionaryInfo[]>([])
const selectedDictionary = ref<DictionaryInfo | null>(null)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive({
  dict_name: '',
  dict_code: '',
  dict_type: '',
  status: 1,
  sort: 0,
  remark: ''
})

// 表单验证规则
const formRules: FormRules = {
  dict_name: [{ required: true, message: t('dictionary.dictNameRequired'), trigger: 'blur' }],
  dict_code: [{ required: true, message: t('dictionary.dictCodeRequired'), trigger: 'blur' }],
  dict_type: [{ required: true, message: t('dictionary.dictTypeRequired'), trigger: 'blur' }]
}

// 过滤后的字典列表
const filteredDictionaryList = computed(() => {
  if (!searchKeyword.value) return dictionaryList.value
  const keyword = searchKeyword.value.toLowerCase()
  return dictionaryList.value.filter(
    dict =>
      dict.dict_name.toLowerCase().includes(keyword) ||
      dict.dict_code.toLowerCase().includes(keyword)
  )
})

// 获取字典列表
const fetchDictionaryData = async () => {
  dictionaryLoading.value = true
  try {
    const res = await fetchDictionaryList({ page: 1, pageSize: 1000 })
    dictionaryList.value = res.data.result
    // 如果有选中的字典，更新其数据
    if (selectedDictionary.value) {
      const updated = dictionaryList.value.find(d => d.id === selectedDictionary.value!.id)
      if (updated) {
        selectedDictionary.value = updated
      }
    }
  } catch (error) {
    console.error('获取字典列表失败:', error)
  } finally {
    dictionaryLoading.value = false
  }
}

// 搜索字典
const handleSearchDictionary = () => {
  // 搜索时自动触发计算属性更新
}

// 选择字典
const handleSelectDictionary = (dict: DictionaryInfo) => {
  selectedDictionary.value = dict
  fetchItemData()
}

// 刷新字典列表
const refreshDictionaryList = () => {
  fetchDictionaryData()
}

// 新增字典
const handleAdd = () => {
  dialogType.value = 'add'
  dialogVisible.value = true
}

// 编辑字典
const handleEdit = (dict: DictionaryInfo) => {
  dialogType.value = 'edit'
  selectedDictionary.value = dict
  Object.assign(formData, {
    dict_name: dict.dict_name,
    dict_code: dict.dict_code,
    dict_type: dict.dict_type,
    status: dict.status,
    sort: dict.sort,
    remark: dict.remark || ''
  })
  dialogVisible.value = true
}

// 删除字典
const handleDelete = async (dict: DictionaryInfo) => {
  try {
    await ElMessageBox.confirm(t('dictionary.deleteDictionaryConfirm'), t('common.tips'), {
      type: 'warning'
    })
    await deleteDictionary(dict.id)
    ElMessage.success(t('common.deleteSuccess'))
    if (selectedDictionary.value?.id === dict.id) {
      selectedDictionary.value = null
    }
    fetchDictionaryData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 提交字典表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async valid => {
    if (!valid) return

    submitLoading.value = true
    try {
      if (dialogType.value === 'add') {
        await addDictionary(formData)
        ElMessage.success(t('common.addSuccess'))
      } else {
        await updateDictionary(selectedDictionary.value!.id, formData)
        ElMessage.success(t('common.updateSuccess'))
      }
      dialogVisible.value = false
      fetchDictionaryData()
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      submitLoading.value = false
    }
  })
}

// 对话框关闭
const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    dict_name: '',
    dict_code: '',
    dict_type: '',
    status: 1,
    sort: 0,
    remark: ''
  })
}

// ==================== 字典项相关 ====================
const itemLoading = ref(false)
const itemTableData = ref<DictionaryItemInfo[]>([])
const selectedItemIds = ref<string[]>([])
const itemDialogVisible = ref(false)
const itemDialogType = ref<'add' | 'edit'>('add')
const itemSubmitLoading = ref(false)
const itemFormRef = ref<FormInstance>()
const currentItem = ref<DictionaryItemInfo | null>(null)

// 字典项分页
const itemPagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

// 字典项表格列配置
const itemColumns = ref<ColumnOption[]>([
  { type: 'selection' as const, width: 55 },
  { prop: 'label', label: t('dictionary.itemLabel'), minWidth: 150 },
  { prop: 'value', label: t('dictionary.itemValue'), minWidth: 150 },
  { prop: 'status', label: t('common.status'), width: 100, useSlot: true },
  { prop: 'sort', label: t('common.sort'), width: 100 },
  { prop: 'tag_color', label: t('dictionary.tagColor'), width: 120, useSlot: true },
  { prop: 'remark', label: t('common.remark'), minWidth: 200 },
  { prop: 'action', label: t('common.actions'), width: 150, fixed: 'right' as const, useSlot: true }
])

// 字典项表单数据
const itemFormData = reactive({
  label: '',
  value: '',
  status: 1,
  sort: 0,
  tag_color: '',
  remark: ''
})

// 字典项表单验证规则
const itemFormRules: FormRules = {
  label: [{ required: true, message: t('dictionary.itemLabelRequired'), trigger: 'blur' }],
  value: [{ required: true, message: t('dictionary.itemValueRequired'), trigger: 'blur' }]
}

// 获取字典项列表
const fetchItemData = async () => {
  if (!selectedDictionary.value) return

  itemLoading.value = true
  try {
    const res = await fetchDictionaryItemList({
      page: itemPagination.current,
      pageSize: itemPagination.size,
      dictionary_id: selectedDictionary.value.id
    })
    itemTableData.value = res.data.result
    itemPagination.total = res.data.total
  } catch (error) {
    console.error('获取字典项列表失败:', error)
  } finally {
    itemLoading.value = false
  }
}

// 刷新字典项列表
const refreshItemList = () => {
  fetchItemData()
}

// 新增字典项
const handleAddItem = () => {
  itemDialogType.value = 'add'
  itemDialogVisible.value = true
}

// 编辑字典项
const handleEditItem = (item: DictionaryItemInfo) => {
  itemDialogType.value = 'edit'
  currentItem.value = item
  Object.assign(itemFormData, {
    label: item.label,
    value: item.value,
    status: item.status,
    sort: item.sort,
    tag_color: item.tag_color || '',
    remark: item.remark || ''
  })
  itemDialogVisible.value = true
}

// 删除字典项
const handleDeleteItem = async (item: DictionaryItemInfo) => {
  try {
    await ElMessageBox.confirm(t('dictionary.deleteDictionaryItemConfirm'), t('common.tips'), {
      type: 'warning'
    })
    await deleteDictionaryItem(item.id)
    ElMessage.success(t('common.deleteSuccess'))
    fetchItemData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 批量删除字典项
const handleBatchDeleteItems = async () => {
  try {
    await ElMessageBox.confirm(
      t('dictionary.batchDeleteItemsConfirm', { count: selectedItemIds.value.length }),
      t('common.tips'),
      { type: 'warning' }
    )
    await deleteDictionaryItemList(selectedItemIds.value)
    ElMessage.success(t('common.deleteSuccess'))
    selectedItemIds.value = []
    fetchItemData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
    }
  }
}

// 字典项表格选择变化
const handleItemSelectionChange = (selection: DictionaryItemInfo[]) => {
  selectedItemIds.value = selection.map(item => item.id)
}

// 字典项分页变化
const handleItemPageChange = (page: number) => {
  itemPagination.current = page
  fetchItemData()
}

const handleItemSizeChange = (size: number) => {
  itemPagination.size = size
  itemPagination.current = 1
  fetchItemData()
}

// 提交字典项表单
const handleItemSubmit = async () => {
  if (!itemFormRef.value || !selectedDictionary.value) return

  await itemFormRef.value.validate(async valid => {
    if (!valid) return

    itemSubmitLoading.value = true
    try {
      const data = {
        ...itemFormData,
        dictionary_id: selectedDictionary.value!.id
      }

      if (itemDialogType.value === 'add') {
        await addDictionaryItem(data)
        ElMessage.success(t('common.addSuccess'))
      } else {
        await updateDictionaryItem(currentItem.value!.id, data)
        ElMessage.success(t('common.updateSuccess'))
      }
      itemDialogVisible.value = false
      fetchItemData()
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      itemSubmitLoading.value = false
    }
  })
}

// 字典项对话框关闭
const handleItemDialogClose = () => {
  itemFormRef.value?.resetFields()
  Object.assign(itemFormData, {
    label: '',
    value: '',
    status: 1,
    sort: 0,
    tag_color: '',
    remark: ''
  })
  currentItem.value = null
}

// 初始化
onMounted(() => {
  fetchDictionaryData()
})
</script>

<style scoped lang="scss">
.dictionary-list {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  
  .dictionary-item {
    padding: 12px;
    margin-bottom: 8px;
    border: 1px solid var(--art-border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background-color: var(--art-hover-bg-color);
      border-color: var(--el-color-primary);
    }
    
    &.active {
      background-color: var(--el-color-primary-light-9);
      border-color: var(--el-color-primary);
    }
  }
}
</style>
