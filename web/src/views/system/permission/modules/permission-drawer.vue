<template>
  <ElDrawer
    :model-value="modelValue"
    :title="drawerTitle"
    size="500px"
    :before-close="handleClose"
    @open="handleOpen"
    @update:model-value="emit('update:modelValue', $event)"
    class="permission-drawer"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      :disabled="formLoading"
    >
      <ElFormItem :label="$t('permission.permissionType')" prop="menu_type">
        <ElSelect v-model="formData.menu_type" :placeholder="$t('common.pleaseSelect')" style="width: 100%">
          <ElOption :label="$t('common.menu')" :value="0" />
          <ElOption :label="$t('common.button')" :value="1" />
          <ElOption label="API" :value="2" />
        </ElSelect>
      </ElFormItem>

      <ElFormItem :label="$t('permission.parentPermission')" prop="parent_id">
        <ElTreeSelect
          v-model="formData.parent_id"
          :data="permissionTreeData"
          :props="({ value: 'id', label: 'title', children: 'children' } as any)"
          :placeholder="$t('common.pleaseSelect')"
          check-strictly
          clearable
          :render-after-expand="false"
          style="width: 100%"
        />
      </ElFormItem>

      <!-- 权限名称：仅菜单和按钮类型需要 -->
      <ElFormItem v-if="formData.menu_type !== 2" :label="$t('common.permissionName')" prop="name">
        <ElInput v-model="formData.name" :placeholder="$t('common.pleaseInput')" />
      </ElFormItem>

      <ElFormItem :label="$t('common.displayName')" prop="title">
        <ElInput v-model="formData.title" :placeholder="$t('common.pleaseInput')" />
      </ElFormItem>

      <!-- 菜单类型字段 -->
      <template v-if="formData.menu_type === 0">
        <ElFormItem :label="$t('permission.routePath')" prop="path">
          <ElInput v-model="formData.path" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>

        <ElFormItem :label="$t('permission.componentPath')" prop="component">
          <ElInput v-model="formData.component" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>

        <ElFormItem :label="$t('common.icon')" prop="icon">
          <ArtIconSelector
            v-model="formData.icon"
            :iconType="IconTypeEnum.UNICODE"
            :text="$t('common.pleaseSelect')"
            width="100%"
          />
        </ElFormItem>
      </template>

      <!-- 按钮类型字段 -->
      <template v-if="formData.menu_type === 1">
        <ElFormItem :label="$t('permission.buttonName')" prop="authTitle">
          <ElInput v-model="formData.authTitle" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>

        <ElFormItem :label="$t('permission.permissionMark')" prop="authMark">
          <ElInput v-model="formData.authMark" placeholder="user:btn:add" />
        </ElFormItem>
      </template>

      <!-- API类型字段 -->
      <template v-if="formData.menu_type === 2">
        <ElFormItem :label="$t('permission.apiPath')" prop="api_path">
          <ElInput v-model="formData.api_path" placeholder="/api/user/*" />
        </ElFormItem>

        <ElFormItem :label="$t('permission.requestMethod')" prop="api_method">
          <ElCheckboxGroup v-model="formData.api_method">
            <ElCheckbox label="GET">GET</ElCheckbox>
            <ElCheckbox label="POST">POST</ElCheckbox>
            <ElCheckbox label="PUT">PUT</ElCheckbox>
            <ElCheckbox label="DELETE">DELETE</ElCheckbox>
            <ElCheckbox label="PATCH">PATCH</ElCheckbox>
          </ElCheckboxGroup>
        </ElFormItem>

        <ElFormItem :label="$t('permission.dataScope')" prop="data_scope">
          <ElSelect v-model="formData.data_scope" :placeholder="$t('common.pleaseSelect')" style="width: 100%">
            <ElOption :label="$t('permission.dataScopeAll')" :value="1" />
            <ElOption :label="$t('permission.dataScopeDeptAndChild')" :value="2" />
            <ElOption :label="$t('permission.dataScopeDeptOnly')" :value="3" />
            <ElOption :label="$t('permission.dataScopeSelfOnly')" :value="4" />
          </ElSelect>
        </ElFormItem>

        <ElFormItem :label="$t('common.remark')" prop="remark">
          <ElInput v-model="formData.remark" type="textarea" :rows="2" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>
      </template>

      <ElFormItem :label="$t('common.sort')" prop="order">
        <ElInputNumber v-model="formData.order" :min="0" :max="9999" style="width: 100%" />
      </ElFormItem>

      <ElFormItem :label="$t('permission.minUserType')" prop="min_user_type">
        <ElSelect v-model="formData.min_user_type" :placeholder="$t('common.pleaseSelect')" style="width: 100%">
          <ElOption :label="$t('login.roles.super')" :value="0" />
          <ElOption :label="$t('login.roles.admin')" :value="1" />
          <ElOption :label="$t('permission.deptAdmin')" :value="2" />
          <ElOption :label="$t('permission.allUsers')" :value="3" />
        </ElSelect>
      </ElFormItem>

      <!-- 菜单配置 -->
      <template v-if="formData.menu_type === 0">
        <ElDivider>{{ $t('permission.menuConfig') }}</ElDivider>

        <ElRow :gutter="20">
          <ElCol :span="12">
            <ElFormItem :label="$t('permission.isHide')">
              <ElSwitch v-model="formData.isHide" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem :label="$t('permission.isHideTab')">
              <ElSwitch v-model="formData.isHideTab" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem :label="$t('permission.keepAlive')">
              <ElSwitch v-model="formData.keepAlive" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem :label="$t('permission.fixedTab')">
              <ElSwitch v-model="formData.fixedTab" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem :label="$t('permission.isFullPage')">
              <ElSwitch v-model="formData.isFullPage" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem :label="$t('permission.isIframe')">
              <ElSwitch v-model="formData.isIframe" />
            </ElFormItem>
          </ElCol>
        </ElRow>

        <ElFormItem :label="$t('permission.externalLink')" prop="link">
          <ElInput v-model="formData.link" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>

        <ElFormItem :label="$t('permission.activePath')" prop="activePath">
          <ElInput v-model="formData.activePath" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>
      </template>
    </ElForm>

    <template #footer>
      <ElButton round @click="handleClose">{{ $t('common.cancel') }}</ElButton>
      <ElButton round type="primary" :loading="submitLoading" @click="handleSubmit">{{ $t('common.confirm') }}</ElButton>
    </template>
  </ElDrawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { fetchPermissionTree, addPermission, updatePermission } from '@/api/system/permission'
