<template>
  <div class="art-full-height">
    <ElContainer class="h-full">
      <!-- 左侧权限树 -->
      <ElAside width="300px" class="perm-aside">
        <ElCard shadow="never" class="h-full perm-card">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-medium">{{ $t('menus.system.permission') }}</span>
              <ElSpace>
                <ElButton round size="small" @click="expandAll">{{ $t('buttons.expandAll') }}</ElButton>
                <ElButton round size="small" @click="collapseAll">{{ $t('buttons.collapseAll') }}</ElButton>
              </ElSpace>
            </div>
          </template>
          
          <div class="perm-content">
            <ElInput
              v-model="searchText"
              :placeholder="$t('common.searchPlaceholder')"
              clearable
              size="small"
              :prefix-icon="Search"
              class="mb-3"
              @input="handleSearch"
            />
            <ElScrollbar class="perm-tree-wrapper">
              <ElTree
                ref="treeRef"
                :data="permissionTree"
                :props="treeProps"
                :filter-node-method="filterNode"
                :expand-on-click-node="false"
                :highlight-current="true"
                :indent="16"
                node-key="id"
                @node-click="handleNodeClick"
              >
                <template #default="{ data }">
                  <div class="tree-node">
                    <ElIcon class="flex-shrink-0" :size="14" :class="getTypeIconClass(data.menu_type)">
                      <Menu v-if="data.menu_type === 0" />
                      <Operation v-else-if="data.menu_type === 1" />
                      <Link v-else />
                    </ElIcon>
                    <span class="node-label" :title="translateTitle(data.title) || data.name">
                      {{ translateTitle(data.title) || data.name }}
                    </span>
                    <ElTag v-if="data.menu_type === 1" type="warning" size="small">{{ $t('common.button') }}</ElTag>
                    <ElTag v-else-if="data.menu_type === 2" type="success" size="small">API</ElTag>
                  </div>
                </template>
              </ElTree>
            </ElScrollbar>
          </div>
        </ElCard>
      </ElAside>

      <!-- 右侧主内容区 -->
      <ElMain class="main-content">
        <template v-if="selectedPermission">
          <!-- 工具栏 -->
          <div class="toolbar">
            <div class="toolbar-left">
              <ElBreadcrumb separator="/">
                <ElBreadcrumbItem>{{ translateTitle(selectedPermission.title) || selectedPermission.name }}</ElBreadcrumbItem>
                <ElBreadcrumbItem>
                  <ElTag :type="getTypeTagType(selectedPermission.menu_type)" size="small">
                    {{ getTypeName(selectedPermission.menu_type) }}
                  </ElTag>
                </ElBreadcrumbItem>
              </ElBreadcrumb>
            </div>
            <div class="toolbar-right">
              <template v-if="selectedPermission.menu_type === 0">
                <ElButton
                  v-auth="'permission:btn:add'"
                  round
                  type="primary"
                  size="small"
                  :icon="Plus"
                  @click="addSubMenu"
                >
                  {{ $t('buttons.addSubMenu') }}
                </ElButton>
                <ElButton
                  v-auth="'permission:btn:add'"
                  round
                  type="warning"
                  size="small"
                  :icon="Plus"
                  @click="showButtonDrawer('add')"
                >
                  {{ $t('common.button') }}
                </ElButton>
                <ElButton
                  v-auth="'permission:btn:add'"
                  round
                  type="success"
                  size="small"
                  :icon="Plus"
                  @click="showApiDrawer('add')"
                >
                  API
                </ElButton>
              </template>
              <ElButton
                v-auth="'permission:btn:update'"
                round
                type="primary"
                size="small"
                @click="showMenuDrawer('edit', selectedPermission)"
              >
                {{ $t('buttons.edit') }}
              </ElButton>
              <ElButton
                v-auth="'permission:btn:delete'"
                round
                type="danger"
                size="small"
                @click="deletePermission(selectedPermission)"
              >
                {{ $t('buttons.delete') }}
              </ElButton>
            </div>
          </div>

          <!-- 详情卡片 -->
          <ElCard class="detail-card" shadow="never">
            <ElTabs v-model="activeTab">
              <!-- 基本信息 -->
              <ElTabPane :label="$t('common.basicInfo')" name="info">
                <div class="info-section">
                  <ElDescriptions :column="2" border size="default">
                    <!-- 通用字段 -->
                    <ElDescriptionsItem :label="$t('permission.parentPermission')">
                      {{ getParentPermissionName(selectedPermission.parent_id) }}
                    </ElDescriptionsItem>
                    <ElDescriptionsItem :label="$t('permission.permissionType')">
                      <ElTag :type="getTypeTagType(selectedPermission.menu_type)" size="small">
                        {{ getTypeName(selectedPermission.menu_type) }}
                      </ElTag>
                    </ElDescriptionsItem>
                    
                    <!-- 菜单类型字段 -->
                    <template v-if="selectedPermission.menu_type === 0">
                      <ElDescriptionsItem :label="$t('permission.routeName')">
                        {{ selectedPermission.name || '-' }}
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.menuTitle')">
                        {{ translateTitle(selectedPermission.title) }}
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.routePath')" :span="2">
                        <code class="code-tag">{{ selectedPermission.path || '-' }}</code>
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.componentPath')" :span="2">
                        <code class="code-tag">{{ selectedPermission.component || '-' }}</code>
                      </ElDescriptionsItem>
                    </template>
                    
                    <!-- 按钮类型字段 -->
                    <template v-else-if="selectedPermission.menu_type === 1">
                      <ElDescriptionsItem :label="$t('permission.buttonName')">
                        {{ translateTitle(selectedPermission.authTitle) }}
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.permissionMark')">
                        <code class="code-tag">{{ selectedPermission.authMark || '-' }}</code>
                      </ElDescriptionsItem>
                    </template>
                    
                    <!-- API类型字段 -->
                    <template v-else-if="selectedPermission.menu_type === 2">
                      <ElDescriptionsItem :label="$t('permission.apiName')">
                        {{ selectedPermission.title || '-' }}
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.dataScope')">
                        <ElTag :type="getDataScopeTagType(selectedPermission.data_scope)" size="small">
                          {{ getDataScopeName(selectedPermission.data_scope) }}
                        </ElTag>
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.apiPath')" :span="2">
                        <code class="code-tag">{{ selectedPermission.api_path || '-' }}</code>
                      </ElDescriptionsItem>
                      <ElDescriptionsItem :label="$t('permission.requestMethod')" :span="2">
                        <template v-if="Array.isArray(selectedPermission.api_method)">
                          <ElTag 
                            v-for="method in selectedPermission.api_method" 
                            :key="method" 
                            :type="getMethodTagType(method)" 
                            size="small"
                            class="mr-1"
                          >
                            {{ method }}
                          </ElTag>
                        </template>
                        <ElTag v-else-if="selectedPermission.api_method" :type="getMethodTagType(selectedPermission.api_method)" size="small">
                          {{ selectedPermission.api_method }}
                        </ElTag>
                        <span v-else>-</span>
                      </ElDescriptionsItem>
                      <ElDescriptionsItem v-if="selectedPermission.remark" :label="$t('common.remark')" :span="2">
                        {{ selectedPermission.remark }}
                      </ElDescriptionsItem>
                    </template>
                    
                    <!-- 通用底部字段 -->
                    <ElDescriptionsItem :label="$t('permission.minUserType')">
                      <ElTag :type="getMinUserTypeTagType(selectedPermission.min_user_type)" size="small">
                        {{ getMinUserTypeName(selectedPermission.min_user_type) }}
                      </ElTag>
                    </ElDescriptionsItem>
                    <ElDescriptionsItem :label="$t('common.sort')">{{ selectedPermission.order ?? 999 }}</ElDescriptionsItem>
                    <ElDescriptionsItem :label="$t('common.createTime')">
                      {{ formatDate(selectedPermission.created_at) }}
                    </ElDescriptionsItem>
                    <ElDescriptionsItem :label="$t('common.updateTime')">
                      {{ formatDate(selectedPermission.updated_at) }}
                    </ElDescriptionsItem>
                  </ElDescriptions>
                </div>
              </ElTabPane>

              <!-- 按钮权限（仅菜单类型显示） -->
              <ElTabPane v-if="selectedPermission.menu_type === 0" :label="$t('common.buttonPermissions')" name="buttons">
                <div class="tab-toolbar">
                  <span class="tab-title">{{ $t('common.buttonPermissions') }} ({{ buttonPermissions.length }})</span>
                  <ElButton round type="warning" size="small" :icon="Plus" @click="showButtonDrawer('add')">
                    {{ $t('buttons.addButton') }}
                  </ElButton>
                </div>
                <ElTable :data="buttonPermissions" border size="small">
                  <ElTableColumn prop="authTitle" :label="$t('common.buttonName')" min-width="120">
                    <template #default="{ row }">{{ translateTitle(row.authTitle) }}</template>
                  </ElTableColumn>
                  <ElTableColumn prop="authMark" :label="$t('permission.permissionMark')" min-width="150">
                    <template #default="{ row }">
                      <code class="code-tag">{{ row.authMark }}</code>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn prop="order" :label="$t('common.sort')" width="80" align="center" />
                  <ElTableColumn :label="$t('common.actions')" width="120" align="center">
                    <template #default="{ row }">
                      <ElButton type="primary" size="small" link @click="showButtonDrawer('edit', row)">{{ $t('buttons.edit') }}</ElButton>
                      <ElButton type="danger" size="small" link @click="deleteButton(row)">{{ $t('buttons.delete') }}</ElButton>
                    </template>
                  </ElTableColumn>
                </ElTable>
              </ElTabPane>

              <!-- API权限（仅菜单类型显示） -->
              <ElTabPane v-if="selectedPermission.menu_type === 0" :label="$t('role.apiPermission')" name="apis">
                <div class="tab-toolbar">
                  <span class="tab-title">{{ $t('role.apiPermission') }} ({{ apiPermissions.length }})</span>
                  <ElButton round type="success" size="small" :icon="Plus" @click="showApiDrawer('add')">
                    {{ $t('permission.addApiPermission') }}
                  </ElButton>
                </div>
                <ElTable :data="apiPermissions" border size="small">
                  <ElTableColumn prop="title" :label="$t('common.displayName')" min-width="120" />
                  <ElTableColumn prop="api_path" :label="$t('permission.apiPath')" min-width="200">
                    <template #default="{ row }">
                      <code class="code-tag">{{ row.api_path }}</code>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn prop="api_method" :label="$t('permission.requestMethod')" min-width="150" align="center">
                    <template #default="{ row }">
                      <template v-if="Array.isArray(row.api_method)">
                        <ElTag 
                          v-for="method in row.api_method" 
                          :key="method" 
                          :type="getMethodTagType(method)" 
                          size="small"
                          class="mr-1"
                        >
                          {{ method }}
                        </ElTag>
                      </template>
                      <ElTag v-else :type="getMethodTagType(row.api_method)" size="small">{{ row.api_method }}</ElTag>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn prop="data_scope" :label="$t('permission.dataScope')" width="120" align="center">
                    <template #default="{ row }">
                      <ElTag :type="getDataScopeTagType(row.data_scope)" size="small">
                        {{ getDataScopeName(row.data_scope) }}
                      </ElTag>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="$t('common.actions')" width="120" align="center">
                    <template #default="{ row }">
                      <ElButton type="primary" size="small" link @click="showApiDrawer('edit', row)">{{ $t('buttons.edit') }}</ElButton>
                      <ElButton type="danger" size="small" link @click="deleteApi(row)">{{ $t('buttons.delete') }}</ElButton>
                    </template>
                  </ElTableColumn>
                </ElTable>
              </ElTabPane>
            </ElTabs>
          </ElCard>
        </template>

        <!-- 未选择权限的提示 -->
        <div v-else class="empty-state">
          <ElEmpty :description="$t('common.selectPermissionToView')">
            <template #image>
              <ElIcon :size="60" class="text-gray-300"><Menu /></ElIcon>
            </template>
            <ElButton round type="primary" :icon="Plus" @click="showMenuDrawer('add')">
              {{ $t('permission.addRootMenu') }}
            </ElButton>
          </ElEmpty>
        </div>
      </ElMain>
    </ElContainer>

    <!-- 菜单权限抽屉 -->
    <PermissionDrawer
      v-model="menuDrawerVisible"
      :dialog-type="menuDrawerType"
      :permission-data="currentMenuData"
      @success="handleMenuSuccess"
    />

    <!-- 按钮权限抽屉 -->
    <ButtonPermissionDrawer
      v-model="buttonDrawerVisible"
      :dialog-type="buttonDrawerType"
      :permission-data="currentButtonData"
      :parent-id="selectedPermission?.id"
      @success="handleButtonSuccess"
    />

    <!-- API权限抽屉 -->
    <ApiPermissionDrawer
      v-model="apiDrawerVisible"
      :dialog-type="apiDrawerType"
      :permission-data="currentApiData"
      :parent-id="selectedPermission?.id"
      @success="handleApiSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElTree } from 'element-plus'
