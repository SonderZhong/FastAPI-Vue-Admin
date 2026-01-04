<template>
  <ElDrawer
    v-model="drawerVisible"
    :title="$t('user.viewPermissions', '查看权限') + (props.userData ? ` - ${props.userData.nickname}` : '')"
    direction="rtl"
    size="45%"
    :before-close="handleClose"
    destroy-on-close
    class="permission-drawer"
  >
    <div v-if="props.userData" class="h-full flex flex-col">
      <!-- 用户信息卡片 -->
      <div class="user-info-card">
        <ElAvatar :size="48" :src="getAvatarUrl(props.userData.avatar)">
          <ElIcon><User /></ElIcon>
        </ElAvatar>
        <div class="user-info">
          <div class="user-name">{{ props.userData.nickname }}</div>
          <div class="user-meta">@{{ props.userData.username }} · {{ props.userData.department_name || '无部门' }}</div>
        </div>
        <ElTag :type="props.userData.status === 1 ? 'success' : 'danger'" size="small" round>
          {{ props.userData.status === 1 ? $t('common.enabled', '启用') : $t('common.disabled', '禁用') }}
        </ElTag>
      </div>

      <!-- 权限统计 -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value text-green-600">{{ totalPermissionsCount }}</span>
          <span class="stat-label">{{ $t('user.totalPermissions', '总权限') }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value text-blue-600">{{ menuPermissionsCount }}</span>
          <span class="stat-label">{{ $t('common.menu', '菜单') }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value text-orange-600">{{ buttonPermissionsCount }}</span>
          <span class="stat-label">{{ $t('common.button', '按钮') }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value text-purple-600">{{ apiPermissionsCount }}</span>
          <span class="stat-label">API</span>
        </div>
      </div>

      <!-- Tab 切换 -->
      <ElTabs v-model="activeTab" class="permission-tabs">
        <!-- 菜单/按钮权限 Tab -->
        <ElTabPane name="menu" :label="$t('role.menuPermission', '菜单/按钮权限')">
          <div class="tab-content">
            <!-- 操作按钮 -->
            <div class="action-bar">
              <ElButton size="small" round @click="expandAllMenu">
                <ElIcon class="mr-1"><ArrowDown /></ElIcon>
                {{ $t('buttons.expandAll', '展开') }}
              </ElButton>
              <ElButton size="small" round @click="collapseAllMenu">
                <ElIcon class="mr-1"><ArrowUp /></ElIcon>
                {{ $t('buttons.collapseAll', '收起') }}
              </ElButton>
            </div>

            <!-- 菜单权限树 -->
            <div class="tree-container">
              <ElScrollbar>
                <ElTree
                  ref="menuTreeRef"
                  v-loading="loading"
                  :data="menuPermissionTree"
                  node-key="permission_id"
                  :default-expand-all="false"
                  :props="treeProps"
                >
                  <template #default="{ data }">
                    <div class="tree-node">
                      <ElIcon :class="getIconClass(data.permission_type)">
                        <Folder v-if="data.permission_type === 0" />
                        <Operation v-else-if="data.permission_type === 1" />
                        <Link v-else />
                      </ElIcon>
                      <span class="node-label">{{ getTranslatedPermissionName(data.permission_name) }}</span>
                      <ElTag v-if="data.permission_type === 1" type="warning" size="small" round>
                        {{ $t('common.button', '按钮') }}
                      </ElTag>
                      <ElTag v-else-if="data.permission_type === 2" type="success" size="small" round>
                        API
                      </ElTag>
                      <template v-if="data.permission_type === 2 && data.api_path">
                        <ElTag :type="getMethodTagType(data.api_method)" size="small" round class="ml-1">
                          {{ data.api_method || 'GET' }}
                        </ElTag>
                        <code class="api-path">{{ data.api_path }}</code>
                      </template>
                      <ElTag type="success" size="small" round class="ml-2">
                        {{ data.role_name }}
                      </ElTag>
                    </div>
                  </template>
                </ElTree>
                <div v-if="menuPermissionTree.length === 0 && !loading" class="empty-state">
                  <ElIcon :size="40" class="text-gray-300"><Folder /></ElIcon>
                  <p>{{ $t('user.noPermissions', '暂无菜单/按钮权限') }}</p>
                </div>
              </ElScrollbar>
            </div>
          </div>
        </ElTabPane>

        <!-- API 权限 Tab -->
        <ElTabPane name="api" :label="$t('role.publicApiPermission', '公共API权限')">
          <div class="tab-content">
            <!-- 操作按钮 -->
            <div class="action-bar">
              <ElButton size="small" round @click="expandAllApi">
                <ElIcon class="mr-1"><ArrowDown /></ElIcon>
                {{ $t('buttons.expandAll', '展开') }}
              </ElButton>
              <ElButton size="small" round @click="collapseAllApi">
                <ElIcon class="mr-1"><ArrowUp /></ElIcon>
                {{ $t('buttons.collapseAll', '收起') }}
              </ElButton>
            </div>

            <!-- API 权限树 -->
            <div class="tree-container">
              <ElScrollbar>
                <ElTree
                  ref="apiTreeRef"
                  v-loading="loading"
                  :data="apiPermissionTree"
                  node-key="permission_id"
                  :default-expand-all="false"
                  :props="treeProps"
                >
                  <template #default="{ data }">
                    <div class="tree-node">
                      <ElIcon class="text-green-500">
                        <Connection v-if="data.children?.length" />
                        <Link v-else />
                      </ElIcon>
                      <span class="node-label">{{ data.permission_name }}</span>
                      <template v-if="data.api_path">
                        <ElTag :type="getMethodTagType(data.api_method)" size="small" round class="ml-2">
                          {{ data.api_method || 'GET' }}
                        </ElTag>
                        <code class="api-path">{{ data.api_path }}</code>
                      </template>
                      <ElTag type="success" size="small" round class="ml-2">
                        {{ data.role_name }}
                      </ElTag>
                    </div>
                  </template>
                </ElTree>
                <div v-if="apiPermissionTree.length === 0 && !loading" class="empty-state">
                  <ElIcon :size="40" class="text-gray-300"><Link /></ElIcon>
                  <p>{{ $t('user.noPermissions', '暂无API权限') }}</p>
                </div>
              </ElScrollbar>
            </div>
          </div>
        </ElTabPane>
      </ElTabs>
    </div>

    <!-- 空状态 -->
    <div v-else class="flex items-center justify-center h-full">
      <div class="text-center text-gray-500">
        <ElIcon class="text-4xl mb-4"><User /></ElIcon>
        <p>{{ $t('user.noUserSelected', '请选择用户') }}</p>
      </div>
    </div>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElTree } from 'element-plus'
import { ArrowDown, ArrowUp, Folder, Operation, Connection, Link, User } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { fetchUserPermissionList, type UserInfo, type UserPermissionInfo } from '@/api/system/user'
import { getAvatarUrl } from '@/utils'

interface Props {
  visible: boolean
  userData: UserInfo | null
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'close'): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  userData: null
})