import type { PermissionInfo, PermissionTree } from '@/api/system/permission'
import { IconTypeEnum } from '@/enums/appEnum'

interface Props {
  modelValue: boolean
  dialogType: 'add' | 'edit'
  permissionData?: Partial<PermissionInfo>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const { t } = useI18n()

const formRef = ref<FormInstance>()
const formLoading = ref(false)
const submitLoading = ref(false)
const permissionTree = ref<PermissionTree[]>([])

const formData = ref({
  menu_type: 0,
  parent_id: undefined as string | undefined,
  name: '',
  title: '',
  path: '',
  component: '',
  icon: '',
  order: 999,
  min_user_type: 3,
  authTitle: '',
  authMark: '',
  api_path: '',
  api_method: [] as string[],
  data_scope: 4,
  remark: '',
  isHide: false,
  isHideTab: false,
  keepAlive: false,
  fixedTab: false,
  isFullPage: false,
  isIframe: false,
  link: '',
  activePath: ''
})

const formRules = computed(() => ({
  menu_type: [{ required: true, message: t('common.pleaseSelect'), trigger: 'change' }],
  name: [
    { validator: (_: any, value: string, callback: Function) => {
      // API 类型不需要权限名称
      if (formData.value.menu_type === 2) {
        callback()
        return
      }
      if (!value) {
        callback(new Error(t('common.pleaseInput')))
        return
      }
      if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(value)) {
        callback(new Error(t('permission.namePattern')))
        return
      }
      callback()
    }, trigger: 'blur' }
  ],
  title: [{ required: true, message: t('common.pleaseInput'), trigger: 'blur' }],
  path: [{ validator: (_: any, value: string, callback: Function) => {
    // 菜单类型且非 iframe 时路由路径必填
    if (formData.value.menu_type === 0 && !formData.value.isIframe && !value) callback(new Error(t('permission.pathRequired')))
    else callback()
  }, trigger: 'blur' }],
  authTitle: [{ validator: (_: any, value: string, callback: Function) => {
    if (formData.value.menu_type === 1 && !value) callback(new Error(t('permission.authTitleRequired')))
    else callback()
  }, trigger: 'blur' }],
  authMark: [{ validator: (_: any, value: string, callback: Function) => {
    if (formData.value.menu_type === 1 && !value) callback(new Error(t('permission.authMarkRequired')))
    else callback()
  }, trigger: 'blur' }],
  api_path: [{ validator: (_: any, value: string, callback: Function) => {
    if (formData.value.menu_type === 2 && !value) callback(new Error(t('permission.apiPathRequired')))
    else callback()
  }, trigger: 'blur' }],
  api_method: [{ validator: (_: any, value: string[], callback: Function) => {
    if (formData.value.menu_type === 2 && (!value || value.length === 0)) callback(new Error(t('permission.apiMethodRequired')))
    else callback()
  }, trigger: 'change' }],
  link: [{ validator: (_: any, value: string, callback: Function) => {
    // iframe 类型时 link 必填
    if (formData.value.menu_type === 0 && formData.value.isIframe && !value) callback(new Error(t('permission.linkRequired')))
    else callback()
  }, trigger: 'blur' }]
}))