import { Search, Menu, Operation, Link, Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import {
  fetchPermissionTree,
  fetchPermissionList,
  fetchMenuButtons,
  deletePermission as deletePermissionApi,
  deleteButtonPermission as deleteButtonPermissionApi,
  deleteApiPermission as deleteApiPermissionApi,
  type PermissionInfo
} from '@/api/system/permission'
import { getUserTypeName, UserType } from '@/utils/permission'
import PermissionDrawer from './modules/permission-drawer.vue'
import ButtonPermissionDrawer from './modules/button-permission-drawer.vue'
import ApiPermissionDrawer from './modules/api-permission-drawer.vue'

defineOptions({ name: 'Permission' })

const { t } = useI18n()

// 响应式数据
const searchText = ref('')
const permissionTree = ref<PermissionInfo[]>([])
const selectedPermission = ref<PermissionInfo | null>(null)
const buttonPermissions = ref<PermissionInfo[]>([])
const apiPermissions = ref<PermissionInfo[]>([])
const activeTab = ref('info')

// 树组件
const treeRef = ref<InstanceType<typeof ElTree>>()
const treeProps = { children: 'children', label: 'title' }

// 抽屉状态
const menuDrawerVisible = ref(false)
const menuDrawerType = ref<'add' | 'edit'>('add')
const currentMenuData = ref<Partial<PermissionInfo>>({})

const buttonDrawerVisible = ref(false)
const buttonDrawerType = ref<'add' | 'edit'>('add')
const currentButtonData = ref<Partial<PermissionInfo>>({})

const apiDrawerVisible = ref(false)
const apiDrawerType = ref<'add' | 'edit'>('add')
const currentApiData = ref<Partial<PermissionInfo>>({})

// 翻译标题
const translateTitle = (title: string | undefined) => {
  if (!title) return ''
  if (title.includes('.')) {
    try {
      return t(title, title)
    } catch {
      return title
    }
  }
  return title
}

// 格式化日期
const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 获取类型图标样式
const getTypeIconClass = (menuType: number) => {
  switch (menuType) {
    case 0: return 'text-blue-500'
    case 1: return 'text-orange-500'
    case 2: return 'text-green-500'
    default: return 'text-gray-500'
  }
}

// 获取类型名称
const getTypeName = (menuType: number) => {
  switch (menuType) {
    case 0: return t('common.menu')
    case 1: return t('common.button')
    case 2: return 'API'
    default: return t('common.unknown')
  }
}

// 获取类型标签样式
const getTypeTagType = (menuType: number) => {
  switch (menuType) {
    case 0: return 'primary'
    case 1: return 'warning'
    case 2: return 'success'
    default: return 'info'
  }
}

// 获取HTTP方法标签样式
const getMethodTagType = (method: string | undefined) => {
  switch (method?.toUpperCase()) {
    case 'GET': return 'success'
    case 'POST': return 'primary'
    case 'PUT': return 'warning'
    case 'DELETE': return 'danger'
    case 'PATCH': return 'info'
    default: return 'info'
  }
}

// 获取最低用户身份名称
const getMinUserTypeName = (minUserType: number | undefined) => {
  if (minUserType === undefined || minUserType === null) return t('permission.allUsers')
  return getUserTypeName(minUserType) + t('permission.andAbove')
}

// 获取最低用户身份标签类型
const getMinUserTypeTagType = (minUserType: number | undefined) => {
  if (minUserType === undefined || minUserType === null) return 'info'
  switch (minUserType) {
    case UserType.SUPER_ADMIN: return 'danger'
    case UserType.ADMIN: return 'warning'
    case UserType.DEPT_ADMIN: return 'primary'
    default: return 'info'
  }
}

// 获取数据权限名称
const getDataScopeName = (dataScope: number | undefined) => {
  switch (dataScope) {
    case 1: return t('permission.dataScopeAll')
    case 2: return t('permission.dataScopeDeptAndChild')
    case 3: return t('permission.dataScopeDeptOnly')
    case 4: return t('permission.dataScopeSelfOnly')
    default: return t('permission.dataScopeSelfOnly')
  }
}

// 获取数据权限标签类型
const getDataScopeTagType = (dataScope: number | undefined) => {
  switch (dataScope) {
    case 1: return 'danger'
    case 2: return 'warning'
    case 3: return 'primary'
    case 4: return 'info'
    default: return 'info'
  }
}

// 获取上级权限名称
const getParentPermissionName = (parentId: string | undefined) => {
  if (!parentId) return t('permission.rootPermission')
  
  // 递归查找权限
  const findPermission = (nodes: PermissionInfo[], id: string): PermissionInfo | null => {
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children?.length) {
        const found = findPermission(node.children, id)
        if (found) return found
      }
    }
    return null
  }
  
  const parent = findPermission(permissionTree.value, parentId)
  if (parent) {
    return translateTitle(parent.title) || parent.name || parentId
  }
  return parentId
}