const emit = defineEmits<Emits>()
const { t: $t } = useI18n()

// 响应式数据
const loading = ref(false)
const activeTab = ref('menu')
const permissions = ref<UserPermissionInfo[]>([])

// 树组件引用
const menuTreeRef = ref<InstanceType<typeof ElTree>>()
const apiTreeRef = ref<InstanceType<typeof ElTree>>()

const treeProps = {
  children: 'children',
  label: 'permission_name'
}

// 抽屉显示状态
const drawerVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 权限名称国际化映射
const permissionNameMap = computed(() => ({
  系统管理: $t('menus.system.title', '系统管理'),
  用户管理: $t('menus.system.user', '用户管理'),
  角色管理: $t('menus.system.role', '角色管理'),
  部门管理: $t('menus.system.department', '部门管理'),
  菜单管理: $t('menus.system.menu', '菜单管理'),
  权限管理: $t('menus.system.permission', '权限管理'),
  配置管理: $t('menus.system.config', '配置管理'),
  新增: $t('buttons.add', '新增'),
  编辑: $t('buttons.edit', '编辑'),
  删除: $t('buttons.delete', '删除'),
  查看: $t('buttons.info', '查看详情'),
  详情: $t('buttons.info', '查看详情'),
  导出: $t('buttons.export', '导出'),
  导入: $t('buttons.import', '导入'),
  重置密码: $t('buttons.resetPassword', '重置密码'),
  分配权限: $t('buttons.assignPermission', '分配权限'),
  分配角色: $t('user.assignRoles', '分配角色'),
  查看权限: $t('user.viewPermissions', '查看权限'),
  仪表板: $t('menus.dashboard.title', '仪表板'),
  控制台: $t('menus.dashboard.console', '控制台'),
  工作台: $t('menus.dashboard.workbench', '工作台')
}))

// 构建树形权限结构
const buildPermissionTree = (perms: UserPermissionInfo[]): UserPermissionInfo[] => {
  const permissionMap = new Map<string, UserPermissionInfo>()
  const rootPermissions: UserPermissionInfo[] = []

  perms.forEach((permission) => {
    permissionMap.set(permission.permission_id, { ...permission, children: [] })
  })

  perms.forEach((permission) => {
    const currentPermission = permissionMap.get(permission.permission_id)!
    if (permission.parent_id && permissionMap.has(permission.parent_id)) {
      const parentPermission = permissionMap.get(permission.parent_id)!
      if (!parentPermission.children) {
        parentPermission.children = []
      }
      parentPermission.children.push(currentPermission)
    } else {
      rootPermissions.push(currentPermission)
    }
  })

  return rootPermissions
}

// 菜单/按钮权限树（包含有父级的API权限）
const menuPermissionTree = computed(() => {
  const menuPerms = permissions.value.filter(p => 
    p.permission_type === 0 || 
    p.permission_type === 1 || 
    (p.permission_type === 2 && p.parent_id) // 包含有父级的API权限
  )
  return buildPermissionTree(menuPerms)
})

