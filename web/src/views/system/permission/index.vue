<template>
  <div class="art-full-height">
    <ElCard class="art-table-card h-full" shadow="never">
      <div class="mb-4 flex flex-wrap items-center gap-4">
        <ElInput
          v-model="searchForm.keyword"
          :placeholder="$t('user.searchPermissions')"
          clearable
          class="!w-[280px]"
          @keyup.enter="handleSearch"
        />
        <ElSelect
          v-model="searchForm.menu_type"
          :placeholder="$t('permission.permissionType')"
          clearable
          class="!w-[140px]"
        >
          <ElOption :label="$t('common.menu')" :value="0" />
          <ElOption :label="$t('common.button')" :value="1" />
        </ElSelect>
        <ElButton type="primary" :icon="Search" @click="handleSearch">
          {{ $t('table.searchBar.search') }}
        </ElButton>
        <ElButton :icon="Refresh" @click="handleReset">
          {{ $t('table.searchBar.reset') }}
        </ElButton>
      </div>

      <div class="mb-4 flex items-center justify-between">
        <ElSpace wrap>
          <ElButton v-auth="'permission:btn:add'" type="primary" :icon="Plus" @click="openCreate()">
            {{ $t('buttons.addPermission') }}
          </ElButton>
          <ElButton @click="toggleExpand">
            {{ expanded ? $t('buttons.collapseAll') : $t('buttons.expandAll') }}
          </ElButton>
        </ElSpace>
        <ElButton :icon="Refresh" circle @click="fetchData" />
      </div>

      <ArtTable
        ref="tableRef"
        row-key="id"
        :data="tableData"
        :columns="columns"
        :loading="loading"
        :pagination="undefined"
        :tree-props="{ children: 'children' }"
        default-expand-all
      >
        <template #title="{ row }">
          <div
            class="permission-title-cell flex min-w-0 flex-nowrap items-center gap-2 whitespace-nowrap"
          >
            <ElIcon :class="row.menu_type === 0 ? 'text-sky-500' : 'text-amber-500'">
              <FolderOpened v-if="row.menu_type === 0" />
              <Operation v-else />
            </ElIcon>
            <span class="truncate">{{ getDisplayName(row) }}</span>
          </div>
        </template>

        <template #menu_type="{ row }">
          <ElTag :type="row.menu_type === 0 ? 'primary' : 'warning'" size="small">
            {{ row.menu_type === 0 ? $t('common.menu') : $t('common.button') }}
          </ElTag>
        </template>

        <template #identifier="{ row }">
          <span v-if="row.menu_type === 0" class="truncate">
            {{ row.name || row.path || '-' }}
          </span>
          <code
            v-else
            class="rounded bg-[var(--el-fill-color-light)] px-2 py-1 text-xs text-[var(--el-text-color-secondary)]"
          >
            {{ row.code || row.name || '-' }}
          </code>
        </template>

        <template #action="{ row }">
          <ElButton
            v-if="row.menu_type === 0"
            v-auth="'permission:btn:add'"
            type="primary"
            link
            size="small"
            @click="openCreate(row.id)"
          >
            {{ $t('buttons.addSubMenu') }}
          </ElButton>
          <ElButton
            v-auth="'permission:btn:update'"
            type="primary"
            link
            size="small"
            @click="openEdit(row)"
          >
            {{ $t('buttons.edit') }}
          </ElButton>
          <ElButton
            v-auth="'permission:btn:delete'"
            type="danger"
            link
            size="small"
            @click="handleDelete(row)"
          >
            {{ $t('buttons.delete') }}
          </ElButton>
        </template>
      </ArtTable>
    </ElCard>

    <ElDrawer v-model="drawerVisible" :title="drawerTitle" size="620px" @closed="resetForm">
      <ElForm ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <ElFormItem :label="$t('permission.permissionType')" prop="menu_type">
          <ElRadioGroup v-model="formData.menu_type" :disabled="drawerMode === 'edit'">
            <ElRadio :value="0">{{ $t('common.menu') }}</ElRadio>
            <ElRadio :value="1">{{ $t('common.button') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>

        <ElFormItem :label="$t('permission.parentPermission')" prop="parent_id">
          <ElTreeSelect
            v-model="formData.parent_id"
            :data="parentOptions"
            :props="{ label: 'title', value: 'id', children: 'children' }"
            check-strictly
            clearable
            class="w-full"
            :placeholder="$t('common.pleaseSelect')"
          />
        </ElFormItem>

        <template v-if="formData.menu_type === 0">
          <ElFormItem :label="$t('permission.menuTitle')" prop="title">
            <ElInput v-model="formData.title" :placeholder="$t('common.pleaseInput')" />
          </ElFormItem>
          <ElFormItem :label="$t('permission.routeName')" prop="name">
            <ElInput v-model="formData.name" :placeholder="$t('common.pleaseInput')" />
          </ElFormItem>
          <ElFormItem :label="$t('permission.routePath')" prop="path">
            <ElInput v-model="formData.path" :placeholder="$t('common.pleaseInput')" />
          </ElFormItem>
          <ElFormItem :label="$t('permission.componentPath')" prop="component">
            <ElInput v-model="formData.component" :placeholder="$t('common.pleaseInput')" />
          </ElFormItem>
          <ElFormItem :label="$t('common.icon')" prop="icon">
            <ArtIconSelector
              v-model="formData.icon"
              :iconType="IconTypeEnum.UNICODE"
              :text="$t('common.pleaseSelect')"
              width="100%"
            />
          </ElFormItem>

          <div class="grid grid-cols-2 gap-4">
            <ElFormItem :label="$t('permission.keepAlive')" prop="keepAlive">
              <ElSwitch v-model="formData.keepAlive" />
            </ElFormItem>
            <ElFormItem :label="$t('permission.isHide')" prop="isHide">
              <ElSwitch v-model="formData.isHide" />
            </ElFormItem>
            <ElFormItem :label="$t('permission.isFullPage')" prop="isFullPage">
              <ElSwitch v-model="formData.isFullPage" />
            </ElFormItem>
            <ElFormItem :label="$t('permission.externalLink')" prop="link">
              <ElInput v-model="formData.link" :placeholder="$t('common.pleaseInput')" />
            </ElFormItem>
          </div>
        </template>

        <template v-else>
          <ElFormItem :label="$t('permission.buttonName')" prop="authTitle">
            <ElInput v-model="formData.authTitle" :placeholder="$t('common.pleaseInput')" />
          </ElFormItem>
          <ElFormItem :label="$t('permission.permissionMark')" prop="authMark">
            <ElInput v-model="formData.authMark" placeholder="user:btn:add" />
          </ElFormItem>
        </template>

        <ElFormItem :label="$t('common.sort')" prop="order">
          <ElInputNumber v-model="formData.order" :min="0" :max="9999" class="!w-full" />
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
        <ElButton @click="drawerVisible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </ElButton>
      </template>
    </ElDrawer>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, reactive, ref } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { FolderOpened, Operation, Plus, Refresh, Search } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtIconSelector from '@/components/core/base/art-icon-selector/index.vue'
  import { IconTypeEnum } from '@/enums/appEnum'
  import type { ColumnOption } from '@/types'
  import {
    addPermission,
    deletePermission,
    fetchPermissionTree,
    updatePermission,
    type PermissionInfo,
    type PermissionTree
  } from '@/api/system/permission'

  defineOptions({ name: 'Permission' })

  const { t, te } = useI18n()

  type PermissionFormData = {
    menu_type: number
    parent_id: string
    title: string
    name: string
    path: string
    component: string
    icon: string
    keepAlive: boolean
    isHide: boolean
    isFullPage: boolean
    link: string
    authTitle: string
    authMark: string
    order: number
    remark: string
  }

  const searchForm = reactive({
    keyword: '',
    menu_type: undefined as number | undefined
  })

  const loading = ref(false)
  const expanded = ref(true)
  const tableRef = ref<any>()
  const rawTree = ref<PermissionTree[]>([])

  const columns = computed<ColumnOption[]>(() => [
    { prop: 'title', label: t('common.permissionName'), minWidth: 220, useSlot: true },
    { prop: 'menu_type', label: t('common.type'), width: 90, useSlot: true },
    {
      prop: 'identifier',
      label: `${t('permission.routeName')} / ${t('permission.permissionMark')}`,
      minWidth: 180,
      useSlot: true
    },
    { prop: 'order', label: t('common.sort'), width: 80 },
    { prop: 'created_at', label: t('common.createTime'), width: 180 },
    { prop: 'action', label: t('common.actions'), width: 220, fixed: 'right', useSlot: true }
  ])

  const translateLocaleText = (value?: string) => {
    if (!value) {
      return ''
    }

    if (te(value)) {
      return t(value)
    }

    return value
  }

  const getDisplayName = (row: PermissionInfo) => {
    return translateLocaleText(row.title) || translateLocaleText(row.name) || row.code || '-'
  }

  const comparePermissionOrder = (left: PermissionTree, right: PermissionTree) => {
    const orderDiff = (left.order ?? 0) - (right.order ?? 0)
    if (orderDiff !== 0) {
      return orderDiff
    }

    return String(left.id || '').localeCompare(String(right.id || ''))
  }

  const normalizeTree = (nodes: PermissionTree[] = []): PermissionTree[] => {
    return nodes
      .filter((node) => node.menu_type === 0 || node.menu_type === 1)
      .map((node) => ({
        ...node,
        title: translateLocaleText(node.title),
        name: translateLocaleText(node.name),
        children: normalizeTree(node.children || [])
      }))
      .sort(comparePermissionOrder)
  }

  const keywordMatch = (node: PermissionTree) => {
    const keyword = searchForm.keyword.trim().toLowerCase()
    if (!keyword) {
      return true
    }

    return [translateLocaleText(node.title), translateLocaleText(node.name), node.path, node.code]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  }

  const filterTree = (nodes: PermissionTree[]): PermissionTree[] => {
    return nodes
      .map((node) => {
        const children = filterTree(node.children || [])
        const typeMatched =
          searchForm.menu_type === undefined || node.menu_type === searchForm.menu_type
        const matched = keywordMatch(node) && typeMatched

        if (matched || children.length > 0) {
          return {
            ...node,
            children
          }
        }

        return null
      })
      .filter(Boolean) as PermissionTree[]
  }

  const tableData = computed(() => filterTree(rawTree.value))
  const currentId = ref('')

  const collectDescendantIds = (
    nodes: PermissionTree[],
    targetId: string,
    result = new Set<string>()
  ) => {
    for (const node of nodes) {
      if (node.id === targetId) {
        const collect = (item: PermissionTree) => {
          if (item.id) {
            result.add(item.id)
          }
          ;(item.children || []).forEach(collect)
        }
        collect(node)
        return result
      }

      if (node.children?.length) {
        collectDescendantIds(node.children, targetId, result)
      }
    }

    return result
  }

  const menuOnlyTree = (nodes: PermissionTree[]): PermissionTree[] => {
    return nodes
      .filter((node) => node.menu_type === 0)
      .map((node) => ({
        ...node,
        children: menuOnlyTree(node.children || [])
      }))
  }

  const parentOptions = computed(() => {
    const roots = menuOnlyTree(rawTree.value)
    const rootNode = { id: '', title: t('permission.rootPermission'), children: roots }

    if (!currentId.value) {
      return [rootNode]
    }

    const excludedIds = collectDescendantIds(rawTree.value, currentId.value)
    const filterNodes = (nodes: PermissionTree[]): PermissionTree[] =>
      nodes
        .filter((node) => !excludedIds.has(node.id || ''))
        .map((node) => ({
          ...node,
          children: filterNodes(node.children || [])
        }))

    return [{ ...rootNode, children: filterNodes(roots) }]
  })

  const fetchData = async () => {
    loading.value = true
    try {
      const res = await fetchPermissionTree()
      rawTree.value = normalizeTree(res.data?.result || [])
    } catch (error) {
      console.error('fetch permission tree failed:', error)
      ElMessage.error(t('common.updateFailed'))
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    expanded.value = true
  }

  const handleReset = () => {
    Object.assign(searchForm, {
      keyword: '',
      menu_type: undefined
    })
    expanded.value = true
  }

  const flattenTree = (nodes: PermissionTree[]): PermissionTree[] => {
    return nodes.flatMap((node) => [node, ...flattenTree(node.children || [])])
  }

  const toggleExpand = () => {
    expanded.value = !expanded.value
    flattenTree(tableData.value).forEach((row) => {
      tableRef.value?.elTableRef?.toggleRowExpansion(row, expanded.value)
    })
  }

  const drawerVisible = ref(false)
  const drawerMode = ref<'add' | 'edit'>('add')
  const submitLoading = ref(false)
  const formRef = ref<FormInstance>()

  const drawerTitle = computed(() =>
    drawerMode.value === 'add' ? t('buttons.addPermission') : t('buttons.updatePermission')
  )

  const createDefaultForm = (): PermissionFormData => ({
    menu_type: 0,
    parent_id: '',
    title: '',
    name: '',
    path: '',
    component: '',
    icon: '',
    keepAlive: false,
    isHide: false,
    isFullPage: false,
    link: '',
    authTitle: '',
    authMark: '',
    order: 0,
    remark: ''
  })

  const formData = reactive<PermissionFormData>(createDefaultForm())

  const formRules: FormRules = {
    menu_type: [{ required: true, message: t('common.pleaseSelect'), trigger: 'change' }],
    title: [
      {
        validator: (_rule, value, callback) => {
          if (formData.menu_type === 0 && !value) {
            callback(new Error(t('common.pleaseInput')))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ],
    name: [
      {
        validator: (_rule, value, callback) => {
          if (formData.menu_type === 0 && !value) {
            callback(new Error(t('common.pleaseInput')))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ],
    path: [
      {
        validator: (_rule, value, callback) => {
          if (formData.menu_type === 0 && !value) {
            callback(new Error(t('permission.pathRequired')))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ],
    authTitle: [
      {
        validator: (_rule, value, callback) => {
          if (formData.menu_type === 1 && !value) {
            callback(new Error(t('permission.authTitleRequired')))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ],
    authMark: [
      {
        validator: (_rule, value, callback) => {
          if (formData.menu_type === 1 && !value) {
            callback(new Error(t('permission.authMarkRequired')))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ]
  }

  const resetForm = () => {
    Object.assign(formData, createDefaultForm())
    currentId.value = ''
    formRef.value?.clearValidate()
  }

  const openCreate = (parentId = '') => {
    drawerMode.value = 'add'
    resetForm()
    formData.parent_id = parentId
    drawerVisible.value = true
  }

  const openEdit = (row: PermissionTree) => {
    drawerMode.value = 'edit'
    resetForm()
    currentId.value = row.id || ''
    Object.assign(formData, {
      menu_type: row.menu_type,
      parent_id: row.parent_id || '',
      title: translateLocaleText(row.title) || '',
      name: translateLocaleText(row.name) || '',
      path: row.path || '',
      component: row.component || '',
      icon: row.icon || '',
      keepAlive: row.keepAlive || false,
      isHide: row.isHide || false,
      isFullPage: row.isFullPage || false,
      link: row.link || '',
      authTitle: translateLocaleText(row.title) || '',
      authMark: row.code || row.name || '',
      order: row.order || 0,
      remark: row.remark || ''
    })
    drawerVisible.value = true
  }

  const buildSubmitPayload = (): Partial<PermissionInfo> => {
    if (formData.menu_type === 0) {
      return {
        menu_type: 0,
        parent_id: formData.parent_id || undefined,
        title: formData.title,
        name: formData.name,
        path: formData.path,
        component: formData.component || undefined,
        icon: formData.icon || undefined,
        keepAlive: formData.keepAlive,
        isHide: formData.isHide,
        isFullPage: formData.isFullPage,
        link: formData.link || undefined,
        order: formData.order,
        remark: formData.remark || undefined
      }
    }

    return {
      menu_type: 1,
      parent_id: formData.parent_id || undefined,
      title: formData.authTitle,
      code: formData.authMark,
      name: formData.authMark.replace(/:/g, '_'),
      order: formData.order,
      remark: formData.remark || undefined
    }
  }

  const handleSubmit = async () => {
    if (!formRef.value) {
      return
    }

    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) {
      return
    }

    submitLoading.value = true
    try {
      const payload = buildSubmitPayload()
      if (drawerMode.value === 'add') {
        await addPermission(payload)
        ElMessage.success(t('common.addSuccess'))
      } else {
        await updatePermission(currentId.value, payload)
        ElMessage.success(t('common.updateSuccess'))
      }

      drawerVisible.value = false
      await fetchData()
    } catch (error) {
      console.error('submit permission failed:', error)
      ElMessage.error(t('common.updateFailed'))
    } finally {
      submitLoading.value = false
    }
  }

  const handleDelete = async (row: PermissionTree) => {
    const name = getDisplayName(row)
    const confirmed = await ElMessageBox.confirm(
      t('common.confirmDeletePermission', { name }),
      t('common.tips'),
      { type: 'warning' }
    ).catch(() => false)

    if (!confirmed) {
      return
    }

    try {
      await deletePermission(row.id || '')
      ElMessage.success(t('common.deleteSuccess'))
      await fetchData()
    } catch (error) {
      console.error('delete permission failed:', error)
      ElMessage.error(t('common.deleteFailed'))
    }
  }

  onMounted(() => {
    fetchData()
  })
</script>

<style scoped lang="scss">
  :deep(.el-table__body td:nth-child(1) .cell) {
    display: flex;
    align-items: center;
    white-space: nowrap;
  }

  :deep(.el-table__body td:nth-child(1) .el-table__expand-icon),
  :deep(.el-table__body td:nth-child(1) .el-table__indent) {
    flex: 0 0 auto;
  }

  .permission-title-cell {
    line-height: 1;
  }
</style>
