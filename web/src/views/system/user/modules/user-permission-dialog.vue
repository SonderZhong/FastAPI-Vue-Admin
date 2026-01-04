<template>
  <ElDialog
    v-model="dialogVisible"
    :title="$t('user.viewPermissions', '查看权限')"
    width="900px"
    :before-close="handleClose"
  >
    <div v-if="userData">
      <div class="mb-4">
        <ElAlert
          :title="$t('user.userPermissions', '用户 {name} 的权限列表', { name: userData.nickname })"
          type="info"
          :closable="false"
        />
      </div>

      <!-- 权限统计 -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded-lg text-center">
          <div class="text-2xl font-bold text-blue-600">{{ totalPermissionsCount }}</div>
          <div class="text-sm text-gray-600 mt-1">{{
            $t('user.totalPermissions', '总权限数')
          }}</div>
        </div>
        <div class="bg-green-50 p-4 rounded-lg text-center">
          <div class="text-2xl font-bold text-green-600">{{ menuPermissionsCount }}</div>
          <div class="text-sm text-gray-600 mt-1"
            >{{ $t('common.menu', '菜单') }}{{ $t('common.permissions', '权限') }}</div
          >
        </div>
        <div class="bg-orange-50 p-4 rounded-lg text-center">
          <div class="text-2xl font-bold text-orange-600">{{ buttonPermissionsCount }}</div>
          <div class="text-sm text-gray-600 mt-1"
            >{{ $t('common.button', '按钮') }}{{ $t('common.permissions', '权限') }}</div
          >
        </div>
      </div>

      <!-- 权限搜索 -->
      <div class="mb-4">
        <ElInput
          v-model="searchText"
          :placeholder="$t('user.searchPermissions', '搜索权限名称或标识')"
          clearable
          :prefix-icon="Search"
          class="w-80"
        />
      </div>

      <!-- 权限树形列表 -->
      <div class="border rounded-lg">
        <ElTable
          :data="treePermissions"
          border
          max-height="400"
          v-loading="loading"
          row-key="permission_id"
          :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
          :expand-row-keys="expandedKeys"
          @expand-change="handleExpandChange"
        >
          <ElTableColumn
            prop="permission_name"
            :label="$t('common.permissionName', '权限名称')"
            min-width="250"
          >
            <template #default="{ row }">
              <div class="flex items-center">
                <ElIcon v-if="row.permission_type === 0" class="mr-2 text-blue-500">
                  <Menu />
                </ElIcon>
                <ElIcon v-else class="mr-2 text-orange-500">
                  <Operation />
                </ElIcon>
                <span>{{ getTranslatedPermissionName(row.permission_name) }}</span>
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn
            prop="permission_auth"
            :label="$t('common.authMark', '权限标识')"
            min-width="200"
            show-overflow-tooltip
          />
          <ElTableColumn
            prop="permission_type"
            :label="$t('common.type', '类型')"
            width="100"
            align="center"
          >
            <template #default="{ row }">
              <ElTag :type="row.permission_type === 0 ? 'primary' : 'warning'" size="small">
                {{
                  row.permission_type === 0
                    ? $t('common.menu', '菜单')
                    : $t('common.button', '按钮')
                }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="role_name" :label="$t('user.fromRole', '来源角色')" min-width="120">
            <template #default="{ row }">
              <ElTag type="success" size="small">{{ row.role_name }}</ElTag>
            </template>
          </ElTableColumn>
        </ElTable>

        <div
          v-if="filteredPermissions.length === 0 && !loading"
          class="p-8 text-center text-gray-500"
        >
          <ElIcon class="text-4xl mb-4 text-gray-400"><Lock /></ElIcon>
          <p>{{ $t('user.noPermissions', '暂无权限数据') }}</p>
        </div>
      </div>

      <!-- 权限说明 -->
      <div class="mt-4 p-4 bg-gray-50 rounded-lg">
        <div class="text-sm text-gray-600">
          <div class="font-medium mb-2">{{ $t('user.permissionExplanation', '权限说明') }}：</div>
          <ul class="list-disc list-inside space-y-1 text-xs">
            <li>{{
              $t('user.menuPermissionDesc', '菜单权限：控制用户可以访问的页面和功能模块')
            }}</li>
            <li>{{
              $t('user.buttonPermissionDesc', '按钮权限：控制用户可以执行的具体操作，如增删改查')
            }}</li>
            <li>{{
              $t(
                'user.rolePermissionDesc',
                '用户权限通过角色获得，修改角色权限会影响所有该角色的用户'
              )
            }}</li>
          </ul>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">{{ $t('buttons.close', '关闭') }}</ElButton>
        <ElButton type="primary" @click="refreshData" :loading="loading">
          {{ $t('buttons.refresh', '刷新') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Search, Lock, Menu, Operation } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import {
    fetchUserPermissionList,
    type UserInfo,
    type UserPermissionInfo
  } from '@/api/system/user'

  const { t: $t } = useI18n()

  interface Props {
    visible: boolean
    userData?: UserInfo
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
  }

  const props = withDefaults(defineProps<Props>(), {
    visible: false
  })

  const emit = defineEmits<Emits>()

  // 响应式数据
  const loading = ref(false)
  const searchText = ref('')
  const permissions = ref<UserPermissionInfo[]>([])
  const expandedKeys = ref<string[]>([])

  // 弹窗显示状态
  const dialogVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  // 权限名称国际化映射
  const permissionNameMap = computed(() => ({
    // 系统管理相关
    系统管理: $t('menus.system.title', '系统管理'),
    用户管理: $t('menus.system.user', '用户管理'),
    角色管理: $t('menus.system.role', '角色管理'),
    部门管理: $t('menus.system.department', '部门管理'),
    菜单管理: $t('menus.system.menu', '菜单管理'),
    权限管理: $t('menus.system.permission', '权限管理'),
    // 按钮操作相关
    新增: $t('buttons.add', '新增'),
    编辑: $t('buttons.edit', '编辑'),
    删除: $t('buttons.delete', '删除'),
    查看: $t('buttons.info', '查看详情'),
    导出: $t('buttons.export', '导出'),
    导入: $t('buttons.import', '导入'),
    重置密码: $t('buttons.resetPassword', '重置密码'),
    分配权限: $t('buttons.assignPermission', '分配权限'),
    // 仪表板相关
    仪表板: $t('menus.dashboard.title', '仪表板'),
    控制台: $t('menus.dashboard.console', '控制台'),
    // 异常页面相关
    异常页面: $t('menus.exception.title', '异常页面'),
    '403': $t('menus.exception.forbidden', '403'),
    '404': $t('menus.exception.notFound', '404'),
    '500': $t('menus.exception.serverError', '500')
  }))

  /**
   * 构建树形权限结构
   */
  const buildPermissionTree = (permissions: UserPermissionInfo[]): UserPermissionInfo[] => {
    const permissionMap = new Map<string, UserPermissionInfo>()
    const rootPermissions: UserPermissionInfo[] = []

    // 创建权限映射
    permissions.forEach((permission) => {
      permissionMap.set(permission.permission_id, { ...permission, children: [] })
    })

    // 构建树形结构
    permissions.forEach((permission) => {
      const currentPermission = permissionMap.get(permission.permission_id)!

      if (permission.parent_id && permissionMap.has(permission.parent_id)) {
        // 有父权限，添加到父权限的子级
        const parentPermission = permissionMap.get(permission.parent_id)!
        if (!parentPermission.children) {
          parentPermission.children = []
        }
        parentPermission.children.push(currentPermission)
      } else {
        // 顶级权限
        rootPermissions.push(currentPermission)
      }
    })

    return rootPermissions
  }

  // 树形权限数据
  const treePermissions = computed(() => {
    return buildPermissionTree(filteredPermissions.value)
  })

  // 过滤后的权限列表
  const filteredPermissions = computed(() => {
    if (!searchText.value) return permissions.value

    const keyword = searchText.value.toLowerCase()
    return permissions.value.filter(
      (permission) =>
        getTranslatedPermissionName(permission.permission_name).toLowerCase().includes(keyword) ||
        permission.permission_auth.toLowerCase().includes(keyword) ||
        permission.role_name.toLowerCase().includes(keyword)
    )
  })

  /**
   * 获取翻译后的权限名称
   */
  const getTranslatedPermissionName = (permissionName: string): string => {
    return (permissionNameMap.value as Record<string, string>)[permissionName] || permissionName
  }

  /**
   * 处理树形表格展开/收起
   */
  const handleExpandChange = (row: UserPermissionInfo, expanded: boolean) => {
    if (expanded) {
      if (!expandedKeys.value.includes(row.permission_id)) {
        expandedKeys.value.push(row.permission_id)
      }
    } else {
      const index = expandedKeys.value.indexOf(row.permission_id)
      if (index > -1) {
        expandedKeys.value.splice(index, 1)
      }
    }
  }

  // 总权限数量
  const totalPermissionsCount = computed(() => {
    return permissions.value.length
  })

  // 菜单权限数量
  const menuPermissionsCount = computed(() => {
    return permissions.value.filter((permission) => permission.permission_type === 0).length
  })

  // 按钮权限数量
  const buttonPermissionsCount = computed(() => {
    return permissions.value.filter((permission) => permission.permission_type === 1).length
  })

  /**
   * 监听弹窗显示状态
   */
  watch(
    () => props.visible,
    (newVal) => {
      if (newVal && props.userData) {
        loadUserPermissions()
      }
    }
  )

  /**
   * 关闭弹窗
   */
  const handleClose = () => {
    dialogVisible.value = false
    searchText.value = ''
  }

  /**
   * 加载用户权限列表
   */
  const loadUserPermissions = async () => {
    if (!props.userData) return

    try {
      loading.value = true
      const response = await fetchUserPermissionList(props.userData.id)
      if (response.success && response.data) {
        permissions.value = response.data.result || []
      }
    } catch (error) {
      console.error('加载用户权限失败:', error)
      ElMessage.error($t('user.loadPermissionsFailed', '加载权限失败'))
    } finally {
      loading.value = false
    }
  }

  /**
   * 刷新数据
   */
  const refreshData = () => {
    loadUserPermissions()
  }
</script>

<style scoped>
  .dialog-footer {
    text-align: right;
  }
</style>
