<template>
  <div class="art-full-height">
    <ElContainer class="h-full">
      <!-- 左侧部门树 -->
      <ElAside width="300px" class="dept-aside">
        <ElCard shadow="never" class="h-full dept-card">
          <template #header>
            <div class="dept-header">
              <span class="font-medium">{{ $t('department.structure', '部门结构') }}</span>
              <ElButton
                v-auth="'department:btn:add'"
                type="primary"
                size="small"
                round
                :icon="Plus"
                @click="showDialog('add')"
              >
                {{ $t('department.add', '新增') }}
              </ElButton>
            </div>
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
                      v-if="data.children && data.children.length > 0"
                      :value="data.children.length"
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

      <!-- 右侧详情 -->
      <ElMain class="main-content">
        <template v-if="selectedDepartment">
          <!-- 工具栏 -->
          <div class="toolbar">
            <div class="toolbar-left">
              <ElBreadcrumb separator="/">
                <ElBreadcrumbItem v-for="item in breadcrumbItems" :key="item.id">
                  {{ item.name }}
                </ElBreadcrumbItem>
              </ElBreadcrumb>
            </div>
            <div class="toolbar-right">
              <ElButton
                v-auth="'department:btn:add'"
                type="success"
                size="small"
                round
                :icon="Plus"
                @click="addSubDepartment(selectedDepartment)"
              >
                {{ $t('department.addSub', '添加下属') }}
              </ElButton>
              <ElButton
                v-auth="'department:btn:update'"
                type="primary"
                size="small"
                round
                :icon="Edit"
                @click="showDialog('edit', selectedDepartment)"
              >
                {{ $t('buttons.edit', '编辑') }}
              </ElButton>
              <ElButton
                v-auth="'department:btn:delete'"
                type="danger"
                size="small"
                round
                :icon="Delete"
                @click="deleteDepartment(selectedDepartment)"
              >
                {{ $t('buttons.delete', '删除') }}
              </ElButton>
            </div>
          </div>

          <!-- 详情卡片 -->
          <ElCard class="detail-card" shadow="never">
            <!-- 基本信息 -->
            <div class="info-section">
              <div class="section-title">
                <ElIcon class="mr-2"><InfoFilled /></ElIcon>
                {{ $t('department.basicInfo', '基本信息') }}
              </div>
              <ElRow :gutter="24">
                <ElCol :span="8">
                  <div class="info-item">
                    <span class="info-label">{{ $t('department.name', '部门名称') }}</span>
                    <span class="info-value">{{ selectedDepartment.name }}</span>
                  </div>
                </ElCol>
                <ElCol :span="8">
                  <div class="info-item">
                    <span class="info-label">{{ $t('department.principal', '负责人') }}</span>
                    <span class="info-value">{{ selectedDepartment.principal || '-' }}</span>
                  </div>
                </ElCol>
                <ElCol :span="8">
                  <div class="info-item">
                    <span class="info-label">{{ $t('common.status', '状态') }}</span>
                    <ElTag :type="selectedDepartment.status === 0 ? 'success' : 'info'" size="small">
                      {{ selectedDepartment.status === 0 ? '正常' : '停用' }}
                    </ElTag>
                  </div>
                </ElCol>
                <ElCol :span="8">
                  <div class="info-item">
                    <span class="info-label">{{ $t('department.phone', '联系电话') }}</span>
                    <span class="info-value">{{ selectedDepartment.phone || '-' }}</span>
                  </div>
                </ElCol>
                <ElCol :span="8">
                  <div class="info-item">
                    <span class="info-label">{{ $t('department.email', '邮箱') }}</span>
                    <span class="info-value">{{ selectedDepartment.email || '-' }}</span>
                  </div>
                </ElCol>
                <ElCol :span="8">
                  <div class="info-item">
                    <span class="info-label">{{ $t('department.sort', '排序') }}</span>
                    <span class="info-value">{{ selectedDepartment.sort }}</span>
                  </div>
                </ElCol>
                <ElCol :span="24" v-if="selectedDepartment.remark">
                  <div class="info-item">
                    <span class="info-label">{{ $t('common.remark', '备注') }}</span>
                    <span class="info-value">{{ selectedDepartment.remark }}</span>
                  </div>
                </ElCol>
              </ElRow>
            </div>

            <!-- 时间信息 -->
            <div class="info-section">
              <div class="section-title">
                <ElIcon class="mr-2"><Clock /></ElIcon>
                {{ $t('department.timeInfo', '时间信息') }}
              </div>
              <ElRow :gutter="24">
                <ElCol :span="12">
                  <div class="info-item">
                    <span class="info-label">{{ $t('common.createTime', '创建时间') }}</span>
                    <span class="info-value text-gray-500 text-sm">{{ formatDate(selectedDepartment.created_at) }}</span>
                  </div>
                </ElCol>
                <ElCol :span="12">
                  <div class="info-item">
                    <span class="info-label">{{ $t('common.updateTime', '更新时间') }}</span>
                    <span class="info-value text-gray-500 text-sm">{{ formatDate(selectedDepartment.updated_at) }}</span>
                  </div>
                </ElCol>
              </ElRow>
            </div>

            <!-- 子部门 -->
            <div class="info-section" v-if="getDepartmentChildren(selectedDepartment.id).length > 0">
              <div class="section-title">
                <ElIcon class="mr-2"><OfficeBuilding /></ElIcon>
                {{ $t('department.subDepartments', '子部门') }}
                <ElBadge :value="getDepartmentChildren(selectedDepartment.id).length" type="primary" class="ml-2" />
              </div>
              <div class="sub-dept-list">
                <div
                  v-for="child in getDepartmentChildren(selectedDepartment.id)"
                  :key="child.id"
                  class="sub-dept-item"
                  @click="selectDepartment(child)"
                >
                  <ElIcon class="text-blue-500 mr-2"><OfficeBuilding /></ElIcon>
                  <span>{{ child.name }}</span>
                  <ElIcon class="arrow-icon"><ArrowRight /></ElIcon>
                </div>
              </div>
            </div>
          </ElCard>
        </template>

        <!-- 未选择部门的提示 -->
        <div v-else class="empty-state">
          <ElEmpty :description="$t('department.selectTip', '请选择左侧部门查看详情')">
            <template #image>
              <ElIcon :size="60" class="text-gray-300"><OfficeBuilding /></ElIcon>
            </template>
          </ElEmpty>
        </div>
      </ElMain>
    </ElContainer>

    <!-- 部门编辑抽屉 -->
    <DepartmentDrawer
      v-model="dialogVisible"
      :dialog-type="dialogType"
      :department-data="currentDepartmentData"
      @success="handleDialogSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessageBox, ElMessage, ElTree } from 'element-plus'
