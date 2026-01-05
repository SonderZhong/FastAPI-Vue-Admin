<template>
  <ElDialog
    v-model="visible"
    :title="$t('role.assignPermissions', '分配权限')"
    width="70%"
    align-center
    @close="handleClose"
  >
    <div class="permission-dialog">
      <div class="dialog-header mb-4">
        <ElSpace>
          <ElButton type="primary" size="small" @click="expandAll">{{
            $t('buttons.expandAll', '展开全部')
          }}</ElButton>
          <ElButton type="primary" size="small" @click="collapseAll">{{
            $t('buttons.collapseAll', '收起全部')
          }}</ElButton>
          <ElButton type="success" size="small" @click="checkAll">{{
            $t('buttons.selectAll', '全选')
          }}</ElButton>
          <ElButton type="warning" size="small" @click="uncheckAll">{{
            $t('buttons.deselectAll', '取消全选')
          }}</ElButton>
        </ElSpace>
      </div>

      <ElScrollbar height="60vh">
        <ElTree
          ref="treeRef"
          :data="permissionTree"
          show-checkbox
          node-key="id"
          :default-expand-all="false"
          :default-checked-keys="checkedKeys"
          :props="treeProps"
          @check="handleTreeCheck"
        >
          <template #default="{ data }">
            <div class="flex items-center">
              <ElIcon class="mr-2 text-blue-500">
                <OfficeBuilding v-if="data.menu_type === 0" />
                <Setting v-else />
              </ElIcon>
              <span>{{ translateTitle(data.title) || data.name }}</span>
              <ElTag v-if="data.menu_type === 1" type="warning" size="small" class="ml-2">
                {{ $t('common.button', '按钮') }}
              </ElTag>
            </div>
          </template>
        </ElTree>
      </ElScrollbar>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">{{ $t('buttons.cancel', '取消') }}</ElButton>
        <ElButton type="primary" @click="handleSubmit">{{
          $t('buttons.confirm', '确定')
        }}</ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ref, computed, watch, nextTick } from 'vue'
  import { ElMessage, ElTree } from 'element-plus'
  import { OfficeBuilding, Setting } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { fetchPermissionTree, type PermissionInfo } from '@/api/system/permission'
  import { fetchRolePermissionList, assignRolePermissions, type RoleInfo } from '@/api/system/role'

  const { t: $t } = useI18n()

  /**
   * 翻译权限标题
   */
  const translateTitle = (title?: string): string => {
    if (!title) return ''

    // 如果标题是国际化键值，则翻译
    if (title.includes('.')) {
      try {
        const translated = $t(title)
        return translated !== title ? translated : title
      } catch {
        return title
      }
    }

    return title
  }

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

  // 树组件引用
  const treeRef = ref<InstanceType<typeof ElTree>>()

  // 权限树数据
  const permissionTree = ref<PermissionInfo[]>([])
  const checkedKeys = ref<string[]>([])

  // 树组件配置
  const treeProps = {
    children: 'children',
    label: 'title'
  }

  // 监听对话框打开
  watch(visible, (newVisible) => {
    if (newVisible && props.roleData) {
      loadPermissionTree()
      loadRolePermissions()
    }
  })

  /**
   * 加载权限树数据
   */
  const loadPermissionTree = async () => {
    try {
      const response = await fetchPermissionTree()
      if (response.success && response.data) {
        permissionTree.value = response.data?.result || []
      }
    } catch (error) {
      console.error('加载权限树失败:', error)
      ElMessage.error('加载权限树失败')
    }
  }

  /**
   * 加载角色权限
   */
  const loadRolePermissions = async () => {
    if (!props.roleData?.id) return

    try {
      const response = await fetchRolePermissionList(props.roleData.id)
      if (response.success && response.data) {
        // 使用权限ID作为选中的key
        checkedKeys.value =
          response.data?.result?.map((item) => item.permission_id) || []
        nextTick(() => {
          treeRef.value?.setCheckedKeys(checkedKeys.value)
        })
      }
    } catch (error) {
      console.error('加载角色权限失败:', error)
    }
  }

  /**
   * 展开全部
   */
  const expandAll = () => {
    const tree = treeRef.value
    if (tree) {
      const getAllKeys = (nodes: PermissionInfo[]): string[] => {
        let keys: string[] = []
        nodes.forEach((node) => {
          if (node.id) {
            keys.push(node.id)
          }
          if (node.children && node.children.length > 0) {
            keys = keys.concat(getAllKeys(node.children))
          }
        })
        return keys
      }

      const allKeys = getAllKeys(permissionTree.value)
      allKeys.forEach((key) => {
        tree.store.nodesMap[key]?.expand()
      })
    }
  }

  /**
   * 收起全部
   */
  const collapseAll = () => {
    const tree = treeRef.value
    if (tree) {
      const getAllKeys = (nodes: PermissionInfo[]): string[] => {
        let keys: string[] = []
        nodes.forEach((node) => {
          if (node.id) {
            keys.push(node.id)
          }
          if (node.children && node.children.length > 0) {
            keys = keys.concat(getAllKeys(node.children))
          }
        })
        return keys
      }

      const allKeys = getAllKeys(permissionTree.value)
      allKeys.forEach((key) => {
        tree.store.nodesMap[key]?.collapse()
      })
    }
  }

  /**
   * 全选
   */
  const checkAll = () => {
    const tree = treeRef.value
    if (tree) {
      const getAllKeys = (nodes: PermissionInfo[]): string[] => {
        let keys: string[] = []
        nodes.forEach((node) => {
          if (node.id) {
            keys.push(node.id)
          }
          if (node.children && node.children.length > 0) {
            keys = keys.concat(getAllKeys(node.children))
          }
        })
        return keys
      }

      const allKeys = getAllKeys(permissionTree.value)
      tree.setCheckedKeys(allKeys)
    }
  }

  /**
   * 取消全选
   */
  const uncheckAll = () => {
    const tree = treeRef.value
    if (tree) {
      tree.setCheckedKeys([])
    }
  }

  /**
   * 处理树节点选择
   */
  const handleTreeCheck = () => {
    // 可以在这里处理选择逻辑
  }

  /**
   * 关闭对话框
   */
  const handleClose = () => {
    visible.value = false
  }

  /**
   * 提交权限分配
   */
  const handleSubmit = async () => {
    if (!props.roleData?.id) return

    try {
      const tree = treeRef.value
      if (!tree) return

      const checkedNodes = tree.getCheckedKeys()
      const halfCheckedNodes = tree.getHalfCheckedKeys()
      const allCheckedKeys = [...checkedNodes, ...halfCheckedNodes] as string[]

      console.log('角色ID:', props.roleData.id)
      console.log('选中的权限ID:', allCheckedKeys)

      const response = await assignRolePermissions(props.roleData.id, {
        permission_ids: allCheckedKeys
      })

      if (response.success) {
        ElMessage.success('权限分配成功')
        emit('success')
        handleClose()
      } else {
        console.error('权限分配失败:', response)
        ElMessage.error(response.msg || '权限分配失败')
      }
    } catch (error) {
      console.error('权限分配异常:', error)
      ElMessage.error('权限分配失败: ' + (error as any)?.message || '未知错误')
    }
  }
</script>

<style lang="scss" scoped>
  .permission-dialog {
    .dialog-header {
      padding: 10px 0;
      border-bottom: 1px solid #ebeef5;
    }
  }

  .dialog-footer {
    text-align: right;
  }
</style>
