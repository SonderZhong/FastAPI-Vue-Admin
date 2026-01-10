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
                      v-if="getDepartmentUserCount(data.id) > 0"
                      :value="getDepartmentUserCount(data.id)"
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
                <span class="search-label">{{ $t('user.scope', '范围') }}</span>
                <ElSwitch
                  v-model="showSubDeptUsers"
                  :active-text="$t('user.includeSub', '含下属')"
                  :inactive-text="$t('user.currentOnly', '仅当前')"
                  @change="handleScopeChange"
                />
              </div>
              <div class="search-item">
                <span class="search-label">{{ $t('user.username', '用户名') }}</span>
                <ElInput
                  v-model="searchText"
                  :placeholder="$t('user.search', '搜索用户')"
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
                  v-auth="'user:btn:addUser'"
                  type="primary"
                  :icon="Plus"
                  @click="showDialog('add')"
                >
                  {{ $t('user.addUser', '新增用户') }}
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
              @row-click="selectUser"
              @pagination:size-change="handleSizeChange"
              @pagination:current-change="handleCurrentChange"
            />
          </ElCard>
        </template>

        <!-- 未选择部门的提示 -->
        <div v-else class="empty-state">
          <ElEmpty :description="$t('user.selectDept', '请选择左侧部门查看用户')">
            <template #image>
              <ElIcon :size="60" class="text-gray-300"><OfficeBuilding /></ElIcon>
            </template>
          </ElEmpty>
        </div>
      </ElMain>
    </ElContainer>

    <!-- 用户编辑抽屉 -->
    <UserEditDrawer
      v-model="dialogVisible"
      :dialog-type="dialogType"
      :user-data="currentUserData"
      :department-id="selectedDepartment?.id"
      :department-name="selectedDepartment?.name"
      @success="refreshData"
    />

    <!-- 角色分配抽屉 -->
    <UserRoleDrawer
      v-model="roleDrawerVisible"
      :user-data="currentUserData"
      @success="refreshData"
    />

    <!-- 权限查看抽屉 -->
    <UserPermissionDrawer
      v-model:visible="permissionDrawerVisible"
      :user-data="currentUserData || null"
    />

    <!-- 重置密码抽屉 -->
    <UserResetPasswordDrawer
      v-model="resetPasswordDrawerVisible"
      :user-data="currentUserData || null"
      @success="handleResetPasswordSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, h, watch, onMounted } from 'vue'
import { dayjs, ElMessage, ElMessageBox, ElTree, ElTag, ElButton, ElDropdown, ElDropdownMenu, ElDropdownItem, ElIcon, ElAvatar } from 'element-plus'
import { Search, OfficeBuilding, User, ArrowDown, Plus, UserFilled, Lock, Key, Delete } from '@element-plus/icons-vue'
import { fetchDepartmentTree } from '@/api/system/department'
import type { DepartmentTree, DepartmentInfo } from '@/typings/department'
import {
  fetchUserList,
  deleteUser as apiDeleteUser,
  type UserInfo,
  type UserQueryParams
} from '@/api/system/user'
import { useI18n } from 'vue-i18n'
import { useTable } from '@/composables/useTable'
import { usePermission } from '@/composables/usePermission'
import ArtTable from '@/components/core/tables/art-table/index.vue'
import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
import UserEditDrawer from './modules/user-edit-drawer.vue'
import UserRoleDrawer from './modules/user-role-drawer.vue'
import UserResetPasswordDrawer from './modules/user-reset-password-drawer.vue'
import UserPermissionDrawer from './modules/user-permission-drawer.vue'
import { getUserTypeName, UserType } from '@/utils/permission'
import { getAvatarUrl } from '@/utils'

defineOptions({ name: 'User' })

const { t: $t } = useI18n()
const { hasPermission } = usePermission()

// 响应式数据
const treeFilterText = ref('')
const searchText = ref('')
const showSubDeptUsers = ref(true)
const departmentTree = ref<DepartmentTree[]>([])
const selectedDepartment = ref<DepartmentInfo | null>(null)
const selectedUser = ref<UserInfo | null>(null)
const departmentUserCounts = ref<Record<string, number>>({})

/**
 * 获取用户身份标签类型（颜色）
 */
