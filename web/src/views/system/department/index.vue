<template>
  <div class="art-full-height">
    <ElCard class="art-table-card h-full" shadow="never">
      <ArtSearchBar
        :model-value="searchForm"
        @update:model-value="Object.assign(searchForm, $event)"
        :items="searchItems"
        @search="handleSearch"
        @reset="handleReset"
      />

      <ArtTableHeader v-model:columns="columns" :loading="loading" @refresh="fetchData">
        <template #left>
          <ElSpace wrap>
            <ElButton
              v-auth="'department:btn:add'"
              type="primary"
              :icon="Plus"
              @click="openCreate()"
            >
              {{ $t('department.addDepartment') }}
            </ElButton>

            <ElButton @click="toggleExpand">
              {{ expanded ? $t('department.collapseAll') : $t('department.expandAll') }}
            </ElButton>
          </ElSpace>
        </template>
      </ArtTableHeader>

      <ArtTable
        ref="tableRef"
        row-key="id"
        :data="tableData"
        :columns="columns"
        :loading="loading"
        :pagination="undefined"
        :tree-props="{ children: 'children' }"
        default-expand-all
        fit
      >
        <template #name="{ row }">
          <div class="flex min-w-0 items-center gap-2">
            <ElIcon class="text-sky-500"><OfficeBuilding /></ElIcon>
            <span class="truncate">{{ row.name }}</span>
          </div>
        </template>

        <template #tenant="{ row }">
          <ElTag v-if="row.tenant_id" size="small" type="primary">
            {{ getTenantName(row.tenant_id) }}
          </ElTag>
          <span v-else class="text-[var(--el-text-color-secondary)]">-</span>
        </template>

        <template #status="{ row }">
          <ElTag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
          </ElTag>
        </template>

        <template #action="{ row }">
          <ElSpace wrap :size="4">
            <ElButton
              v-auth="'department:btn:add'"
              type="primary"
              link
              size="small"
              @click="openCreate(row.id)"
            >
              {{ $t('department.addSub') }}
            </ElButton>

            <ElButton
              v-auth="'department:btn:update'"
              type="primary"
              link
              size="small"
              @click="openEdit(row)"
            >
              {{ $t('buttons.edit') }}
            </ElButton>
            <ElButton
              v-auth="'department:btn:delete'"
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              {{ $t('buttons.delete') }}
            </ElButton>
          </ElSpace>
        </template>
      </ArtTable>
    </ElCard>

    <ElDrawer v-model="drawerVisible" :title="drawerTitle" size="640px" @closed="resetForm">
      <div
        class="mb-4 rounded-lg border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-lighter)] px-4 py-3"
      >
        <div class="text-xs text-[var(--el-text-color-secondary)]">{{
          $t('department.currentTenant')
        }}</div>
        <div class="mt-1 text-sm font-medium text-[var(--el-text-color-primary)]">
          {{ activeTenantName }}
        </div>
      </div>

      <ElForm ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <ElFormItem :label="$t('department.parent')" prop="parent_id">
          <ElTreeSelect
            v-model="formData.parent_id"
            :data="parentTreeData"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            check-strictly
            clearable
            class="w-full"
            :placeholder="$t('department.selectParent')"
          />
        </ElFormItem>
        <ElFormItem :label="$t('department.name')" prop="name">
          <ElInput v-model="formData.name" :placeholder="$t('department.nameRequired')" />
        </ElFormItem>
        <ElFormItem :label="$t('department.code')" prop="code">
          <ElInput v-model="formData.code" :placeholder="$t('department.codeRequired')" />
        </ElFormItem>
        <ElFormItem :label="$t('department.principal')" prop="principal">
          <ElInput v-model="formData.principal" :placeholder="$t('department.principalRequired')" />
        </ElFormItem>
        <ElFormItem :label="$t('department.phone')" prop="phone">
          <ElInput v-model="formData.phone" :placeholder="$t('department.phone')" />
        </ElFormItem>
        <ElFormItem :label="$t('department.email')" prop="email">
          <ElInput v-model="formData.email" :placeholder="$t('department.email')" />
        </ElFormItem>
        <ElFormItem :label="$t('department.sort')" prop="sort">
          <ElInputNumber v-model="formData.sort" :min="0" :max="9999" class="!w-full" />
        </ElFormItem>
        <ElFormItem :label="$t('common.status')" prop="status">
          <ElRadioGroup v-model="formData.status">
            <ElRadio :label="1">{{ $t('common.enabled') }}</ElRadio>
            <ElRadio :label="0">{{ $t('common.disabled') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem :label="$t('department.remark')" prop="remark">
          <ElInput
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            :placeholder="$t('department.remark')"
          />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <ElButton @click="drawerVisible = false">{{ $t('buttons.cancel') }}</ElButton>
        <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">{{
          $t('buttons.confirm')
        }}</ElButton>
      </template>
    </ElDrawer>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, reactive, ref } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { OfficeBuilding, Plus } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { useUserStore } from '@/store/modules/user'
  import { usePermission } from '@/composables/usePermission'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
  import type { ColumnOption } from '@/types'
  import {
    addDepartment,
    deleteDepartment,
    fetchDepartmentList,
    type DepartmentInfo,
    updateDepartment
  } from '@/api/system/department'
  import { fetchTenantList, type TenantInfo } from '@/api/system/tenant'

  defineOptions({ name: 'Department' })

  type DepartmentRow = DepartmentInfo & { children?: DepartmentRow[] }

  const { t: $t } = useI18n()
  const userStore = useUserStore()
  const { isSuperAdmin } = usePermission()

  const searchForm = reactive({
    tenant_id: '',
    name: '',
    principal: '',
    status: undefined as number | undefined
  })

  const tenantOptions = ref<TenantInfo[]>([])
  const loading = ref(false)
  const expanded = ref(true)
  const tableRef = ref<any>()
  const rawList = ref<DepartmentInfo[]>([])
  const currentEditId = ref('')

  const currentTenantId = computed(() => String(userStore.info?.tenant_id || ''))
  const tenantMap = computed(() =>
    tenantOptions.value.reduce<Record<string, string>>((acc, item) => {
      acc[item.id] = item.name
      return acc
    }, {})
  )

  const effectiveTenantId = computed(() => {
    if (isSuperAdmin.value) {
      return searchForm.tenant_id || currentTenantId.value
    }
    return currentTenantId.value
  })

  const activeTenantName = computed(() => {
    const tenantId = effectiveTenantId.value
    if (!tenantId) {
      return $t('department.unselectedTenant')
    }
    return tenantMap.value[tenantId] || `${$t('department.tenantLabel')} ${tenantId}`
  })

  const searchItems = computed(() => {
    const items: any[] = []

    if (isSuperAdmin.value) {
      items.push({
        key: 'tenant_id',
        type: 'select',
        label: $t('department.tenantLabel'),
        props: {
          placeholder: $t('common.pleaseSelect') + $t('department.tenantLabel'),
          clearable: true,
          filterable: true,
          options: tenantOptions.value.map((item) => ({
            label: item.name,
            value: item.id
          }))
        }
      })
    }

    items.push(
      {
        key: 'name',
        type: 'input',
        label: $t('department.name'),
        props: {
          placeholder: $t('department.nameRequired'),
          clearable: true
        }
      },
      {
        key: 'principal',
        type: 'input',
        label: $t('department.principal'),
        props: {
          placeholder: $t('department.principalRequired'),
          clearable: true
        }
      },
      {
        key: 'status',
        type: 'select',
        label: $t('common.status'),
        props: {
          placeholder: $t('common.pleaseSelect') + $t('common.status'),
          clearable: true,
          options: [
            { label: $t('common.enabled'), value: 1 },
            { label: $t('common.disabled'), value: 0 }
          ]
        }
      }
    )

    return items
  })

  const columns = ref<ColumnOption[]>([
    ...(isSuperAdmin.value
      ? [
          {
            prop: 'tenant',
            label: $t('department.tenantLabel'),
            width: 160,
            useSlot: true
          } as ColumnOption
        ]
      : []),
    { prop: 'name', label: $t('department.name'), minWidth: 220, useSlot: true },
    { prop: 'code', label: $t('department.code'), minWidth: 140 },
    { prop: 'principal', label: $t('department.principal'), minWidth: 120 },
    { prop: 'phone', label: $t('department.phone'), minWidth: 140 },
    { prop: 'email', label: $t('department.email'), minWidth: 180 },
    { prop: 'sort', label: $t('department.sort'), width: 80 },
    { prop: 'status', label: $t('common.status'), width: 90, useSlot: true },
    { prop: 'created_at', label: $t('common.createTime'), width: 180 },
    { prop: 'action', label: $t('common.actions'), width: 220, fixed: 'right', useSlot: true }
  ])

  const buildTree = (items: DepartmentInfo[]): DepartmentRow[] => {
    const map = new Map<string, DepartmentRow>()
    const roots: DepartmentRow[] = []

    items.forEach((item) => {
      map.set(item.id, { ...item, children: [] })
    })

    map.forEach((item) => {
      if (item.parent_id && map.has(item.parent_id)) {
        map.get(item.parent_id)?.children?.push(item)
      } else {
        roots.push(item)
      }
    })

    const sortNodes = (nodes: DepartmentRow[]) => {
      nodes.sort((a, b) => (a.sort || 0) - (b.sort || 0))
      nodes.forEach((node) => {
        if (node.children?.length) {
          sortNodes(node.children)
        }
      })
    }

    sortNodes(roots)
    return roots
  }

  const matchesKeyword = (dept: DepartmentInfo) => {
    const nameMatched = !searchForm.name || dept.name.includes(searchForm.name)
    const principalMatched =
      !searchForm.principal || String(dept.principal || '').includes(searchForm.principal)
    const statusMatched = searchForm.status === undefined || dept.status === searchForm.status
    return nameMatched && principalMatched && statusMatched
  }

  const filterTree = (nodes: DepartmentRow[]): DepartmentRow[] => {
    return nodes
      .map((node) => {
        const children = filterTree(node.children || [])
        if (matchesKeyword(node) || children.length > 0) {
          return { ...node, children }
        }
        return null
      })
      .filter(Boolean) as DepartmentRow[]
  }

  const tableData = computed(() => filterTree(buildTree(rawList.value)))

  const collectDescendantIds = (nodes: DepartmentRow[], targetId: string): Set<string> => {
    const ids = new Set<string>()

    const walk = (items: DepartmentRow[]): boolean => {
      for (const item of items) {
        if (item.id === targetId) {
          const collect = (node: DepartmentRow) => {
            ids.add(node.id)
            node.children?.forEach(collect)
          }
          collect(item)
          return true
        }

        if (item.children?.length && walk(item.children)) {
          return true
        }
      }

      return false
    }

    walk(buildTree(rawList.value))
    return ids
  }

  const parentTreeData = computed(() => {
    const tree = buildTree(rawList.value)
    if (!currentEditId.value) {
      return [{ id: '', name: $t('department.topLevel'), children: tree }]
    }

    const excludedIds = collectDescendantIds(tree, currentEditId.value)
    const filterNodes = (nodes: DepartmentRow[]): DepartmentRow[] =>
      nodes
        .filter((node) => !excludedIds.has(node.id))
        .map((node) => ({
          ...node,
          children: node.children?.length ? filterNodes(node.children) : []
        }))

    return [{ id: '', name: $t('department.topLevel'), children: filterNodes(tree) }]
  })

  const getTenantName = (tenantId: string | null) => {
    if (!tenantId) {
      return '-'
    }
    return tenantMap.value[tenantId] || tenantId
  }

  const getDefaultTenantId = () => {
    if (!isSuperAdmin.value) {
      return ''
    }

    if (
      currentTenantId.value &&
      tenantOptions.value.some((item) => item.id === currentTenantId.value)
    ) {
      return currentTenantId.value
    }

    return tenantOptions.value[0]?.id || currentTenantId.value || ''
  }

  const syncTenantSelection = () => {
    if (!isSuperAdmin.value) {
      return
    }

    if (
      searchForm.tenant_id &&
      tenantOptions.value.some((item) => item.id === searchForm.tenant_id)
    ) {
      return
    }

    searchForm.tenant_id = getDefaultTenantId()
  }

  const fetchTenants = async () => {
    if (!isSuperAdmin.value) {
      tenantOptions.value = []
      return
    }

    const res = await fetchTenantList({ page: 1, pageSize: 1000 })
    tenantOptions.value = res.data?.result || []
    syncTenantSelection()
  }

  const fetchData = async () => {
    loading.value = true
    try {
      const res = await fetchDepartmentList({
        page: 1,
        pageSize: 9999,
        tenant_id: effectiveTenantId.value || undefined
      })
      rawList.value = res.data?.result || []
    } finally {
      loading.value = false
    }
  }

  const handleSearch = async () => {
    await fetchData()
  }

  const handleReset = async () => {
    Object.assign(searchForm, {
      tenant_id: getDefaultTenantId(),
      name: '',
      principal: '',
      status: undefined
    })
    await fetchData()
  }

  const flattenTree = (items: DepartmentRow[]): DepartmentRow[] => {
    const result: DepartmentRow[] = []
    const walk = (nodes: DepartmentRow[]) => {
      nodes.forEach((node) => {
        result.push(node)
        if (node.children?.length) {
          walk(node.children)
        }
      })
    }
    walk(items)
    return result
  }

  const toggleExpand = () => {
    expanded.value = !expanded.value
    flattenTree(tableData.value).forEach((row) => {
      tableRef.value?.elTableRef?.toggleRowExpansion(row, expanded.value)
    })
  }

  const drawerVisible = ref(false)
  const drawerMode = ref<'add' | 'edit'>('add')
  const drawerTitle = computed(() =>
    drawerMode.value === 'add' ? $t('department.addDepartment') : $t('department.editDepartment')
  )
  const submitLoading = ref(false)
  const formRef = ref<FormInstance>()

  const createDefaultForm = () => ({
    parent_id: '',
    name: '',
    code: '',
    principal: '',
    phone: '',
    email: '',
    sort: 0,
    status: 1,
    remark: ''
  })

  const formData = reactive(createDefaultForm())

  const formRules: FormRules = {
    name: [{ required: true, message: $t('department.nameRequired'), trigger: 'blur' }],
    code: [{ required: true, message: $t('department.codeRequired'), trigger: 'blur' }]
  }

  const resetForm = () => {
    Object.assign(formData, createDefaultForm())
    currentEditId.value = ''
    formRef.value?.clearValidate()
  }

  const openCreate = (parentId = '') => {
    drawerMode.value = 'add'
    resetForm()
    formData.parent_id = parentId
    drawerVisible.value = true
  }

  const openEdit = (row: DepartmentInfo) => {
    drawerMode.value = 'edit'
    resetForm()
    currentEditId.value = row.id
    Object.assign(formData, {
      parent_id: row.parent_id || '',
      name: row.name,
      code: row.code || '',
      principal: row.principal || '',
      phone: row.phone || '',
      email: row.email || '',
      sort: row.sort,
      status: row.status,
      remark: row.remark || ''
    })
    drawerVisible.value = true
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
      const payload = {
        tenant_id: isSuperAdmin.value ? effectiveTenantId.value || undefined : undefined,
        name: formData.name,
        code: formData.code,
        parent_id: formData.parent_id || null,
        principal: formData.principal || undefined,
        phone: formData.phone || undefined,
        email: formData.email || undefined,
        sort: formData.sort,
        status: formData.status,
        remark: formData.remark || undefined
      }

      if (drawerMode.value === 'add') {
        await addDepartment(payload)
        ElMessage.success($t('common.addSuccess'))
      } else {
        await updateDepartment(currentEditId.value, payload)
        ElMessage.success($t('common.updateSuccess'))
      }

      drawerVisible.value = false
      await fetchData()
    } finally {
      submitLoading.value = false
    }
  }

  const handleDelete = async (row: DepartmentInfo) => {
    const confirmed = await ElMessageBox.confirm(
      $t('department.deleteConfirm', { name: row.name }),
      $t('common.tips'),
      {
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmed) {
      return
    }

    await deleteDepartment(row.id)
    ElMessage.success($t('common.deleteSuccess'))
    await fetchData()
  }

  onMounted(async () => {
    await fetchTenants()
    await fetchData()
  })
</script>