// 展开所有节点
const expandAll = () => {
  const tree = treeRef.value
  if (tree) {
    const getAllKeys = (nodes: PermissionInfo[]): string[] => {
      let keys: string[] = []
      nodes.forEach(node => {
        if (node.id) keys.push(node.id)
        if (node.children?.length) keys = keys.concat(getAllKeys(node.children))
      })
      return keys
    }
    getAllKeys(permissionTree.value).forEach(key => tree.store.nodesMap[key]?.expand())
  }
}

// 收起所有节点
const collapseAll = () => {
  const tree = treeRef.value
  if (tree) {
    const getAllKeys = (nodes: PermissionInfo[]): string[] => {
      let keys: string[] = []
      nodes.forEach(node => {
        if (node.id) keys.push(node.id)
        if (node.children?.length) keys = keys.concat(getAllKeys(node.children))
      })
      return keys
    }
    getAllKeys(permissionTree.value).forEach(key => tree.store.nodesMap[key]?.collapse())
  }
}

// 过滤节点
const filterNode = (value: string, data: any) => {
  if (!value) return true
  const title = translateTitle(data.title) || data.name || ''
  const name = data.name || ''
  return title.toLowerCase().includes(value.toLowerCase()) || name.toLowerCase().includes(value.toLowerCase())
}