// API 权限树（只包含独立的API权限，没有父级的）
const apiPermissionTree = computed(() => {
  const apiPerms = permissions.value.filter(p => p.permission_type === 2 && !p.parent_id)
  return buildPermissionTree(apiPerms)
})

// 统计数量
const totalPermissionsCount = computed(() => permissions.value.length)
const menuPermissionsCount = computed(() => permissions.value.filter(p => p.permission_type === 0).length)
const buttonPermissionsCount = computed(() => permissions.value.filter(p => p.permission_type === 1).length)
const apiPermissionsCount = computed(() => permissions.value.filter(p => p.permission_type === 2).length)

const translateTitle = (title: string | undefined) => {
  if (!title) return ''
  if (title.includes('.')) {
    try {
      return $t(title, title)
    } catch {
      return title
    }
  }
  return title
}

const getTranslatedPermissionName = (permissionName: string): string => {
  const translated = translateTitle(permissionName)
  if (translated && translated !== permissionName) {
    return translated
  }
  return (permissionNameMap.value as Record<string, string>)[permissionName] || permissionName
}

const getMethodTagType = (method?: string): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  const methodMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'warning'
  }
  return methodMap[method || 'GET'] || 'info'
}

const getIconClass = (permissionType?: number): string => {
  switch (permissionType) {
    case 0: return 'text-blue-500'
    case 1: return 'text-orange-500'
    case 2: return 'text-green-500'
    default: return 'text-gray-500'
  }
}

// 菜单树操作
const getAllMenuKeys = (nodes: UserPermissionInfo[]): string[] => {
  let keys: string[] = []
  nodes.forEach((node) => {
    if (node.permission_id) keys.push(node.permission_id)
    if (node.children?.length) keys = keys.concat(getAllMenuKeys(node.children))
  })
  return keys
}

const expandAllMenu = () => {
  const tree = menuTreeRef.value
  if (!tree) return
  getAllMenuKeys(menuPermissionTree.value).forEach((key) => tree.store.nodesMap[key]?.expand())
}

const collapseAllMenu = () => {
  const tree = menuTreeRef.value
  if (!tree) return
  getAllMenuKeys(menuPermissionTree.value).forEach((key) => tree.store.nodesMap[key]?.collapse())
}

// API 树操作
const getAllApiKeys = (nodes: UserPermissionInfo[]): string[] => {
  let keys: string[] = []
  nodes.forEach((node) => {
    if (node.permission_id) keys.push(node.permission_id)
    if (node.children?.length) keys = keys.concat(getAllApiKeys(node.children))
  })
  return keys
}

const expandAllApi = () => {
  const tree = apiTreeRef.value
  if (!tree) return
  getAllApiKeys(apiPermissionTree.value).forEach((key) => tree.store.nodesMap[key]?.expand())
}

const collapseAllApi = () => {
  const tree = apiTreeRef.value
  if (!tree) return
  getAllApiKeys(apiPermissionTree.value).forEach((key) => tree.store.nodesMap[key]?.collapse())
}

const fetchPermissions = async () => {
  if (!props.userData?.id) return

  loading.value = true
  try {
    const response = await fetchUserPermissionList(props.userData.id)
    permissions.value = response.data.result || []
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error($t('common.loadFailed', '加载失败'))
    permissions.value = []
  } finally {
    loading.value = false
  }
}

const handleClose = (done?: () => void) => {
  permissions.value = []
  activeTab.value = 'menu'
  drawerVisible.value = false
  emit('close')
  if (done) {
    done()
  }
}

watch(
  () => props.visible,
  (visible) => {
    drawerVisible.value = visible
    if (visible && props.userData) {
      activeTab.value = 'menu'
      fetchPermissions()
    } else if (!visible) {
      permissions.value = []
    }
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.permission-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
  
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  :deep(.el-drawer__body) {
    padding: 0;
    display: flex;
    flex-direction: column;
  }
}

.user-info-card {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.user-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.stats-bar {
  flex-shrink: 0;
  display: flex;
  padding: 12px 20px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.stat-item {
  flex: 1;
  text-align: center;
  
  &:not(:last-child) {
    border-right: 1px solid var(--el-border-color-lighter);
  }
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: block;
  margin-top: 2px;
}

.permission-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  
  :deep(.el-tabs__header) {
    flex-shrink: 0;
    margin: 0;
    padding: 0 20px;
    background: var(--el-fill-color-lighter);
  }
  
  :deep(.el-tabs__content) {
    flex: 1;
    min-height: 0;
    padding: 0;
  }
  
  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.tab-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.action-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tree-container {
  flex: 1;
  min-height: 0;
  padding: 12px 20px;
  
  :deep(.el-scrollbar) {
    height: 100%;
  }
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  
  .node-label {
    flex-shrink: 0;
  }
  
  .api-path {
    font-size: 11px;
    color: var(--el-text-color-secondary);
    background: var(--el-fill-color-light);
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 4px;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--el-text-color-secondary);
  
  p {
    margin-top: 12px;
  }
}
</style>