import { Search, OfficeBuilding, Plus, Edit, Delete, InfoFilled, Clock, ArrowRight } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { fetchDepartmentTree, deleteDepartment as deleteDepartmentApi } from '@/api/system/department'
import DepartmentDrawer from './modules/department-drawer.vue'
import type { DepartmentInfo, DepartmentTree } from '@/typings/department'

defineOptions({ name: 'Department' })

const { t: $t } = useI18n()

// 弹窗相关
const dialogType = ref<'add' | 'edit'>('add')
const dialogVisible = ref(false)
const currentDepartmentData = ref<Partial<DepartmentInfo>>({})

// 树形组件相关
const treeRef = ref<InstanceType<typeof ElTree>>()
const treeFilterText = ref('')
const departmentTree = ref<DepartmentTree[]>([])
const selectedDepartment = ref<DepartmentInfo | null>(null)

const treeProps = { children: 'children', label: 'name' }

// 面包屑路径
const breadcrumbItems = computed(() => {
  if (!selectedDepartment.value) return []
  
  const items: { id: string; name: string }[] = []
  const findPath = (nodes: DepartmentTree[], targetId: string, path: { id: string; name: string }[]): boolean => {
    for (const node of nodes) {
      const currentPath = [...path, { id: node.id, name: node.name }]
      if (node.id === targetId) {
        items.push(...currentPath)
        return true
      }
      if (node.children && findPath(node.children, targetId, currentPath)) {
        return true
      }
    }
    return false
  }
  
  findPath(departmentTree.value, selectedDepartment.value.id, [])
  return items
})

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getDepartmentChildren = (departmentId: string): DepartmentInfo[] => {
  const findChildren = (nodes: DepartmentTree[]): DepartmentInfo[] => {
    for (const node of nodes) {
      if (node.id === departmentId) {
        return node.children || []
      }
      if (node.children) {
        const result = findChildren(node.children)
        if (result.length > 0) return result
      }
    }
    return []
  }
  return findChildren(departmentTree.value)
}

const filterNode = (value: string, data: any) => {
  if (!value) return true
  return data.name.includes(value)
}

watch(treeFilterText, (val) => {
  treeRef.value?.filter(val)
})

const handleNodeClick = (data: DepartmentInfo) => {
  selectedDepartment.value = data
}

const selectDepartment = (department: DepartmentInfo) => {
  selectedDepartment.value = department
  treeRef.value?.setCurrentKey(department.id)
}

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

const showDialog = (type: 'add' | 'edit', row?: DepartmentInfo) => {
  dialogType.value = type
  currentDepartmentData.value = row || {}
  nextTick(() => {
    dialogVisible.value = true
  })
}

const addSubDepartment = (parentDepartment: DepartmentInfo) => {
  dialogType.value = 'add'
  currentDepartmentData.value = {
    parent_id: parentDepartment.id
  } as Partial<DepartmentInfo>
  nextTick(() => {
    dialogVisible.value = true
  })
}

const deleteDepartment = (row: DepartmentInfo) => {
  ElMessageBox.confirm(
    `确定要删除部门「${row.name}」吗？`,
    '删除确认',
    { type: 'warning' }
  ).then(async () => {
    try {
      const response = await deleteDepartmentApi(row.id)
      if (response.success) {
        ElMessage.success('删除成功')
        if (selectedDepartment.value?.id === row.id) {
          selectedDepartment.value = null
        }
        await loadDepartmentTree()
      } else {
        ElMessage.error(response.msg || '删除失败')
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleDialogSubmit = async () => {
  dialogVisible.value = false
  currentDepartmentData.value = {}
  await loadDepartmentTree()
}

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

.dept-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-card {
  flex: 1;
  margin: 12px;
  overflow: auto;
  
  :deep(.el-card__body) {
    padding: 0;
  }
}

.info-section {
  padding: 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  &:last-child {
    border-bottom: none;
  }
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.info-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.info-label {
  width: 80px;
  flex-shrink: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.info-value {
  flex: 1;
  color: var(--el-text-color-primary);
  font-size: 13px;
  word-break: break-all;
}

.sub-dept-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sub-dept-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: var(--el-color-primary-light-9);
    
    .arrow-icon {
      transform: translateX(4px);
      color: var(--el-color-primary);
    }
  }
  
  .arrow-icon {
    margin-left: auto;
    color: var(--el-text-color-secondary);
    transition: all 0.2s;
  }
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
