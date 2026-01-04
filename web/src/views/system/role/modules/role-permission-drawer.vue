<template>
  <ElDrawer
    v-model="visible"
    :title="$t('role.assignPermissions', '分配权限') + (roleData ? ` - ${roleData.name}` : '')"
    size="560px"
    :destroy-on-close="false"
    class="permission-drawer"
    @close="handleClose"
  >
    <!-- Tab 切换 -->
    <ElTabs v-model="activeTab" class="permission-tabs">
      <!-- 菜单/按钮权限 Tab -->
      <ElTabPane name="menu" :label="$t('role.menuPermission', '菜单/按钮权限')">
        <div class="tab-content">
          <!-- 操作按钮 -->
          <div class="action-bar">
            <div class="action-left">
              <ElCheckbox v-model="cascadeEnabled" size="small">
                {{ $t('role.cascadeSelection', '级联选择') }}
              </ElCheckbox>
            </div>
            <div class="action-right">
              <ElButton size="small" round @click="expandAllMenu">
                <ElIcon class="mr-1"><ArrowDown /></ElIcon>
                {{ $t('buttons.expandAll', '展开') }}
              </ElButton>
              <ElButton size="small" round @click="collapseAllMenu">
                <ElIcon class="mr-1"><ArrowUp /></ElIcon>
                {{ $t('buttons.collapseAll', '收起') }}
              </ElButton>
              <ElButton type="success" size="small" round @click="checkAllMenu">
                <ElIcon class="mr-1"><Select /></ElIcon>
                {{ $t('buttons.selectAll', '全选') }}
              </ElButton>
              <ElButton type="warning" size="small" round @click="uncheckAllMenu">
                <ElIcon class="mr-1"><CloseBold /></ElIcon>
                {{ $t('buttons.deselectAll', '取消') }}
              </ElButton>
            </div>
          </div>

          <!-- 菜单权限树 -->
          <div class="tree-container">
            <ElScrollbar>
              <ElTree
                ref="menuTreeRef"
                v-loading="menuLoading"
                :data="menuPermissionTree"
                show-checkbox
                node-key="id"
                :default-expand-all="false"
                :check-strictly="!cascadeEnabled"
                :props="treeProps"
              >
                <template #default="{ data }">
                  <div class="tree-node">
                    <ElIcon :class="getIconClass(data.menu_type)">
                      <Folder v-if="data.menu_type === 0" />
                      <Operation v-else-if="data.menu_type === 1" />
                      <Link v-else />
                    </ElIcon>
                    <span class="node-label">{{ translateTitle(data.title) || data.name }}</span>
                    <ElTag v-if="data.menu_type === 1" type="warning" size="small" round>
                      {{ $t('common.button', '按钮') }}
                    </ElTag>
                    <ElTag v-else-if="data.menu_type === 2" type="success" size="small" round>
                      API
                    </ElTag>
                    <template v-if="data.menu_type === 2 && data.api_path">
                      <ElTag :type="getMethodTagType(data.api_method)" size="small" round class="ml-1">
                        {{ Array.isArray(data.api_method) ? data.api_method.join(',') : (data.api_method || 'GET') }}
                      </ElTag>
                      <code class="api-path">{{ data.api_path }}</code>
                    </template>
                  </div>
                </template>
              </ElTree>
            </ElScrollbar>
          </div>
        </div>
      </ElTabPane>

      <!-- API 权限 Tab -->
      <ElTabPane name="api" :label="$t('role.publicApiPermission', '公共API权限')">
        <div class="tab-content">
          <!-- 操作按钮 -->
          <div class="action-bar">
            <div class="action-left">
              <ElCheckbox v-model="cascadeEnabled" size="small">
                {{ $t('role.cascadeSelection', '级联选择') }}
              </ElCheckbox>
            </div>
            <div class="action-right">
              <ElButton size="small" round @click="expandAllApi">
                <ElIcon class="mr-1"><ArrowDown /></ElIcon>
                {{ $t('buttons.expandAll', '展开') }}
              </ElButton>
              <ElButton size="small" round @click="collapseAllApi">
                <ElIcon class="mr-1"><ArrowUp /></ElIcon>
                {{ $t('buttons.collapseAll', '收起') }}
              </ElButton>
              <ElButton type="success" size="small" round @click="checkAllApi">
                <ElIcon class="mr-1"><Select /></ElIcon>
                {{ $t('buttons.selectAll', '全选') }}
              </ElButton>
              <ElButton type="warning" size="small" round @click="uncheckAllApi">
                <ElIcon class="mr-1"><CloseBold /></ElIcon>
                {{ $t('buttons.deselectAll', '取消') }}
              </ElButton>
            </div>
          </div>

          <!-- API 权限树 -->
          <div class="tree-container">
            <ElScrollbar>
              <ElTree
                ref="apiTreeRef"
                v-loading="apiLoading"
                :data="apiPermissionTree"
                show-checkbox
                node-key="id"
                :default-expand-all="false"
                :check-strictly="!cascadeEnabled"
                :props="treeProps"
              >
                <template #default="{ data }">
                  <div class="tree-node">
                    <ElIcon class="text-green-500">
                      <Connection v-if="data.children?.length" />
                      <Link v-else />
                    </ElIcon>
                    <span class="node-label">{{ data.title || data.name }}</span>
                    <template v-if="data.api_path">
                      <ElTag :type="getMethodTagType(data.api_method)" size="small" round class="ml-2">
                        {{ data.api_method || 'GET' }}
                      </ElTag>
                      <code class="api-path">{{ data.api_path }}</code>
                    </template>
                  </div>
                </template>
              </ElTree>
            </ElScrollbar>
          </div>
        </div>
      </ElTabPane>
    </ElTabs>

    <template #footer>
      <div class="drawer-footer">
        <ElButton round @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" round :loading="submitting" @click="handleSubmit">
          {{ $t('buttons.confirm', '确定') }}
        </ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElTree } from 'element-plus'
