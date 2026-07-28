<template>
  <ElDrawer v-model="drawerVisible" :title="drawerTitle" size="560px" @closed="handleClosed">
    <div v-if="props.userData" class="flex h-full min-h-0 flex-col">
      <div class="flex items-center gap-3 rounded-lg bg-[var(--el-fill-color-lighter)] px-4 py-4">
        <ElAvatar :size="44" :src="getAvatarUrl(props.userData.avatar)">
          <ElIcon><User /></ElIcon>
        </ElAvatar>
        <div class="min-w-0 flex-1">
          <div class="truncate text-sm font-medium text-[var(--el-text-color-primary)]">
            {{ props.userData.nickname || props.userData.username }}
          </div>
          <div class="truncate text-xs text-[var(--el-text-color-secondary)]">
            @{{ props.userData.username }}
            <span v-if="props.userData.department_name">
              / {{ props.userData.department_name }}</span
            >
          </div>
        </div>
        <ElTag :type="props.userData.status === 1 ? 'success' : 'danger'" size="small">
          {{ props.userData.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
        </ElTag>
      </div>

      <div class="mt-4 grid grid-cols-3 gap-3">
        <div
          class="rounded-lg border border-[var(--el-border-color-lighter)] px-3 py-3 text-center"
        >
          <div class="text-lg font-semibold text-sky-600">{{ roleCount }}</div>
          <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">{{
            $t('role.roleName')
          }}</div>
        </div>
        <div
          class="rounded-lg border border-[var(--el-border-color-lighter)] px-3 py-3 text-center"
        >
          <div class="text-lg font-semibold text-emerald-600">{{ menuCount }}</div>
          <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">{{
            $t('permission.menu')
          }}</div>
        </div>
        <div
          class="rounded-lg border border-[var(--el-border-color-lighter)] px-3 py-3 text-center"
        >
          <div class="text-lg font-semibold text-amber-600">{{ buttonCount }}</div>
          <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">{{
            $t('common.button')
          }}</div>
        </div>
      </div>

      <div
        class="mt-4 flex flex-wrap items-center justify-between gap-3 border-b border-[var(--el-border-color-lighter)] pb-4"
      >
        <ElSpace wrap>
          <ElTag v-for="roleName in roleNames" :key="roleName" size="small" type="primary">
            {{ roleName }}
          </ElTag>
          <span v-if="roleNames.length === 0" class="text-sm text-[var(--el-text-color-secondary)]">
            {{ $t('user.noAssignedRoles') }}
          </span>
        </ElSpace>

        <ElSpace wrap>
          <ElButton size="small" @click="expandAll">{{ $t('buttons.expandAll') }}</ElButton>
          <ElButton size="small" @click="collapseAll">{{ $t('buttons.collapseAll') }}</ElButton>
        </ElSpace>
      </div>

      <div class="mt-4 min-h-0 flex-1 overflow-hidden">
        <ElScrollbar height="100%">
          <ElTree
            ref="treeRef"
            v-loading="loading"
            :data="permissionTree"
            node-key="permission_id"
            :props="treeProps"
            default-expand-all
          >
            <template #default="{ data }">
              <div class="flex min-w-0 items-center gap-2 py-1 pr-2">
                <ElIcon
                  :class="data.permission_type === 'menu' ? 'text-sky-500' : 'text-amber-500'"
                >
                  <FolderOpened v-if="data.permission_type === 'menu'" />
                  <Operation v-else />
                </ElIcon>
                <span class="truncate">{{ getPermissionLabel(data) }}</span>
                <span
                  v-if="data.permission_code"
                  class="truncate text-xs text-[var(--el-text-color-secondary)]"
                >
                  {{ data.permission_code }}
                </span>
                <ElTag v-if="data.permission_type === 'menu'" size="small" type="primary">
                  {{ $t('permission.menu') }}
                </ElTag>
                <ElTag v-else size="small" type="warning">
                  {{ $t('common.button') }}
                </ElTag>
                <ElTooltip
                  v-if="data.roles?.length"
                  :content="getRoleNamesText(data.roles)"
                  placement="top"
                >
                  <ElTag size="small" type="success">
                    {{ data.roles.length }} {{ $t('common.role', '角色') }}
                  </ElTag>
                </ElTooltip>
              </div>
            </template>
          </ElTree>

          <ElEmpty
            v-if="!loading && permissionTree.length === 0"
            :description="$t('user.noPermissions')"
          />
        </ElScrollbar>
      </div>
    </div>
  </ElDrawer>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import { ElMessage, ElTree } from 'element-plus'
  import { FolderOpened, Operation, User } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import {
    fetchUserPermissionList,
    type UserInfo,
    type UserPermissionInfo
  } from '@/api/system/user'
  import { getAvatarUrl } from '@/utils'

  interface Props {
    visible: boolean
    userData: UserInfo | null
  }

  interface Emits {
    (e: 'update:visible', visible: boolean): void
    (e: 'close'): void
  }

  type PermissionTreeNode = UserPermissionInfo & {
    children: PermissionTreeNode[]
  }

  const props = withDefaults(defineProps<Props>(), {
    visible: false,
    userData: null
  })

  const emit = defineEmits<Emits>()
  const { t: $t } = useI18n()

  const drawerVisible = computed({
    get: () => props.visible,
    set: (value: boolean) => emit('update:visible', value)
  })

  const drawerTitle = computed(
    () =>
      `${$t('user.viewPermissions')}${props.userData ? ` - ${props.userData.nickname || props.userData.username}` : ''}`
  )

  const treeRef = ref<InstanceType<typeof ElTree>>()
  const loading = ref(false)
  const permissions = ref<UserPermissionInfo[]>([])

  const treeProps = {
    children: 'children',
    label: 'permission_name'
  }

  const roleNames = computed(() => {
    const names = new Set<string>()
    permissions.value.forEach((permission) => {
      permission.roles?.forEach((role) => {
        if (role.name) {
          names.add(role.name)
        }
      })
    })
    return Array.from(names)
  })

  const getRoleNamesText = (roles: Array<{ id: string | null; name: string }> = []) =>
    roles.map((item) => item.name).join('、')

  const roleCount = computed(() => roleNames.value.length)
  const menuCount = computed(
    () => permissions.value.filter((item) => item.permission_type === 'menu').length
  )
  const buttonCount = computed(
    () => permissions.value.filter((item) => item.permission_type === 'button').length
  )

  const buildTree = (items: UserPermissionInfo[]): PermissionTreeNode[] => {
    const nodeMap = new Map<string, PermissionTreeNode>()
    const roots: PermissionTreeNode[] = []

    items.forEach((item) => {
      nodeMap.set(item.permission_id, {
        ...item,
        children: []
      })
    })

    items.forEach((item) => {
      const current = nodeMap.get(item.permission_id)
      if (!current) {
        return
      }

      const parentId = item.parent_id ? String(item.parent_id) : ''
      if (parentId && nodeMap.has(parentId)) {
        nodeMap.get(parentId)?.children.push(current)
        return
      }

      roots.push(current)
    })

    return roots
  }

  const permissionTree = computed(() => buildTree(permissions.value))

  const getPermissionLabel = (permission: UserPermissionInfo) => {
    const raw = permission.permission_name || permission.permission_code || ''
    if (raw.includes('.')) {
      const translated = $t(raw)
      return translated === raw ? raw : translated
    }
    return raw
  }

  const getAllKeys = (nodes: PermissionTreeNode[]): string[] => {
    return nodes.flatMap((node) => [node.permission_id, ...getAllKeys(node.children || [])])
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

  const fetchPermissions = async () => {
    if (!props.userData?.id) {
      permissions.value = []
      return
    }

    loading.value = true
    try {
      const res = await fetchUserPermissionList(props.userData.id)
      permissions.value = res.data?.result || []
    } catch (error) {
      console.error('fetch user permissions failed:', error)
      permissions.value = []
      ElMessage.error($t('common.loadFailed'))
    } finally {
      loading.value = false
    }
  }

  const handleClosed = () => {
    permissions.value = []
    emit('close')
  }

  watch(
    () => props.visible,
    (value) => {
      if (value) {
        fetchPermissions()
        return
      }
      permissions.value = []
    },
    { immediate: true }
  )
</script>