// 搜索处理
const handleSearch = (value: string) => {
  treeRef.value?.filter(value)
}

// 节点点击
const handleNodeClick = (data: PermissionInfo) => {
  selectedPermission.value = data
  activeTab.value = 'info'
  if (data.menu_type === 0 && data.id) {
    loadButtonPermissions(data.id)
    loadApiPermissions(data.id)
  } else {
    buttonPermissions.value = []
    apiPermissions.value = []
  }
}

// 加载权限树
const loadPermissionTree = async () => {
  try {
    const res = await fetchPermissionTree()
    if (res.success && res.data) {
      permissionTree.value = res.data.result || []
    }
  } catch (e) {
    console.error('加载权限树失败:', e)
    ElMessage.error('加载权限数据失败')
  }
}

// 加载按钮权限
const loadButtonPermissions = async (parentId: string) => {
  try {
    const res = await fetchMenuButtons(parentId)
    if (res.success && res.data) {
      buttonPermissions.value = res.data.result || []
    }
  } catch (e) {
    console.error('加载按钮权限失败:', e)
  }
}

// 加载API权限（从权限列表中筛选）
const loadApiPermissions = async (parentId: string) => {
  try {
    const res = await fetchPermissionList({ parent_id: parentId, menu_type: 2, pageSize: 100 })
    if (res.success && res.data) {
      apiPermissions.value = res.data.result || []
    }
  } catch (e) {
    console.error('加载API权限失败:', e)
  }
}