const getUserTypeTagType = (userType: number): 'danger' | 'warning' | 'primary' | 'info' => {
  switch (userType) {
    case UserType.SUPER_ADMIN:
      return 'danger'
    case UserType.ADMIN:
      return 'warning'
    case UserType.DEPT_ADMIN:
      return 'primary'
    case UserType.NORMAL_USER:
    default:
      return 'info'
  }
}

// 使用 useTable 管理用户列表
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
} = useTable<typeof fetchUserList>({
  core: {
    apiFn: fetchUserList,
    apiParams: {} as UserQueryParams,
    immediate: false,
    paginationKey: { current: 'page', size: 'pageSize' },
    columnsFactory: () => [
      { type: 'index', width: 80, label: $t('table.column.index'), align: 'center' },
      {
        prop: 'avatar',
        label: $t('user.avatar', '头像'),
        width: 80,
        align: 'center',
        formatter: (row: UserInfo) => h(ElAvatar, { size: 36, src: getAvatarUrl(row.avatar) }, () => h(ElIcon, null, () => h(User)))
      },
      { prop: 'username', label: $t('user.username', '用户名'), align: 'center', showOverflowTooltip: true },
      { prop: 'nickname', label: $t('user.nickname', '昵称'), align: 'center', showOverflowTooltip: true },
      {
        prop: 'department_name',
        label: $t('common.dept', '部门'),
        align: 'center',
        showOverflowTooltip: true,
        formatter: (row: UserInfo) => row.department_name || '-'
      },
      {
        prop: 'user_type',
        label: $t('user.userType', '身份'),
        width: 120,
        align: 'center',
        formatter: (row: UserInfo) => h(ElTag, { type: getUserTypeTagType(row.user_type ?? UserType.NORMAL_USER), size: 'small' }, () => getUserTypeName(row.user_type ?? UserType.NORMAL_USER))
      },
      {
        prop: 'status',
        label: $t('common.status', '状态'),
        width: 80,
        align: 'center',
        formatter: (row: UserInfo) => h(ElTag, { type: row.status === 1 ? 'success' : 'danger', size: 'small' }, () => row.status === 1 ? $t('common.enable', '启用') : $t('common.disable', '禁用'))
      },
      {
        prop: 'created_at',
        label: $t('common.createTime', '创建时间'),
        width: 160,
        align: 'center',
        formatter: (row: UserInfo) => dayjs(row.created_at).format('YYYY-MM-DD HH:mm')
      },
      {
        prop: 'actions',
        label: $t('common.actions', '操作'),
        width: 180,
        align: 'center',
        fixed: 'right',
        formatter: (row: UserInfo) => {
          const buttons = []
          if (hasPermission('user:btn:updateUser')) {
            buttons.push(h(ElButton, { type: 'primary', size: 'small', onClick: () => showDialog('edit', row) }, () => $t('buttons.edit', '编辑')))
          }
          buttons.push(
            h(ElDropdown, { trigger: 'click', onCommand: handleCommand }, {
              default: () => h(ElButton, { type: 'info', size: 'small' }, () => [$t('common.more', '更多'), h(ElIcon, { class: 'el-icon--right' }, () => h(ArrowDown))]),
              dropdown: () => h(ElDropdownMenu, null, () => [
                hasPermission('user:btn:addRole') && h(ElDropdownItem, { command: { action: 'assignRoles', user: row } }, () => [h(ElIcon, { class: 'mr-1' }, () => h(UserFilled)), $t('user.assignRoles', '分配角色')]),
                hasPermission('user:btn:permissionList') && h(ElDropdownItem, { command: { action: 'viewPermissions', user: row } }, () => [h(ElIcon, { class: 'mr-1' }, () => h(Lock)), $t('user.viewPermissions', '查看权限')]),
                hasPermission('user:btn:reset_password') && h(ElDropdownItem, { command: { action: 'resetPassword', user: row }, divided: true }, () => [h(ElIcon, { class: 'mr-1' }, () => h(Key)), $t('user.resetPassword', '重置密码')]),
                hasPermission('user:btn:deleteUser') && h(ElDropdownItem, { command: { action: 'delete', user: row } }, () => h('span', { class: 'text-red-500' }, [h(ElIcon, { class: 'mr-1' }, () => h(Delete)), $t('buttons.delete', '删除')]))
              ].filter(Boolean))
            })
          )
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

// 树组件引用
const treeRef = ref<InstanceType<typeof ElTree>>()
const treeProps = { children: 'children', label: 'name' }

/**
 * 获取部门用户数量
 */
const getDepartmentUserCount = (departmentId: string): number => {
  return departmentUserCounts.value[departmentId] || 0
}

/**
 * 获取部门及其所有下级部门的ID列表
 */
const getAllSubDepartmentIds = (department: DepartmentTree): string[] => {
  const ids = [department.id]
  if (department.children && department.children.length > 0) {
    department.children.forEach((child: DepartmentTree) => {
      ids.push(...getAllSubDepartmentIds(child))
    })
  }
  return ids
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

// 抽屉相关
const dialogVisible = ref(false)
const roleDrawerVisible = ref(false)
const permissionDrawerVisible = ref(false)
const resetPasswordDrawerVisible = ref(false)
const currentUserData = ref<UserInfo | undefined>(undefined)
const dialogType = ref<'add' | 'edit'>('add')

// 监听搜索框过滤树
watch(treeFilterText, (val) => {
  treeRef.value?.filter(val)
})

// 监听搜索文本
watch(searchText, () => {
  if (selectedDepartment.value) {
    ;(searchParams as any).page = 1
    loadUserList()
  }
})

/**
 * 过滤树节点
 */
const filterNode = (value: string, data: any) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase())
}

/**
 * 处理部门节点点击
 */
const handleNodeClick = (data: DepartmentInfo) => {
  selectedDepartment.value = data
  selectedUser.value = null
  ;(searchParams as any).page = 1
  loadUserList()
}

/**
 * 处理范围切换
 */
const handleScopeChange = () => {
  ;(searchParams as any).page = 1
  loadUserList()
}

/**
 * 加载用户列表
 */
const loadUserList = async () => {
  if (!selectedDepartment.value) return

  let deptIds: string[]
  if (showSubDeptUsers.value) {
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
    username: searchText.value || undefined
  })

  getData()
}

/**
 * 选择用户
 */
const selectUser = (user: UserInfo) => {
  selectedUser.value = user
}

/**
 * 处理下拉菜单命令
 */
const handleCommand = (command: { action: string; user: UserInfo }) => {
  const { action, user } = command
  switch (action) {
    case 'assignRoles':
      showRoleDrawer(user)
      break
    case 'viewPermissions':
      showPermissionDrawer(user)
      break
    case 'resetPassword':
      showResetPasswordDrawer(user)
      break
    case 'delete':
      deleteUser(user)
      break
  }
}

/**
 * 显示用户编辑抽屉
 */
const showDialog = (type: 'add' | 'edit', userData?: UserInfo) => {
  dialogType.value = type
  currentUserData.value = userData
  dialogVisible.value = true
}

/**
 * 显示角色分配抽屉
 */
const showRoleDrawer = (userData: UserInfo) => {
  currentUserData.value = userData
  roleDrawerVisible.value = true
}

/**
 * 显示权限查看抽屉
 */
const showPermissionDrawer = (userData: UserInfo) => {
  currentUserData.value = userData
  permissionDrawerVisible.value = true
}

/**
 * 显示重置密码抽屉
 */
const showResetPasswordDrawer = (user: UserInfo) => {
  currentUserData.value = user
  resetPasswordDrawerVisible.value = true
}

/**
 * 删除用户
 */
const deleteUser = async (user: UserInfo) => {
  const confirm = await ElMessageBox.confirm(
    `确定删除用户【${user.nickname}】吗？`,
    '确认删除',
    { type: 'warning' }
  ).catch(() => false)
  if (!confirm) return

  try {
    await apiDeleteUser(user.id)
    ElMessage.success($t('common.deleteSuccess', '删除成功'))
    if (selectedUser.value?.id === user.id) {
      selectedUser.value = null
    }
    refreshData()
  } catch {
    ElMessage.error('删除失败')
  }
}

/**
 * 重置密码成功回调
 */
const handleResetPasswordSuccess = () => {
  refreshUpdate()
}

/**
 * 加载部门树
 */
const loadDepartmentTree = async () => {
  try {
    const response = await fetchDepartmentTree()
    if (response.success && response.data) {
      departmentTree.value = response.data.result || []
    }
  } catch (error) {
    console.error('加载部门数据失败:', error)
    ElMessage.error('加载部门数据失败')
  }
}

/**
 * 刷新数据
 */
const refreshData = () => {
  refreshUpdate()
}

// 页面初始化
onMounted(() => {
  loadDepartmentTree()
})
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

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