import { ArrowDown, ArrowUp, Select, CloseBold, Folder, Operation, Connection, Link } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { fetchPermissionList, type PermissionInfo } from '@/api/system/permission'
import { fetchRolePermissionList, assignRolePermissions, type RoleInfo } from '@/api/system/role'

const { t } = useI18n()

interface Props {
  modelValue: boolean
  roleData?: RoleInfo
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  roleData: undefined
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Tab 状态
const activeTab = ref('menu')

// 树组件引用
const menuTreeRef = ref<InstanceType<typeof ElTree>>()
const apiTreeRef = ref<InstanceType<typeof ElTree>>()

// 加载状态
const menuLoading = ref(false)
const apiLoading = ref(false)
const submitting = ref(false)

// 级联选择控制
const cascadeEnabled = ref(false)

// 权限数据
const menuPermissionTree = ref<PermissionInfo[]>([])
const apiPermissionTree = ref<PermissionInfo[]>([])
const menuCheckedKeys = ref<string[]>([])
const apiCheckedKeys = ref<string[]>([])

const treeProps = {
  children: 'children',
  label: 'title'
}

const translateTitle = (title?: string): string => {
  if (!title) return ''
  if (title.includes('.')) {
    try {
      const translated = t(title)
      return translated !== title ? translated : title
    } catch {
      return title
    }
  }
  return title
}

const getMethodTagType = (method?: string | string[]): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  const methodMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'warning'
  }
  const methodStr = Array.isArray(method) ? method[0] : method
  return methodMap[methodStr || 'GET'] || 'info'
}

const getIconClass = (menuType?: number): string => {
  switch (menuType) {
    case 0: return 'text-blue-500'
    case 1: return 'text-orange-500'
    case 2: return 'text-green-500'
    default: return 'text-gray-500'
  }
}

watch(visible, async (newVisible) => {
  if (newVisible && props.roleData) {
    activeTab.value = 'menu'
    // 每次打开抽屉都重置级联开关为关闭状态
    cascadeEnabled.value = false
    // 清除之前的选中状态
    menuCheckedKeys.value = []
    apiCheckedKeys.value = []
    
    // 清除树组件状态
    nextTick(() => {
      menuTreeRef.value?.setCheckedKeys([])
      apiTreeRef.value?.setCheckedKeys([])
    })
    
    // 先加载权限数据，再加载角色权限
    await loadPermissions()
    // 等待权限树渲染完成后再设置选中状态
    await nextTick()
    await loadRolePermissions()
  }
})

// 构建树形结构
const buildTree = (items: PermissionInfo[], parentId: string | null = null): PermissionInfo[] => {
  return items
    .filter(item => item.parent_id === parentId || (!item.parent_id && !parentId))
    .map(item => ({
      ...item,
      children: buildTree(items, item.id)
    }))
    .filter(item => item.children?.length || !items.some(i => i.parent_id === item.id) || item.menu_type !== undefined)
}

const loadPermissions = async () => {
  try {
    menuLoading.value = true
    apiLoading.value = true
    
    // 获取所有权限
    const response = await fetchPermissionList({ pageSize: 1000 })
    if (response.success && response.data) {
      const allPermissions = response.data.result || []
      
      // 构建菜单权限树（包含菜单、按钮和相关的API权限）
      const menuAndButtonPerms = allPermissions.filter(p => p.menu_type === 0 || p.menu_type === 1)
      const apiPerms = allPermissions.filter(p => p.menu_type === 2)
      
      // 将有父级的API权限添加到菜单权限树中
      const menuTreePerms = [...menuAndButtonPerms]
      apiPerms.forEach(apiPerm => {
        if (apiPerm.parent_id) {
          menuTreePerms.push(apiPerm)
        }
      })
      
      // 构建菜单权限树
      menuPermissionTree.value = buildTree(menuTreePerms)
      
      // 构建API权限树（只包含独立的API权限，没有父级的）
      const independentApiPerms = apiPerms.filter(p => !p.parent_id)
      apiPermissionTree.value = buildTree(independentApiPerms)
    }
  } catch (error) {
    console.error('加载权限失败:', error)
    ElMessage.error('加载权限失败')
  } finally {
    menuLoading.value = false
    apiLoading.value = false
  }
}

