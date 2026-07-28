<template>
  <ElDrawer v-model="visible" :title="drawerTitle" size="560px" @closed="handleClosed">
    <div class="flex h-full min-h-0 flex-col">
      <div
        class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--el-border-color-lighter)] pb-4"
      >
        <ElCheckbox v-model="cascadeEnabled" size="small">
          {{ $t('role.cascadeSelection') }}
        </ElCheckbox>

        <ElSpace wrap>
          <ElButton size="small" @click="expandAll">{{ $t('buttons.expandAll') }}</ElButton>
          <ElButton size="small" @click="collapseAll">{{ $t('buttons.collapseAll') }}</ElButton>
          <ElButton size="small" type="success" @click="checkAll">{{
            $t('buttons.selectAll')
          }}</ElButton>
          <ElButton size="small" type="warning" @click="uncheckAll">{{
            $t('buttons.deselectAll')
          }}</ElButton>
        </ElSpace>
      </div>

      <div class="mt-4 flex-1 min-h-0 overflow-hidden">
        <ElScrollbar height="100%">
          <ElTree
            ref="treeRef"
            v-loading="loading"
            :data="permissionTree"
            node-key="id"
            show-checkbox
            :check-strictly="!cascadeEnabled"
            :props="treeProps"
          >
            <template #default="{ data }">
              <div class="flex min-w-0 items-center gap-2 py-1">
                <ElIcon :class="data.menu_type === 0 ? 'text-sky-500' : 'text-amber-500'">
                  <FolderOpened v-if="data.menu_type === 0" />
                  <Operation v-else />
                </ElIcon>
                <span class="truncate">{{ getNodeLabel(data) }}</span>
                <ElTag v-if="data.menu_type === 0" size="small" type="primary">{{
                  $t('common.menu')
                }}</ElTag>
                <ElTag v-else size="small" type="warning">{{ $t('common.button') }}</ElTag>
                <code
                  v-if="data.authMark"
                  class="truncate rounded bg-[var(--el-fill-color-light)] px-2 py-0.5 text-xs text-[var(--el-text-color-secondary)]"
                >
                  {{ data.authMark }}
                </code>
              </div>
            </template>
          </ElTree>
        </ElScrollbar>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <ElButton @click="visible = false">{{ $t('buttons.cancel') }}</ElButton>
        <ElButton type="primary" :loading="submitting" @click="handleSubmit">
          {{ $t('buttons.confirm') }}
        </ElButton>
      </div>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
  import { computed, nextTick, ref, watch } from 'vue'
  import { ElMessage, ElTree } from 'element-plus'
  import { FolderOpened, Operation } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { fetchPermissionTree, type PermissionTree } from '@/api/system/permission'
  import { assignRolePermissions, fetchRolePermissionList, type RoleInfo } from '@/api/system/role'

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
  const { t: $t } = useI18n()

  const visible = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emit('update:modelValue', value)
  })

  const drawerTitle = computed(
    () => `${$t('role.assignPermissions')}${props.roleData ? ` - ${props.roleData.name}` : ''}`
  )

  const treeRef = ref<InstanceType<typeof ElTree>>()
  const loading = ref(false)
  const submitting = ref(false)
  const cascadeEnabled = ref(false)
  const permissionTree = ref<PermissionTree[]>([])

  const treeProps = {
    children: 'children',
    label: 'title'
  }

  const filterPermissionTree = (nodes: PermissionTree[] = []): PermissionTree[] => {
    return nodes
      .filter((node) => node.menu_type === 0 || node.menu_type === 1)
      .map((node) => ({
        ...node,
        children: filterPermissionTree(node.children || [])
      }))
  }

  const getNodeLabel = (node: PermissionTree) => {
    const raw = node.title || node.authTitle || node.name || node.authMark || ''
    if (raw.includes('.')) {
      const translated = $t(raw)
      return translated === raw ? raw : translated
    }
    return raw
  }

  const getAllKeys = (nodes: PermissionTree[]): string[] => {
    return nodes
      .flatMap((node) => [node.id || '', ...getAllKeys(node.children || [])])
      .filter(Boolean)
  }

  const loadPermissionTree = async () => {
    loading.value = true
    try {
      const res = await fetchPermissionTree()
      permissionTree.value = filterPermissionTree(res.data?.result || [])
    } catch (error) {
      console.error('load permission tree failed:', error)
      ElMessage.error($t('user.loadPermissionsFailed'))
    } finally {
      loading.value = false
    }
  }

  const loadRolePermissions = async () => {
    if (!props.roleData?.id) {
      return
    }

    try {
      const res = await fetchRolePermissionList(props.roleData.id)
      const checkedKeys = [...(res.data?.menu_ids || []), ...(res.data?.button_ids || [])]
      await nextTick()
      treeRef.value?.setCheckedKeys(checkedKeys)
    } catch (error) {
      console.error('load role permissions failed:', error)
      ElMessage.error($t('common.loadFailed'))
    }
  }

  const expandAll = () => {
    const tree = treeRef.value
    if (!tree) return
    getAllKeys(permissionTree.value).forEach((key) => tree.store.nodesMap[key]?.expand())
  }

  const collapseAll = () => {
    const tree = treeRef.value
    if (!tree) return
    getAllKeys(permissionTree.value).forEach((key) => tree.store.nodesMap[key]?.collapse())
  }

  const checkAll = () => {
    treeRef.value?.setCheckedKeys(getAllKeys(permissionTree.value))
  }

  const uncheckAll = () => {
    treeRef.value?.setCheckedKeys([])
  }

  const handleSubmit = async () => {
    if (!props.roleData?.id) {
      return
    }

    try {
      submitting.value = true
      const checkedKeys = (treeRef.value?.getCheckedKeys() || []) as string[]
      const halfCheckedKeys = (treeRef.value?.getHalfCheckedKeys() || []) as string[]
      const permissionIds = [...new Set([...checkedKeys, ...halfCheckedKeys])]

      const res = await assignRolePermissions(props.roleData.id, {
        permission_ids: permissionIds
      })

      if (res.success) {
        ElMessage.success($t('common.operationSuccess'))
        emit('success')
        visible.value = false
        return
      }

      ElMessage.error(res.msg || $t('common.operationFailed'))
    } catch (error) {
      console.error('assign role permissions failed:', error)
      ElMessage.error($t('common.operationFailed'))
    } finally {
      submitting.value = false
    }
  }

  const handleClosed = () => {
    cascadeEnabled.value = false
    treeRef.value?.setCheckedKeys([])
  }

  watch(
    () => visible.value,
    async (value) => {
      if (!value || !props.roleData?.id) {
        return
      }

      cascadeEnabled.value = false
      await loadPermissionTree()
      await loadRolePermissions()
    }
  )
</script>
