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
          <!-- 工具栏 -->
          <div class="toolbar">
            <div class="toolbar-left">
              <ElBreadcrumb separator="/">
                <ElBreadcrumbItem>{{ selectedDepartment.name }}</ElBreadcrumbItem>
                <ElBreadcrumbItem v-if="!showSubDeptRoles">
                  {{ $t('role.currentOnly', '仅当前部门') }}
                </ElBreadcrumbItem>
                <ElBreadcrumbItem v-else>
                  {{ $t('role.includeChild', '含下属部门') }}
                </ElBreadcrumbItem>
              </ElBreadcrumb>
              <ElSwitch
                v-model="showSubDeptRoles"
                :active-text="$t('role.includeSub', '含下属')"
                size="small"
                @change="handleScopeChange"
              />
            </div>
            <div class="toolbar-right">
              <ElInput
                v-model="searchText"
                :placeholder="$t('role.search', '搜索角色')"
                clearable
                size="small"
                style="width: 180px"
                :prefix-icon="Search"
              />
              <ElButton
                v-auth="'role:btn:add'"
                type="primary"
                size="small"
                :icon="Plus"
                @click="showDialog('add')"
              >
                {{ $t('role.add', '新增角色') }}
              </ElButton>
            </div>
          </div>

          <!-- 表格卡片 -->
          <ElCard class="art-table-card" shadow="never">
            <ArtTableHeader :loading="loading" @refresh="refreshData" />
            
            <ElTable
              v-loading="loading"
              :data="roles"
              border
              stripe
              highlight-current-row
              class="role-table"
              @row-click="handleRowClick"
              @row-dblclick="handleRowDblClick"
            >
              <ElTableColumn type="index" width="60" align="center" :label="$t('table.index', '#')" />
              <ElTableColumn prop="name" :label="$t('role.name', '角色名称')" min-width="120" show-overflow-tooltip />
              <ElTableColumn prop="code" :label="$t('role.code', '角色编码')" min-width="130" show-overflow-tooltip>
                <template #default="{ row }">
                  <code class="code-tag">{{ row.code }}</code>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="department_name" :label="$t('common.dept', '部门')" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.department_name || '-' }}
                </template>
              </ElTableColumn>
              <ElTableColumn prop="description" :label="$t('common.desc', '描述')" min-width="180" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="text-gray-500">{{ row.description || '-' }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="status" :label="$t('common.status', '状态')" width="80" align="center">
                <template #default="{ row }">
                  <ElTag :type="row.status === 1 ? 'success' : 'danger'" size="small">
                    {{ row.status === 1 ? $t('common.enable', '启用') : $t('common.disable', '禁用') }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="created_at" :label="$t('common.createTime', '创建时间')" width="160" align="center">
                <template #default="{ row }">
                  <span class="text-gray-500 text-xs">{{ dayjs(row.created_at).format('YYYY-MM-DD HH:mm') }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn :label="$t('common.actions', '操作')" width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <ElButton
                    v-auth="'role:btn:addPermission'"
                    type="warning"
                    size="small"
                    link
                    @click.stop="showPermissionDialog(row)"
                  >
                    {{ $t('role.perm', '权限') }}
                  </ElButton>
                  <ElButton
                    v-auth="'role:btn:update'"
                    type="primary"
                    size="small"
                    link
                    @click.stop="showDialog('edit', row)"
                  >
                    {{ $t('buttons.edit', '编辑') }}
                  </ElButton>
                  <ElButton
                    v-auth="'role:btn:delete'"
                    type="danger"
                    size="small"
                    link
                    @click.stop="deleteRole(row)"
                  >
                    {{ $t('buttons.delete', '删除') }}
                  </ElButton>
                </template>
              </ElTableColumn>
            </ElTable>

            <!-- 分页 -->
            <div class="pagination-wrapper">
              <span class="total-text">共 {{ total }} 条</span>
              <ElPagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="total"
                layout="sizes, prev, pager, next, jumper"
                small
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
              />
            </div>
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
import { ref, watch, onMounted } from 'vue'
import { dayjs, ElMessage, ElMessageBox, ElTree } from 'element-plus'
import { Search, OfficeBuilding, Plus } from '@element-plus/icons-vue'
import { fetchDepartmentTree } from '@/api/system/department'
import { fetchRoleList, deleteRole as deleteRoleApi } from '@/api/system/role'
import type { DepartmentTree, DepartmentInfo } from '@/typings/department'
import type { RoleInfo } from '@/api/system/role'
import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
import RoleEditDrawer from './modules/role-edit-drawer.vue'
import RolePermissionDrawer from './modules/role-permission-drawer.vue'
import RoleDetailDrawer from './modules/role-detail-drawer.vue'

defineOptions({ name: 'Role' })

// 响应式数据
const loading = ref(false)
const treeFilterText = ref('')
const searchText = ref('')
const showSubDeptRoles = ref(false)
const departmentTree = ref<DepartmentTree[]>([])
const selectedDepartment = ref<DepartmentInfo | null>(null)
const selectedRole = ref<RoleInfo | null>(null)
const roles = ref<RoleInfo[]>([])
const departmentRoleCounts = ref<Record<string, number>>({})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 弹窗
const dialogVisible = ref(false)
const permissionDialog = ref(false)
const detailDrawerVisible = ref(false)
const currentRoleData = ref<RoleInfo | undefined>(undefined)
const dialogType = ref<'add' | 'edit'>('add')

// 树组件
const treeRef = ref<InstanceType<typeof ElTree>>()
const treeProps = { children: 'children', label: 'name' }

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
    currentPage.value = 1
    loadRoleList()
  }
})

watch(treeFilterText, val => treeRef.value?.filter(val))

const filterNode = (value: string, data: any) => !value || data.name.includes(value)

const handleNodeClick = (data: DepartmentInfo) => {
  selectedDepartment.value = data
  selectedRole.value = null
  detailDrawerVisible.value = false
  currentPage.value = 1
  loadRoleList()
}

const handleScopeChange = () => {
  currentPage.value = 1
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
  try {
    loading.value = true
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

    const res = await fetchRoleList({
      page: currentPage.value,
      pageSize: pageSize.value,
      department_ids: deptIds.join(','),
      name: searchText.value || undefined
    })

    if (res.success && res.data) {
      roles.value = res.data.result || []
      total.value = res.data.total || 0
      if (!showSubDeptRoles.value) {
        departmentRoleCounts.value[selectedDepartment.value.id] = total.value
      }
    }
  } catch (e) {
    console.error('加载角色失败:', e)
    ElMessage.error('加载角色数据失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadRoleList()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadRoleList()
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

const refreshData = () => loadRoleList()

onMounted(() => loadDepartmentTree())
</script>

<style lang="scss" scoped>
// 关键：让 ElContainer 填满 art-full-height
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
    min-height: 0; // 关键：允许 flex 子元素收缩
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
  display: flex;
  flex-direction: column;
  background: var(--el-fill-color-lighter);
  overflow: hidden;
}

.toolbar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.art-table-card {
  flex: 1;
  margin: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }
}

.role-table {
  flex: 1;
  min-height: 0;
}

.code-tag {
  font-size: 12px;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.pagination-wrapper {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.total-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
