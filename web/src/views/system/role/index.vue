<template>
  <div class="art-full-height">
    <ElContainer class="h-full">
      <!-- 左侧部门树 -->
      <ElAside width="260px" class="dept-aside">
        <ElCard shadow="never" class="h-full dept-card">
          <template #header>
            <span class="font-medium">{{ $t('department.title', '部门') }}</span>
          </template>
          
          <div class="dept-content">
            <ElInput
              v-model="treeFilterText"
              :placeholder="$t('department.search', '搜索部门')"
              clearable
              size="small"
              :prefix-icon="Search"
              class="mb-3"
            />
            <ElScrollbar class="dept-tree-wrapper">
              <ElTree
                ref="treeRef"
                :data="departmentTree"
                :props="treeProps"
                :filter-node-method="filterNode"
                :expand-on-click-node="false"
                :highlight-current="true"
                :indent="16"
                node-key="id"
                default-expand-all
                @node-click="handleNodeClick"
              >
                <template #default="{ node, data }">
                  <div class="tree-node">
                    <ElIcon class="text-blue-500" :size="14"><OfficeBuilding /></ElIcon>
                    <span class="node-label" :title="node.label">{{ node.label }}</span>
                    <ElBadge
                      v-if="getDepartmentRoleCount(data.id) > 0"
                      :value="getDepartmentRoleCount(data.id)"
                      :max="99"
                      type="info"
                    />
                  </div>
                </template>
              </ElTree>
            </ElScrollbar>
          </div>
        </ElCard>
      </ElAside>

      <!-- 右侧主内容区 -->
      <ElMain class="main-content">
        <template v-if="selectedDepartment">
          <!-- 搜索区域 -->
          <div class="search-area">
            <div class="search-form">
              <div class="search-item">
                <span class="search-label">{{ $t('common.dept', '部门') }}</span>
                <ElBreadcrumb separator="/" class="dept-breadcrumb">
                  <ElBreadcrumbItem>{{ selectedDepartment.name }}</ElBreadcrumbItem>
                </ElBreadcrumb>
              </div>
              <div class="search-item">
                <span class="search-label">{{ $t('role.scope', '范围') }}</span>
                <ElSwitch
                  v-model="showSubDeptRoles"
                  :active-text="$t('role.includeSub', '含下属')"
                  :inactive-text="$t('role.currentOnly', '仅当前')"
                  @change="handleScopeChange"
                />
              </div>
              <div class="search-item">
                <span class="search-label">{{ $t('role.name', '角色名称') }}</span>
                <ElInput
                  v-model="searchText"
                  :placeholder="$t('role.search', '搜索角色')"
                  clearable
                  style="width: 200px"
                  :prefix-icon="Search"
                />
              </div>
            </div>
          </div>

          <!-- 表格卡片 -->
          <ElCard class="art-table-card" shadow="never">
            <ArtTableHeader :loading="loading" v-model:columns="columnChecks" @refresh="refreshData">
              <template #left>
                <ElButton
                  v-auth="'role:btn:add'"
                  type="primary"
                  :icon="Plus"
                  @click="showDialog('add')"
                >
                  {{ $t('role.add', '新增角色') }}
                </ElButton>
              </template>
            </ArtTableHeader>
            
            <ArtTable
              :data="data"
              :loading="loading"
              :columns="columns"
              :pagination="pagination"
              :show-table-header="false"
              row-key="id"
              @row-click="handleRowClick"
              @row-dblclick="handleRowDblClick"
              @pagination:size-change="handleSizeChange"
              @pagination:current-change="handleCurrentChange"
            />
          </ElCard>
        </template>

        <!-- 未选择部门的提示 -->
        <div v-else class="empty-state">
          <ElEmpty :description="$t('role.selectDept', '请选择左侧部门查看角色')">
            <template #image>
              <ElIcon :size="60" class="text-gray-300"><OfficeBuilding /></ElIcon>
            </template>
          </ElEmpty>
        </div>
      </ElMain>
    </ElContainer>

    <!-- 角色详情抽屉 -->
    <RoleDetailDrawer
      v-model="detailDrawerVisible"
      :role-data="selectedRole"
      @edit="showDialog('edit', selectedRole!)"
      @permission="showPermissionDialog(selectedRole!)"
      @delete="deleteRole(selectedRole!)"
      @refresh="refreshData"
    />

    <!-- 角色编辑抽屉 -->
    <RoleEditDrawer
      v-model="dialogVisible"
      :dialog-type="dialogType"
      :role-data="currentRoleData"
      :department-id="selectedDepartment?.id"
      :department-name="selectedDepartment?.name"
      @success="refreshData"
    />

    <!-- 权限分配抽屉 -->
    <RolePermissionDrawer
      v-model="permissionDialog"
      :role-data="currentRoleData"
      @success="refreshData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, h, watch, onMounted } from 'vue'