// 显示菜单抽屉
const showMenuDrawer = (type: 'add' | 'edit', data?: PermissionInfo) => {
  menuDrawerType.value = type
  currentMenuData.value = data || {}
  menuDrawerVisible.value = true
}

// 添加子菜单
const addSubMenu = () => {
  currentMenuData.value = { parent_id: selectedPermission.value?.id, menu_type: 0 }
  menuDrawerType.value = 'add'
  menuDrawerVisible.value = true
}

// 显示按钮抽屉
const showButtonDrawer = (type: 'add' | 'edit', data?: PermissionInfo) => {
  buttonDrawerType.value = type
  currentButtonData.value = data || {}
  buttonDrawerVisible.value = true
}

// 显示API抽屉
const showApiDrawer = (type: 'add' | 'edit', data?: PermissionInfo) => {
  apiDrawerType.value = type
  currentApiData.value = data || {}
  apiDrawerVisible.value = true
}

// 删除权限
const deletePermission = async (row: PermissionInfo) => {
  const name = translateTitle(row.title) || row.name
  const confirm = await ElMessageBox.confirm(`确定删除权限【${name}】吗？`, '确认删除', { type: 'warning' }).catch(() => false)
  if (!confirm) return

  try {
    const res = await deletePermissionApi(row.id!)
    if (res.success) {
      ElMessage.success('删除成功')
      selectedPermission.value = null
      loadPermissionTree()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    console.error('删除权限失败:', e)
    ElMessage.error('删除失败')
  }
}

// 删除按钮
const deleteButton = async (row: PermissionInfo) => {
  const name = translateTitle(row.authTitle) || row.name
  const confirm = await ElMessageBox.confirm(`确定删除按钮【${name}】吗？`, '确认删除', { type: 'warning' }).catch(() => false)
  if (!confirm) return

  try {
    const res = await deleteButtonPermissionApi(row.id!)
    if (res.success) {
      ElMessage.success('删除成功')
      if (selectedPermission.value?.id) loadButtonPermissions(selectedPermission.value.id)
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    console.error('删除按钮失败:', e)
    ElMessage.error('删除失败')
  }
}

// 删除API
const deleteApi = async (row: PermissionInfo) => {
  const name = row.title || row.name
  const confirm = await ElMessageBox.confirm(`确定删除API权限【${name}】吗？`, '确认删除', { type: 'warning' }).catch(() => false)
  if (!confirm) return

  try {
    const res = await deleteApiPermissionApi(row.id!)
    if (res.success) {
      ElMessage.success('删除成功')
      if (selectedPermission.value?.id) loadApiPermissions(selectedPermission.value.id)
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    console.error('删除API失败:', e)
    ElMessage.error('删除失败')
  }
}

// 菜单操作成功
const handleMenuSuccess = () => {
  loadPermissionTree()
}

// 按钮操作成功
const handleButtonSuccess = () => {
  if (selectedPermission.value?.id) loadButtonPermissions(selectedPermission.value.id)
}

// API操作成功
const handleApiSuccess = () => {
  if (selectedPermission.value?.id) loadApiPermissions(selectedPermission.value.id)
}

onMounted(() => loadPermissionTree())
</script>

<style lang="scss" scoped>
:deep(.el-container) {
  height: 100%;
}

.perm-aside {
  height: 100%;
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  overflow: hidden;
}

.perm-card {
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

.perm-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.perm-tree-wrapper {
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

.detail-card {
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
  
  :deep(.el-tabs) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  :deep(.el-tabs__header) {
    padding: 0 16px;
    margin: 0;
  }
  
  :deep(.el-tabs__nav-wrap) {
    padding: 0;
  }
  
  :deep(.el-tabs__content) {
    flex: 1;
    overflow: auto;
    padding: 16px;
  }
}

.info-section {
  padding: 8px 0;
  
  :deep(.el-descriptions) {
    .el-descriptions__label {
      width: 140px;
      font-weight: 500;
      color: var(--el-text-color-regular);
      text-align: right;
      padding-right: 16px;
      vertical-align: top;
    }
    
    .el-descriptions__content {
      word-break: break-all;
      padding-left: 16px;
      vertical-align: top;
    }
    
    .el-descriptions__cell {
      padding: 12px 16px;
      vertical-align: top;
    }
    
    .el-descriptions__table {
      width: 100%;
      table-layout: fixed;
    }
    
    .el-descriptions__body {
      .el-descriptions__table {
        .el-descriptions__row {
          .el-descriptions__cell {
            &:nth-child(odd) {
              width: 160px;
            }
            &:nth-child(even) {
              width: calc(50% - 80px);
            }
          }
        }
      }
    }
  }
  
  // 响应式优化
  @media (max-width: 768px) {
    :deep(.el-descriptions) {
      .el-descriptions__label {
        width: 120px;
        font-size: 13px;
      }
      
      .el-descriptions__content {
        font-size: 13px;
      }
      
      .el-descriptions__cell {
        padding: 8px 12px;
      }
    }
  }
}

.tab-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tab-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.code-tag {
  font-size: 12px;
  background: var(--el-fill-color-light);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: var(--el-text-color-primary);
  border: 1px solid var(--el-border-color-lighter);
  display: inline-block;
  max-width: 100%;
  word-break: break-all;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
