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
          <!-- 工具栏 -->
          <div class="toolbar">
            <div class="toolbar-left">
              <ElBreadcrumb separator="/">
                <ElBreadcrumbItem>{{ selectedDepartment.name }}</ElBreadcrumbItem>
                <ElBreadcrumbItem v-if="!showSubDeptUsers">
                  {{ $t('user.currentOnly', '仅当前部门') }}
                </ElBreadcrumbItem>
                <ElBreadcrumbItem v-else>
                  {{ $t('user.includeChild', '含下属部门') }}
                </ElBreadcrumbItem>
              </ElBreadcrumb>
              <ElSwitch
                v-model="showSubDeptUsers"
                :active-text="$t('user.includeSub', '含下属')"
                size="small"
                @change="handleScopeChange"
              />
            </div>
            <div class="toolbar-right">
              <ElInput
                v-model="searchText"
                :placeholder="$t('user.search', '搜索用户')"
                clearable
                size="small"
                style="width: 180px"
                :prefix-icon="Search"
              />
              <ElButton
                v-auth="'user:btn:addUser'"
                type="primary"
                size="small"
                round
                :icon="Plus"
                @click="showDialog('add')"
              >
                {{ $t('user.addUser', '新增用户') }}
              </ElButton>
            </div>
          </div>

          <!-- 表格卡片 -->
          <ElCard class="art-table-card" shadow="never">
            <ArtTableHeader :loading="loading" @refresh="refreshData" />
            
            <ElTable
              v-loading="loading"
              :data="data"
              border
              stripe
              highlight-current-row
              class="user-table"
              @row-click="selectUser"
            >
              <ElTableColumn type="index" width="60" align="center" :label="$t('table.index', '#')" />
              <ElTableColumn prop="avatar" :label="$t('user.avatar', '头像')" width="80" align="center">
                <template #default="{ row }">
                  <ElAvatar :size="36" :src="getAvatarUrl(row.avatar)">
                    <ElIcon><User /></ElIcon>
                  </ElAvatar>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="username" :label="$t('user.username', '用户名')" min-width="120" show-overflow-tooltip />
              <ElTableColumn prop="nickname" :label="$t('user.nickname', '昵称')" min-width="120" show-overflow-tooltip />
              <ElTableColumn prop="department_name" :label="$t('common.dept', '部门')" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.department_name || '-' }}
                </template>
              </ElTableColumn>
              <ElTableColumn prop="user_type" :label="$t('user.userType', '身份')" width="100" align="center">
                <template #default="{ row }">
                  <ElTag :type="getUserTypeTagType(row.user_type)" size="small">
                    {{ getUserTypeName(row.user_type) }}
                  </ElTag>
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
                  <div class="action-buttons">
                    <ElButton
                      v-auth="'user:btn:updateUser'"
                      type="primary"
                      size="small"
                      link
                      @click.stop="showDialog('edit', row)"
                    >
                      {{ $t('buttons.edit', '编辑') }}
                    </ElButton>
                    <ElDivider direction="vertical" />
                    <ElDropdown @command="handleCommand" trigger="click">
                      <ElButton type="info" size="small" link>
                        {{ $t('common.more', '更多') }}
                        <ElIcon class="el-icon--right"><ArrowDown /></ElIcon>
                      </ElButton>
                      <template #dropdown>
                        <ElDropdownMenu>
                          <ElDropdownItem
                            v-if="hasPermission('user:btn:addRole')"
                            :command="{ action: 'assignRoles', user: row }"
                          >
                            <ElIcon class="mr-1"><UserFilled /></ElIcon>
                            {{ $t('user.assignRoles', '分配角色') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="hasPermission('user:btn:permissionList')"
                            :command="{ action: 'viewPermissions', user: row }"
                          >
                            <ElIcon class="mr-1"><Lock /></ElIcon>
                            {{ $t('user.viewPermissions', '查看权限') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="hasPermission('user:btn:reset_password')"
                            :command="{ action: 'resetPassword', user: row }"
                            divided
                          >
                            <ElIcon class="mr-1"><Key /></ElIcon>
                            {{ $t('user.resetPassword', '重置密码') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="hasPermission('user:btn:deleteUser')"
                            :command="{ action: 'delete', user: row }"
                          >
                            <span class="text-red-500">
                              <ElIcon class="mr-1"><Delete /></ElIcon>
                              {{ $t('buttons.delete', '删除') }}
                            </span>
                          </ElDropdownItem>
                        </ElDropdownMenu>
                      </template>
                    </ElDropdown>
                  </div>
                </template>
              </ElTableColumn>
            </ElTable>

            <!-- 分页 -->
            <div class="pagination-wrapper">
              <span class="total-text">共 {{ pagination.total }} 条</span>
              <ElPagination
                v-model:current-page="pagination.current"
                v-model:page-size="pagination.size"
                :page-sizes="[10, 20, 50, 100]"
                :total="pagination.total"
                layout="sizes, prev, pager, next, jumper"
                small
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
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
import { ref, watch, onMounted } from 'vue'
import { dayjs, ElMessage, ElMessageBox, ElTree } from 'element-plus'
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

// 使用 useTable 管理用户列表
const {
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
    paginationKey: { current: 'page', size: 'pageSize' }
  },
  performance: {
    enableCache: true,
    cacheTime: 5 * 60 * 1000,
    debounceTime: 300
  }
})

// 抽屉相关
const dialogVisible = ref(false)
const roleDrawerVisible = ref(false)
const permissionDrawerVisible = ref(false)
const resetPasswordDrawerVisible = ref(false)
const currentUserData = ref<UserInfo | undefined>(undefined)
const dialogType = ref<'add' | 'edit'>('add')

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
 * 获取用户身份标签类型（颜色）
 */
const getUserTypeTagType = (userType: number) => {
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

.user-table {
  flex: 1;
  min-height: 0;
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

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  
  :deep(.el-divider--vertical) {
    margin: 0 4px;
    height: 14px;
  }
}
</style>