import { dayjs, ElMessage, ElMessageBox, ElTree, ElTag, ElButton } from 'element-plus'
import { Search, OfficeBuilding, Plus } from '@element-plus/icons-vue'
import { fetchDepartmentTree } from '@/api/system/department'
import { fetchRoleList, deleteRole as deleteRoleApi, type RoleQueryParams } from '@/api/system/role'
import type { DepartmentTree, DepartmentInfo } from '@/typings/department'
import type { RoleInfo } from '@/api/system/role'
import { useI18n } from 'vue-i18n'
import { useTable } from '@/composables/useTable'
import { usePermission } from '@/composables/usePermission'
import ArtTable from '@/components/core/tables/art-table/index.vue'
import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
import RoleEditDrawer from './modules/role-edit-drawer.vue'
import RolePermissionDrawer from './modules/role-permission-drawer.vue'
import RoleDetailDrawer from './modules/role-detail-drawer.vue'

defineOptions({ name: 'Role' })

const { t: $t } = useI18n()
const { hasPermission } = usePermission()

// 响应式数据
const treeFilterText = ref('')
const searchText = ref('')
const showSubDeptRoles = ref(false)
const departmentTree = ref<DepartmentTree[]>([])
const selectedDepartment = ref<DepartmentInfo | null>(null)
const selectedRole = ref<RoleInfo | null>(null)
const departmentRoleCounts = ref<Record<string, number>>({})

// 弹窗
const dialogVisible = ref(false)
const permissionDialog = ref(false)
const detailDrawerVisible = ref(false)
const currentRoleData = ref<RoleInfo | undefined>(undefined)
const dialogType = ref<'add' | 'edit'>('add')

// 树组件
const treeRef = ref<InstanceType<typeof ElTree>>()
const treeProps = { children: 'children', label: 'name' }

// 使用 useTable 管理角色列表
const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  searchParams,
  handleSizeChange,
  handleCurrentChange,
  getData,
  refreshUpdate
} = useTable<typeof fetchRoleList>({
  core: {
    apiFn: fetchRoleList,
    apiParams: {} as RoleQueryParams,
    immediate: false,
    paginationKey: { current: 'page', size: 'pageSize' },
    columnsFactory: () => [
      { type: 'index', width: 80, label: $t('table.column.index'), align: 'center' },
      { prop: 'name', label: $t('role.name', '角色名称'), align: 'center', showOverflowTooltip: true },
      {
        prop: 'code',
        label: $t('role.code', '角色编码'),
        align: 'center',
        showOverflowTooltip: true,
        formatter: (row: RoleInfo) => h('code', { class: 'code-tag' }, row.code)
      },
      {
        prop: 'department_name',
        label: $t('common.dept', '部门'),
        align: 'center',
        showOverflowTooltip: true,
        formatter: (row: RoleInfo) => row.department_name || '-'
      },
      {
        prop: 'description',
        label: $t('common.desc', '描述'),
        align: 'center',
        showOverflowTooltip: true,
        formatter: (row: RoleInfo) => h('span', { class: 'text-gray-500' }, row.description || '-')
      },
      {
        prop: 'status',
        label: $t('common.status', '状态'),
        width: 80,
        align: 'center',
        formatter: (row: RoleInfo) => h(ElTag, { type: row.status === 1 ? 'success' : 'danger', size: 'small' }, () => row.status === 1 ? $t('common.enable', '启用') : $t('common.disable', '禁用'))
      },
      {
        prop: 'created_at',
        label: $t('common.createTime', '创建时间'),
        width: 160,
        align: 'center',
        formatter: (row: RoleInfo) => h('span', { class: 'text-gray-500 text-xs' }, dayjs(row.created_at).format('YYYY-MM-DD HH:mm'))
      },
      {
        prop: 'actions',
        label: $t('common.actions', '操作'),
        width: 200,
        align: 'center',
        fixed: 'right',
        formatter: (row: RoleInfo) => {
          const buttons = []
          if (hasPermission('role:btn:addPermission')) {
            buttons.push(h(ElButton, { type: 'warning', size: 'small', onClick: () => showPermissionDialog(row) }, () => $t('role.perm', '权限')))
          }
          if (hasPermission('role:btn:update')) {
            buttons.push(h(ElButton, { type: 'primary', size: 'small', onClick: () => showDialog('edit', row) }, () => $t('buttons.edit', '编辑')))
          }
          if (hasPermission('role:btn:delete')) {
            buttons.push(h(ElButton, { type: 'danger', size: 'small', onClick: () => deleteRole(row) }, () => $t('buttons.delete', '删除')))
          }
          return h('div', { class: 'flex gap-2 justify-center' }, buttons)
        }
      }
    ]
  },
  performance: {
    enableCache: true,
    cacheTime: 5 * 60 * 1000,
    debounceTime: 300
  }
})

const getDepartmentRoleCount = (deptId: string): number => {
  return departmentRoleCounts.value[deptId] || 0
}