const loadRolePermissions = async () => {
  if (!props.roleData?.id) return

  try {
    // 获取角色已选中的权限
    const response = await fetchRolePermissionList(props.roleData.id)
    if (response.success && response.data) {
      // 直接使用后端返回的已选中权限ID
      const checkedPermissionIds = response.data.actual_permission_ids || []
      
      // 设置两个树的选中状态
      menuCheckedKeys.value = checkedPermissionIds
      apiCheckedKeys.value = checkedPermissionIds
      
      // 强制清除并重新设置树组件状态
      nextTick(() => {
        // 先强制清空所有选中状态
        menuTreeRef.value?.setCheckedKeys([])
        apiTreeRef.value?.setCheckedKeys([])
        
        // 延迟设置新的选中状态，确保清空操作完成
        setTimeout(() => {
          menuTreeRef.value?.setCheckedKeys(checkedPermissionIds)
          apiTreeRef.value?.setCheckedKeys(checkedPermissionIds)
        }, 50)
      })
    }
  } catch (error) {
    console.error('加载角色权限失败:', error)
    ElMessage.error('加载角色权限失败')
  }
}

// 菜单树操作
const getAllMenuKeys = (nodes: PermissionInfo[]): string[] => {
  let keys: string[] = []
  nodes.forEach((node) => {
    if (node.id) keys.push(node.id)
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

const checkAllMenu = () => {
  menuTreeRef.value?.setCheckedKeys(getAllMenuKeys(menuPermissionTree.value))
}

const uncheckAllMenu = () => {
  menuTreeRef.value?.setCheckedKeys([])
}

// API 树操作
const getAllApiKeys = (nodes: PermissionInfo[]): string[] => {
  let keys: string[] = []
  nodes.forEach((node) => {
    if (node.id) keys.push(node.id)
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

const checkAllApi = () => {
  apiTreeRef.value?.setCheckedKeys(getAllApiKeys(apiPermissionTree.value))
}

const uncheckAllApi = () => {
  apiTreeRef.value?.setCheckedKeys([])
}

const handleClose = () => {
  visible.value = false
}

// 获取权限树中所有权限节点的ID
const getAllPermissionIds = (nodes: PermissionInfo[]): string[] => {
  let ids: string[] = []
  nodes.forEach((node) => {
    if (node.id) ids.push(node.id)
    if (node.children?.length) ids = ids.concat(getAllPermissionIds(node.children))
  })
  return ids
}

const handleSubmit = async () => {
  if (!props.roleData?.id) return

  try {
    submitting.value = true
    
    // 获取所有选中的权限（包括半选的）
    const menuTree = menuTreeRef.value
    const apiTree = apiTreeRef.value
    
    // 获取菜单权限树中所有选中的权限（包括半选）
    const menuCheckedKeys = menuTree ? menuTree.getCheckedKeys() as string[] : []
    const menuHalfCheckedKeys = menuTree ? menuTree.getHalfCheckedKeys() as string[] : []
    
    // 获取API权限树中所有选中的权限（包括半选）
    const apiCheckedKeys = apiTree ? apiTree.getCheckedKeys() as string[] : []
    const apiHalfCheckedKeys = apiTree ? apiTree.getHalfCheckedKeys() as string[] : []
    
    // 合并所有选中的权限（包括半选状态的父级权限）
    const allSelectedIds = [
      ...menuCheckedKeys,
      ...menuHalfCheckedKeys,
      ...apiCheckedKeys,
      ...apiHalfCheckedKeys
    ]
    
    // 去重
    const uniquePermissionIds = [...new Set(allSelectedIds)]

    const response = await assignRolePermissions(props.roleData.id, {
      permission_ids: uniquePermissionIds
    })

    if (response.success) {
      ElMessage.success(t('common.operationSuccess', '操作成功'))
      
      // 权限更新成功后，重新加载权限数据以确保显示正确
      await loadRolePermissions()
      
      emit('success')
      handleClose()
    } else {
      ElMessage.error(response.msg || t('common.operationFailed', '操作失败'))
    }
  } catch (error) {
    console.error('权限分配异常:', error)
    ElMessage.error('权限分配失败')
  } finally {
    submitting.value = false
  }
}
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
  }
  
  :deep(.el-drawer__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

.permission-tabs {
  height: 100%;
  
  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 20px;
    background: var(--el-fill-color-lighter);
  }
  
  :deep(.el-tabs__content) {
    height: calc(100% - 55px);
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
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  .action-left {
    flex-shrink: 0;
  }
  
  .action-right {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
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
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
