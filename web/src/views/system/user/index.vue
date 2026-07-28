<template>
  <div class="art-full-height !flex-row gap-4 min-h-0">
    <ElCard shadow="never" class="h-full w-[280px] shrink-0">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-[var(--el-text-color-primary)]">
            {{ $t('common.department') }}
          </span>
          <ElTag v-if="selectedDepartment" size="small" type="primary">
            {{ selectedDepartment.name }}
          </ElTag>
        </div>
      </template>

      <div class="flex h-full min-h-0 flex-col">
        <ElInput
          v-model="treeKeyword"
          :placeholder="$t('department.search')"
          clearable
          class="mb-3"
        />

        <ElScrollbar class="min-h-0 flex-1">
          <ElTree
            ref="treeRef"
            node-key="id"
            :current-node-key="selectedDepartmentId"
            :data="departmentTree"
            :props="{ label: 'name', children: 'children' }"
            :filter-node-method="filterDepartmentNode"
            :highlight-current="true"
            :expand-on-click-node="false"
            default-expand-all
            @node-click="handleDepartmentSelect"
          >
            <template #default="{ data }">
              <div class="flex min-w-0 items-center gap-2">
                <ElIcon class="text-sky-500"><OfficeBuilding /></ElIcon>
                <span class="truncate">{{ data.name }}</span>
              </div>
            </template>
          </ElTree>
        </ElScrollbar>
      </div>
    </ElCard>

    <ElCard shadow="never" class="art-table-card !mt-0 h-full min-w-0 flex-1">
      <div
        class="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-lighter)] px-4 py-3"
      >
        <div class="min-w-0">
          <div class="text-xs text-[var(--el-text-color-secondary)]">
            {{ $t('department.scope') }}
          </div>
          <div class="mt-1 truncate text-sm font-medium text-[var(--el-text-color-primary)]">
            {{ selectedDepartment?.name || $t('user.selectDepartmentTip') }}
          </div>
        </div>

        <ElSwitch
          v-model="includeChildren"
          inline-prompt
          :active-text="$t('permission.dataScopeDeptAndChild')"
          :inactive-text="$t('permission.dataScopeDeptOnly')"
          :disabled="!selectedDepartment"
          @change="handleScopeChange"
        />
      </div>

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
              v-auth="'user:btn:addUser'"
              type="primary"
              :icon="Plus"
              :disabled="!selectedDepartment"
              @click="openCreate"
            >
              {{ $t('user.addUser') }}
            </ElButton>
            <ElButton
              v-auth="'user:btn:deleteUser'"
              type="danger"
              :icon="Delete"
              :disabled="selectedIds.length === 0"
              @click="handleBatchDelete"
            >
              {{ $t('buttons.batchDelete') }}
            </ElButton>
          </ElSpace>
        </template>
      </ArtTableHeader>

      <ArtTable
        row-key="id"
        :data="tableData"
        :columns="columns"
        :pagination="pagination"
        :loading="loading"
        fit
        @selection-change="handleSelectionChange"
        @pagination:current-change="handlePageChange"
        @pagination:size-change="handleSizeChange"
      >
        <template #avatar="{ row }">
          <ElAvatar :size="36" :src="getAvatarUrl(row.avatar)">
            <ElIcon><User /></ElIcon>
          </ElAvatar>
        </template>

        <template #gender="{ row }">
          <span>{{ formatGender(row.gender) }}</span>
        </template>

        <template #status="{ row }">
          <ElTag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
          </ElTag>
        </template>

        <template #action="{ row }">
          <ElSpace wrap :size="4">
            <ElButton
              v-auth="'user:btn:updateUser'"
              type="primary"
              link
              size="small"
              @click="openEdit(row)"
            >
              {{ $t('buttons.edit') }}
            </ElButton>

            <ElDropdown trigger="click" @command="handleActionCommand">
              <ElButton link type="primary" size="small">
                {{ $t('common.more') }}
                <ElIcon class="ml-1"><ArrowDown /></ElIcon>
              </ElButton>

              <template #dropdown>
                <ElDropdownMenu>
                  <ElDropdownItem
                    v-if="hasPermission('user:btn:addRole')"
                    :command="{ action: 'roles', row }"
                  >
                    {{ $t('user.assignRoles') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="hasPermission('user:btn:permissionList')"
                    :command="{ action: 'permissions', row }"
                  >
                    {{ $t('user.viewPermissions') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="hasPermission('user:btn:reset_password')"
                    :command="{ action: 'resetPassword', row }"
                  >
                    {{ $t('user.resetPassword') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="hasPermission('user:btn:deleteUser')"
                    :command="{ action: 'delete', row }"
                  >
                    {{ $t('buttons.delete') }}
                  </ElDropdownItem>
                </ElDropdownMenu>
              </template>
            </ElDropdown>
          </ElSpace>
        </template>
      </ArtTable>
    </ElCard>

    <UserEditDrawer
      v-model="editVisible"
      :dialog-type="editMode"
      :user-data="currentUserData"
      :department-id="selectedDepartment?.id"
      @success="fetchData"
    />

    <UserRoleDrawer v-model="roleDrawerVisible" :user-data="currentUserData" @success="fetchData" />

    <UserPermissionDrawer
      v-model:visible="permissionDrawerVisible"
      :user-data="currentUserData || null"
    />

    <UserResetPasswordDrawer
      v-model="resetPasswordDrawerVisible"
      :user-data="currentUserData || null"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, reactive, ref, watch } from 'vue'
  import { dayjs, ElMessage, ElMessageBox } from 'element-plus'
  import { ArrowDown, Delete, OfficeBuilding, Plus, User } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
  import type { ColumnOption } from '@/types'
  import {
    deleteUser,
    deleteUserList,
    fetchUserInfo,
    fetchUserList,
    type UserInfo
  } from '@/api/system/user'
  import { fetchDepartmentTree, type DepartmentInfo } from '@/api/system/department'
  import { usePermission } from '@/composables/usePermission'
  import { getAvatarUrl } from '@/utils'
  import UserEditDrawer from './modules/user-edit-drawer.vue'
  import UserPermissionDrawer from './modules/user-permission-drawer.vue'
  import UserResetPasswordDrawer from './modules/user-reset-password-drawer.vue'
  import UserRoleDrawer from './modules/user-role-drawer.vue'

  defineOptions({ name: 'User' })

  type DepartmentTreeNode = DepartmentInfo & {
    children?: DepartmentTreeNode[]
  }

  const { hasPermission } = usePermission()
  const { t: $t } = useI18n()

  const treeRef = ref<any>()
  const treeKeyword = ref('')
  const departmentTree = ref<DepartmentTreeNode[]>([])
  const selectedDepartmentId = ref('')

  const selectedDepartment = computed(() =>
    findDepartmentById(departmentTree.value, selectedDepartmentId.value)
  )

  const includeChildren = ref(true)
  const searchForm = reactive({
    username: '',
    nickname: '',
    phone: '',
    status: undefined as number | undefined
  })

  const searchItems = [
    {
      key: 'username',
      type: 'input',
      label: $t('user.username'),
      props: {
        placeholder: $t('user.username'),
        clearable: true
      }
    },
    {
      key: 'nickname',
      type: 'input',
      label: $t('user.nickname'),
      props: {
        placeholder: $t('user.nickname'),
        clearable: true
      }
    },
    {
      key: 'phone',
      type: 'input',
      label: $t('user.phone'),
      props: {
        placeholder: $t('user.phone'),
        clearable: true
      }
    },
    {
      key: 'status',
      type: 'select',
      label: $t('common.status'),
      props: {
        placeholder: $t('common.status'),
        clearable: true,
        options: [
          { label: $t('common.enabled'), value: 1 },
          { label: $t('common.disabled'), value: 0 }
        ]
      }
    }
  ]

  const loading = ref(false)
  const tableData = ref<UserInfo[]>([])
  const selectedIds = ref<string[]>([])
  const pagination = reactive({
    current: 1,
    size: 10,
    total: 0
  })

  const columns = ref<ColumnOption[]>([
    { type: 'selection', width: 55 },
    { prop: 'avatar', label: $t('common.icon'), width: 80, useSlot: true },
    { prop: 'username', label: $t('user.username'), minWidth: 140 },
    { prop: 'nickname', label: $t('user.nickname'), minWidth: 140 },
    { prop: 'phone', label: $t('user.phone'), minWidth: 140 },
    { prop: 'email', label: $t('user.email'), minWidth: 180 },
    { prop: 'gender', label: $t('user.gender'), width: 90, useSlot: true },
    { prop: 'status', label: $t('common.status'), width: 90, useSlot: true },
    {
      prop: 'created_at',
      label: $t('common.createTime'),
      width: 180,
      formatter: (row: UserInfo) => dayjs(row.created_at).format('YYYY-MM-DD HH:mm')
    },
    { prop: 'action', label: $t('common.actions'), width: 220, fixed: 'right', useSlot: true }
  ])

  const filterDepartmentNode = (value: string, data: Record<string, any>) => {
    if (!value) {
      return true
    }
    return data.name.toLowerCase().includes(value.toLowerCase())
  }

  watch(treeKeyword, (value) => {
    treeRef.value?.filter(value)
  })

  const findDepartmentById = (
    nodes: DepartmentTreeNode[],
    id: string
  ): DepartmentTreeNode | null => {
    for (const node of nodes) {
      if (node.id === id) {
        return node
      }
      if (node.children?.length) {
        const matched = findDepartmentById(node.children, id)
        if (matched) {
          return matched
        }
      }
    }
    return null
  }

  const collectDepartmentIds = (node: DepartmentTreeNode): string[] => {
    const ids = [node.id]
    node.children?.forEach((child) => {
      ids.push(...collectDepartmentIds(child))
    })
    return ids
  }

  const fetchDepartmentData = async () => {
    const res = await fetchDepartmentTree()
    departmentTree.value = (res.data?.result || []) as DepartmentTreeNode[]

    if (!selectedDepartmentId.value && departmentTree.value.length > 0) {
      selectedDepartmentId.value = departmentTree.value[0].id
    }
  }

  const fetchData = async () => {
    if (!selectedDepartment.value) {
      tableData.value = []
      pagination.total = 0
      return
    }

    const departmentIds = includeChildren.value
      ? collectDepartmentIds(selectedDepartment.value)
      : [selectedDepartment.value.id]

    loading.value = true
    try {
      const res = await fetchUserList({
        page: pagination.current,
        pageSize: pagination.size,
        username: searchForm.username || undefined,
        nickname: searchForm.nickname || undefined,
        phone: searchForm.phone || undefined,
        status: searchForm.status,
        department_ids: departmentIds.join(',')
      })

      tableData.value = res.data?.result || []
      selectedIds.value = []
      pagination.total = res.data?.total || 0

      if (pagination.current > 1 && tableData.value.length === 0) {
        pagination.current -= 1
        await fetchData()
      }
    } finally {
      loading.value = false
    }
  }

  const handleDepartmentSelect = async (data: DepartmentTreeNode) => {
    selectedDepartmentId.value = data.id
    pagination.current = 1
    await fetchData()
  }

  const handleScopeChange = async () => {
    pagination.current = 1
    await fetchData()
  }

  const handleSearch = async () => {
    pagination.current = 1
    await fetchData()
  }

  const handleReset = async () => {
    Object.assign(searchForm, {
      username: '',
      nickname: '',
      phone: '',
      status: undefined
    })
    pagination.current = 1
    await fetchData()
  }

  const handleSelectionChange = (rows: UserInfo[]) => {
    selectedIds.value = rows.map((item) => item.id)
  }

  const handlePageChange = async (page: number) => {
    pagination.current = page
    await fetchData()
  }

  const handleSizeChange = async (size: number) => {
    pagination.size = size
    pagination.current = 1
    await fetchData()
  }

  const formatGender = (gender?: number) => {
    if (gender === 1) {
      return $t('user.male')
    }
    if (gender === 0) {
      return $t('user.female')
    }
    return $t('common.unknown')
  }

  const enrichUserData = async (row: UserInfo) => {
    try {
      const res = await fetchUserInfo(row.id)
      return {
        ...row,
        ...(res.data || {}),
        department_id: res.data?.department_id || row.department_id || selectedDepartment.value?.id,
        department_name:
          res.data?.department_name || row.department_name || selectedDepartment.value?.name
      }
    } catch {
      return {
        ...row,
        department_id: row.department_id || selectedDepartment.value?.id,
        department_name: row.department_name || selectedDepartment.value?.name
      }
    }
  }

  const currentUserData = ref<UserInfo>()
  const editVisible = ref(false)
  const editMode = ref<'add' | 'edit'>('add')
  const roleDrawerVisible = ref(false)
  const permissionDrawerVisible = ref(false)
  const resetPasswordDrawerVisible = ref(false)

  const openCreate = () => {
    currentUserData.value = undefined
    editMode.value = 'add'
    editVisible.value = true
  }

  const openEdit = async (row: UserInfo) => {
    currentUserData.value = await enrichUserData(row)
    editMode.value = 'edit'
    editVisible.value = true
  }

  const openRoleDrawer = async (row: UserInfo) => {
    currentUserData.value = await enrichUserData(row)
    roleDrawerVisible.value = true
  }

  const openPermissionDrawer = async (row: UserInfo) => {
    currentUserData.value = await enrichUserData(row)
    permissionDrawerVisible.value = true
  }

  const openResetPasswordDrawer = async (row: UserInfo) => {
    currentUserData.value = await enrichUserData(row)
    resetPasswordDrawerVisible.value = true
  }

  const handleDelete = async (row: UserInfo) => {
    await ElMessageBox.confirm(
      $t('user.confirmDeleteUser', { name: row.username }),
      $t('common.deleteConfirm'),
      {
        type: 'warning'
      }
    )

    await deleteUser(row.id)
    ElMessage.success($t('common.deleteSuccess'))
    await fetchData()
  }

  const handleBatchDelete = async () => {
    await ElMessageBox.confirm(
      $t('common.confirmBatchDelete', { count: selectedIds.value.length }),
      $t('common.confirm'),
      {
        type: 'warning'
      }
    )

    await deleteUserList({ ids: selectedIds.value })
    selectedIds.value = []
    ElMessage.success($t('common.deleteSuccess'))
    await fetchData()
  }

  const handleActionCommand = async ({ action, row }: { action: string; row: UserInfo }) => {
    if (action === 'roles') {
      await openRoleDrawer(row)
      return
    }

    if (action === 'permissions') {
      await openPermissionDrawer(row)
      return
    }

    if (action === 'resetPassword') {
      await openResetPasswordDrawer(row)
      return
    }

    if (action === 'delete') {
      await handleDelete(row)
    }
  }

  onMounted(async () => {
    await fetchDepartmentData()
    await fetchData()
  })
</script>