// 翻译权限树节点标题
const translateTitle = (title: string | undefined): string => {
  if (!title) return ''
  if (title.startsWith('menus.')) {
    return t(title)
  }
  return title
}

// 递归处理权限树，翻译标题
const processPermissionTree = (nodes: PermissionTree[]): PermissionTree[] => {
  return nodes.map(node => ({
    ...node,
    title: translateTitle(node.title),
    children: node.children ? processPermissionTree(node.children) : []
  }))
}

// 计算属性：翻译后的权限树数据
const permissionTreeData = computed(() => {
  return processPermissionTree(permissionTree.value)
})

const drawerTitle = computed(() => props.dialogType === 'add' ? t('buttons.addPermission') : t('buttons.updatePermission'))

const loadPermissions = async () => {
  try {
    formLoading.value = true
    const res = await fetchPermissionTree()
    if (res.success && res.data) {
      const filterMenus = (perms: PermissionTree[]): PermissionTree[] => {
        return perms.filter(p => p.menu_type === 0).map(p => ({
          ...p,
          children: p.children ? filterMenus(p.children) : []
        }))
      }
      permissionTree.value = filterMenus(res.data.result || [])
    }
  } catch (e) {
    console.error('加载权限数据失败:', e)
  } finally {
    formLoading.value = false
  }
}

const handleOpen = () => {
  loadPermissions()
  if (props.dialogType === 'edit' && props.permissionData) {
    // 处理 api_method，确保是数组
    let apiMethod: string[] = []
    if (props.permissionData.api_method) {
      if (Array.isArray(props.permissionData.api_method)) {
        apiMethod = props.permissionData.api_method
      } else if (typeof props.permissionData.api_method === 'string') {
        apiMethod = [props.permissionData.api_method]
      }
    }
    
    formData.value = {
      menu_type: props.permissionData.menu_type || 0,
      parent_id: props.permissionData.parent_id,
      name: props.permissionData.name || '',
      title: props.permissionData.title || '',
      path: props.permissionData.path || '',
      component: props.permissionData.component || '',
      icon: props.permissionData.icon || '',
      order: props.permissionData.order || 999,
      min_user_type: props.permissionData.min_user_type ?? 3,
      authTitle: props.permissionData.authTitle || '',
      authMark: props.permissionData.authMark || '',
      api_path: props.permissionData.api_path || '',
      api_method: apiMethod,
      data_scope: props.permissionData.data_scope ?? 4,
      remark: props.permissionData.remark || '',
      isHide: props.permissionData.isHide || false,
      isHideTab: props.permissionData.isHideTab || false,
      keepAlive: props.permissionData.keepAlive || false,
      fixedTab: props.permissionData.fixedTab || false,
      isFullPage: props.permissionData.isFullPage || false,
      isIframe: props.permissionData.isIframe || false,
      link: props.permissionData.link || '',
      activePath: props.permissionData.activePath || ''
    }
  } else {
    resetForm()
    if (props.permissionData?.parent_id) formData.value.parent_id = props.permissionData.parent_id
    if (props.permissionData?.menu_type !== undefined) formData.value.menu_type = props.permissionData.menu_type
  }
}