const findDepartmentInTree = (dept: DepartmentTree, targetId: string): DepartmentTree | null => {
  if (dept.id === targetId) return dept
  if (dept.children?.length) {
    for (const child of dept.children) {
      const found = findDepartmentInTree(child, targetId)
      if (found) return found
    }
  }
  return null
}

const getAllSubDepartmentIds = (dept: DepartmentTree): string[] => {
  const ids = [dept.id]
  dept.children?.forEach(child => ids.push(...getAllSubDepartmentIds(child)))
  return ids
}

watch(searchText, () => {
  if (selectedDepartment.value) {
    ;(searchParams as any).page = 1
    loadRoleList()
  }
})

watch(treeFilterText, val => treeRef.value?.filter(val))

const filterNode = (value: string, data: any) => !value || data.name.includes(value)

const handleNodeClick = (data: DepartmentInfo) => {
  selectedDepartment.value = data
  selectedRole.value = null
  detailDrawerVisible.value = false
  ;(searchParams as any).page = 1
  loadRoleList()
}

const handleScopeChange = () => {
  ;(searchParams as any).page = 1
  loadRoleList()
}

const handleRowClick = (row: RoleInfo) => {
  selectedRole.value = row
}

const handleRowDblClick = (row: RoleInfo) => {
  selectedRole.value = row
  currentRoleData.value = row
  detailDrawerVisible.value = true
}

const loadDepartmentTree = async () => {
  try {
    const res = await fetchDepartmentTree()
    if (res.success && res.data) {
      departmentTree.value = res.data.result || []
    }
  } catch (e) {
    console.error('加载部门失败:', e)
    ElMessage.error('加载部门数据失败')
  }
}

const loadRoleList = async () => {
  if (!selectedDepartment.value) return
  
  let deptIds: string[]
  if (showSubDeptRoles.value) {
    let target: DepartmentTree | null = null
    for (const d of departmentTree.value) {
      target = findDepartmentInTree(d, selectedDepartment.value.id)
      if (target) break
    }
    deptIds = target ? getAllSubDepartmentIds(target) : [selectedDepartment.value.id]
  } else {
    deptIds = [selectedDepartment.value.id]
  }

  Object.assign(searchParams, {
    department_ids: deptIds.join(','),
    name: searchText.value || undefined
  })

  getData()
}

const showDialog = (type: 'add' | 'edit', role?: RoleInfo) => {
  dialogType.value = type
  currentRoleData.value = role
  dialogVisible.value = true
}

const showPermissionDialog = (role: RoleInfo) => {
  currentRoleData.value = role
  permissionDialog.value = true
}

const deleteRole = async (role: RoleInfo) => {
  const confirm = await ElMessageBox.confirm(
    `确定删除角色【${role.name}】吗？`,
    '确认删除',
    { type: 'warning' }
  ).catch(() => false)
  if (!confirm) return

  try {
    const res = await deleteRoleApi(role.id)
    if (res.success) {
      ElMessage.success('删除成功')
      detailDrawerVisible.value = false
      selectedRole.value = null
      refreshData()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    console.error('删除角色失败:', e)
    ElMessage.error('删除失败')
  }
}

const refreshData = () => refreshUpdate()

onMounted(() => loadDepartmentTree())
</script>

<style lang="scss" scoped>
:deep(.el-container) {
  height: 100%;
}

.dept-aside {
  height: 100%;
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  overflow: hidden;
}

.dept-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 0;
  border: none;
  
  :deep(.el-card__header) {
    flex-shrink: 0;
    padding: 12px 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
}

.dept-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.dept-tree-wrapper {
  flex: 1;
  min-height: 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  font-size: 13px;
  
  .node-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  :deep(.el-badge__content) {
    font-size: 10px;
    height: 16px;
    line-height: 16px;
    padding: 0 4px;
  }
}

.main-content {
  height: 100%;
  padding: 0;
  padding-left: 16px;
  display: flex;
  flex-direction: column;
  background: var(--el-fill-color-lighter);
  overflow: hidden;
}

.search-area {
  flex-shrink: 0;
  background: var(--el-bg-color);
  padding: 0 16px;
  height: 49px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 24px;
}

.search-item {
  display: flex;
  align-items: center;
  gap: 10px;
  
  :deep(.el-input),
  :deep(.el-select) {
    --el-component-size: 32px;
  }
  
  :deep(.el-switch) {
    --el-switch-height: 20px;
  }
}

.search-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.dept-breadcrumb {
  :deep(.el-breadcrumb__item) {
    .el-breadcrumb__inner {
      color: var(--el-color-primary);
      font-weight: 500;
    }
  }
}

.art-table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  margin: 16px;
  margin-left: 0;
  margin-top: 16px;
  border-radius: 8px;
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }
  
  .table-header {
    flex-shrink: 0;
    margin-bottom: 12px;
  }
  
  :deep(.art-table) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }
}

.code-tag {
  font-size: 12px;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