const resetForm = () => {
  formData.value = {
    menu_type: 0,
    parent_id: undefined,
    name: '',
    title: '',
    path: '',
    component: '',
    icon: '',
    order: 999,
    min_user_type: 3,
    authTitle: '',
    authMark: '',
    api_path: '',
    api_method: [],
    data_scope: 4,
    remark: '',
    isHide: false,
    isHideTab: false,
    keepAlive: false,
    fixedTab: false,
    isFullPage: false,
    isIframe: false,
    link: '',
    activePath: ''
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    submitLoading.value = true

    const submitData: any = { ...formData.value }

    // iframe 类型自动生成 path（如果没有填写）
    if (submitData.menu_type === 0 && submitData.isIframe && !submitData.path) {
      // 使用 name 或时间戳生成唯一路径
      const pathName = submitData.name || `iframe_${Date.now()}`
      submitData.path = `/outside/iframe/${pathName}`
    }

    // 根据类型清理不需要的字段
    if (submitData.menu_type === 0) {
      delete submitData.authTitle
      delete submitData.authMark
      delete submitData.api_path
      delete submitData.api_method
      delete submitData.data_scope
      delete submitData.remark
    } else if (submitData.menu_type === 1) {
      delete submitData.path
      delete submitData.component
      delete submitData.icon
      delete submitData.api_path
      delete submitData.api_method
      delete submitData.data_scope
      delete submitData.remark
      delete submitData.isHide
      delete submitData.isHideTab
      delete submitData.keepAlive
      delete submitData.fixedTab
      delete submitData.isFullPage
      delete submitData.isIframe
      delete submitData.link
      delete submitData.activePath
    } else if (submitData.menu_type === 2) {
      delete submitData.name
      delete submitData.path
      delete submitData.component
      delete submitData.icon
      delete submitData.authTitle
      delete submitData.authMark
      delete submitData.isHide
      delete submitData.isHideTab
      delete submitData.keepAlive
      delete submitData.fixedTab
      delete submitData.isFullPage
      delete submitData.isIframe
      delete submitData.link
      delete submitData.activePath
    }

    // 清理空值
    // 编辑模式：空字符串转为 null（允许清空字段）
    // 新增模式：删除空值字段
    Object.keys(submitData).forEach(key => {
      // 保留 api_method 数组和 data_scope
      if (key === 'api_method' || key === 'data_scope') return
      
      if (props.dialogType === 'edit') {
        // 编辑模式：空字符串转为 null，保留字段以便后端更新
        if (submitData[key] === '' || submitData[key] === undefined) {
          submitData[key] = null
        }
      } else {
        // 新增模式：删除空值字段
        if (submitData[key] === '' || submitData[key] === null || submitData[key] === undefined) {
          delete submitData[key]
        }
      }
    })

    let res
    if (props.dialogType === 'add') {
      res = await addPermission(submitData)
    } else {
      res = await updatePermission(props.permissionData!.id!, submitData)
    }

    if (res.success) {
      ElMessage.success(t('common.operationSuccess'))
      emit('success')
      handleClose()
    } else {
      ElMessage.error(res.msg || t('common.updateFailed'))
    }
  } catch (e) {
    console.error('提交失败:', e)
  } finally {
    submitLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.permission-drawer {
  :deep(.el-drawer) {
    border-radius: 12px 0 0 12px;
  }
}
</style>
