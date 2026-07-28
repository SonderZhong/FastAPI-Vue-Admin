<template>
  <div class="art-full-height">
    <ElCard class="art-table-card h-full" shadow="never">
      <ArtSearchBar
        :model-value="searchForm"
        @update:model-value="Object.assign(searchForm, $event)"
        :items="searchItems"
        @search="handleSearch"
        @reset="handleReset"
      />

      <ArtTableHeader v-model:columns="columns" :loading="loading" @refresh="fetchData">
        <template #left>
          <ElSpace wrap>
            <ElButton v-auth="'tenant:btn:add'" type="primary" :icon="Plus" @click="openCreate">
              {{ $t('tenant.createTenant') }}
            </ElButton>
            <ElButton
              v-auth="'tenant:btn:delete'"
              type="danger"
              :icon="Delete"
              :disabled="selectedIds.length === 0"
              @click="handleBatchDelete"
            >
              {{ $t('buttons.batchDelete') }}
            </ElButton>
          </ElSpace>
        </template>
      </ArtTableHeader>

      <ArtTable
        row-key="id"
        :data="tableData"
        :columns="columns"
        :pagination="pagination"
        :loading="loading"
        fit
        @selection-change="handleSelectionChange"
        @pagination:current-change="handlePageChange"
        @pagination:size-change="handleSizeChange"
      >
        <template #status="{ row }">
          <ElTag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
          </ElTag>
        </template>

        <template #allow_register="{ row }">
          <ElSwitch
            v-model="row.allow_register"
            :loading="row._toggleLoading"
            inline-prompt
            :active-text="$t('common.enabled')"
            :inactive-text="$t('common.disabled')"
            @change="handleToggleRegister(row)"
          />
        </template>

        <template #invite_code="{ row }">
          <div v-if="row.invite_code" class="flex min-w-0 items-center gap-2">
            <ElText truncated class="max-w-[180px]">{{ row.invite_code }}</ElText>
            <ElButton link type="primary" size="small" @click="copyText(row.invite_code)">
              {{ $t('common.copy') }}
            </ElButton>
          </div>
          <ElButton v-else link type="primary" size="small" @click="handleGenerateInviteCode(row)">
            {{ $t('tenant.generateInviteCode') }}
          </ElButton>
        </template>

        <template #remark="{ row }">
          <span class="text-[var(--el-text-color-secondary)]">{{ row.remark || '-' }}</span>
        </template>

        <template #action="{ row }">
          <ElSpace wrap :size="4">
            <ElButton
              v-auth="'tenant:btn:update'"
              type="primary"
              link
              size="small"
              @click="openEdit(row)"
            >
              {{ $t('buttons.edit') }}
            </ElButton>
            <ElButton
              v-auth="'tenant:btn:delete'"
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              {{ $t('buttons.delete') }}
            </ElButton>
            <ElButton link type="primary" size="small" @click="handleViewInvite(row)">
              {{ $t('tenant.inviteInfo') }}
            </ElButton>
          </ElSpace>
        </template>
      </ArtTable>
    </ElCard>

    <ElDialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? $t('tenant.createTenant') : $t('tenant.editTenant')"
      width="560px"
      @closed="resetForm"
    >
      <ElForm ref="formRef" :model="formData" :rules="formRules" label-width="110px">
        <ElFormItem :label="$t('tenant.tenantName')" prop="name">
          <ElInput v-model="formData.name" :placeholder="$t('common.pleaseInput')" />
        </ElFormItem>
        <ElFormItem :label="$t('tenant.tenantCode')" prop="code">
          <ElInput
            v-model="formData.code"
            :disabled="dialogMode === 'edit'"
            :placeholder="$t('common.pleaseInput')"
          />
        </ElFormItem>
        <ElFormItem :label="$t('common.status')" prop="status">
          <ElRadioGroup v-model="formData.status">
            <ElRadio :label="1">{{ $t('common.enabled') }}</ElRadio>
            <ElRadio :label="0">{{ $t('common.disabled') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem :label="$t('common.remark')" prop="remark">
          <ElInput
            v-model="formData.remark"
            type="textarea"
            :rows="4"
            :placeholder="$t('common.pleaseInput')"
          />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <ElButton @click="dialogVisible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">{{
          $t('common.confirm')
        }}</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="inviteDialogVisible" :title="$t('tenant.inviteInfo')" width="560px">
      <div
        class="mb-4 rounded-lg border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-lighter)] px-4 py-3"
      >
        <div class="text-xs text-[var(--el-text-color-secondary)]">{{
          $t('tenant.currentTenant')
        }}</div>
        <div class="mt-1 text-sm font-medium text-[var(--el-text-color-primary)]">
          {{ currentInviteTenantName || '-' }}
        </div>
      </div>

      <ElDescriptions :column="1" border>
        <ElDescriptionsItem :label="$t('tenant.inviteCode')">
          <div class="flex items-center gap-2">
            <ElText>{{ inviteInfo.invite_code || $t('tenant.notGenerated') }}</ElText>
            <ElButton
              v-if="inviteInfo.invite_code"
              link
              type="primary"
              size="small"
              @click="copyText(inviteInfo.invite_code)"
            >
              {{ $t('common.copy') }}
            </ElButton>
          </div>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('tenant.inviteLink')">
          <div class="flex items-center gap-2">
            <ElText truncated class="max-w-[320px]">{{
              inviteInfo.invite_link || $t('tenant.notGenerated')
            }}</ElText>
            <ElButton
              v-if="inviteInfo.invite_link"
              link
              type="primary"
              size="small"
              @click="copyText(inviteInfo.invite_link)"
            >
              {{ $t('common.copy') }}
            </ElButton>
          </div>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('tenant.allowRegister')">
          <ElTag :type="inviteInfo.allow_register ? 'success' : 'info'" size="small">
            {{ inviteInfo.allow_register ? $t('common.enabled') : $t('common.disabled') }}
          </ElTag>
        </ElDescriptionsItem>
      </ElDescriptions>

      <template #footer>
        <ElButton @click="inviteDialogVisible = false">{{ $t('buttons.close') }}</ElButton>
        <ElButton type="primary" @click="handleRegenerateInviteCode">{{
          $t('tenant.regenerateInviteCode')
        }}</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
  import { onMounted, reactive, ref } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { Delete, Plus } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtTableHeader from '@/components/core/tables/art-table-header/index.vue'
  import type { ColumnOption } from '@/types'
  import {
    addTenant,
    deleteTenant,
    deleteTenantList,
    fetchInviteCodeInfo,
    fetchTenantList,
    generateInviteCode,
    toggleInviteRegister,
    type TenantInfo,
    updateTenant
  } from '@/api/system/tenant'

  defineOptions({ name: 'Tenant' })

  const { t } = useI18n()

  type TenantRow = TenantInfo & {
    _toggleLoading?: boolean
  }

  const searchForm = reactive({
    name: '',
    code: '',
    status: undefined as number | undefined
  })

  const searchItems = [
    {
      key: 'name',
      type: 'input',
      label: t('tenant.tenantName'),
      props: {
        placeholder: t('common.pleaseInput'),
        clearable: true
      }
    },
    {
      key: 'code',
      type: 'input',
      label: t('tenant.tenantCode'),
      props: {
        placeholder: t('common.pleaseInput'),
        clearable: true
      }
    },
    {
      key: 'status',
      type: 'select',
      label: t('common.status'),
      props: {
        placeholder: t('common.pleaseSelect'),
        clearable: true,
        options: [
          { label: t('common.enabled'), value: 1 },
          { label: t('common.disabled'), value: 0 }
        ]
      }
    }
  ]

  const loading = ref(false)
  const selectedIds = ref<string[]>([])
  const tableData = ref<TenantRow[]>([])
  const pagination = reactive({
    current: 1,
    size: 10,
    total: 0
  })

  const columns = ref<ColumnOption[]>([
    { type: 'selection', width: 55 },
    { prop: 'name', label: t('tenant.tenantName'), minWidth: 180 },
    { prop: 'code', label: t('tenant.tenantCode'), minWidth: 140 },
    { prop: 'status', label: t('common.status'), width: 90, useSlot: true },
    { prop: 'allow_register', label: t('tenant.allowRegister'), width: 120, useSlot: true },
    { prop: 'invite_code', label: t('tenant.inviteCode'), minWidth: 220, useSlot: true },
    { prop: 'remark', label: t('common.remark'), minWidth: 180, useSlot: true },
    { prop: 'created_at', label: t('common.createTime'), width: 180 },
    { prop: 'action', label: t('common.actions'), width: 220, fixed: 'right', useSlot: true }
  ])

  const fetchData = async () => {
    loading.value = true
    try {
      const res = await fetchTenantList({
        page: pagination.current,
        pageSize: pagination.size,
        name: searchForm.name || undefined,
        code: searchForm.code || undefined,
        status: searchForm.status
      })

      tableData.value = (res.data?.result || []).map((item) => ({
        ...item,
        _toggleLoading: false
      }))
      pagination.total = res.data?.total || 0

      if (pagination.current > 1 && tableData.value.length === 0) {
        pagination.current -= 1
        await fetchData()
      }
    } finally {
      loading.value = false
    }
  }

  const handleSearch = async () => {
    pagination.current = 1
    await fetchData()
  }

  const handleReset = async () => {
    Object.assign(searchForm, {
      name: '',
      code: '',
      status: undefined
    })
    pagination.current = 1
    await fetchData()
  }

  const handlePageChange = async (page: number) => {
    pagination.current = page
    await fetchData()
  }

  const handleSizeChange = async (size: number) => {
    pagination.size = size
    pagination.current = 1
    await fetchData()
  }

  const handleSelectionChange = (rows: TenantRow[]) => {
    selectedIds.value = rows.map((item) => item.id)
  }

  const dialogVisible = ref(false)
  const dialogMode = ref<'add' | 'edit'>('add')
  const submitLoading = ref(false)
  const currentId = ref('')
  const formRef = ref<FormInstance>()

  const createDefaultForm = () => ({
    name: '',
    code: '',
    status: 1,
    remark: ''
  })

  const formData = reactive(createDefaultForm())

  const formRules: FormRules = {
    name: [{ required: true, message: t('tenant.tenantNameRequired'), trigger: 'blur' }],
    code: [{ required: true, message: t('tenant.tenantCodeRequired'), trigger: 'blur' }]
  }

  const resetForm = () => {
    Object.assign(formData, createDefaultForm())
    currentId.value = ''
    formRef.value?.clearValidate()
  }

  const openCreate = () => {
    dialogMode.value = 'add'
    resetForm()
    dialogVisible.value = true
  }

  const openEdit = (row: TenantInfo) => {
    dialogMode.value = 'edit'
    resetForm()
    currentId.value = row.id
    Object.assign(formData, {
      name: row.name,
      code: row.code,
      status: row.status,
      remark: row.remark || ''
    })
    dialogVisible.value = true
  }

  const handleSubmit = async () => {
    if (!formRef.value) {
      return
    }

    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) {
      return
    }

    submitLoading.value = true
    try {
      const payload = {
        name: formData.name,
        code: formData.code,
        status: formData.status,
        remark: formData.remark || undefined
      }

      if (dialogMode.value === 'add') {
        await addTenant(payload)
        ElMessage.success(t('common.addSuccess'))
      } else {
        await updateTenant(currentId.value, payload)
        ElMessage.success(t('common.updateSuccess'))
      }

      dialogVisible.value = false
      await fetchData()
    } finally {
      submitLoading.value = false
    }
  }

  const handleDelete = async (row: TenantInfo) => {
    await ElMessageBox.confirm(t('tenant.deleteConfirm', { name: row.name }), t('common.tips'), {
      type: 'warning'
    })

    await deleteTenant(row.id)
    ElMessage.success(t('common.deleteSuccess'))
    await fetchData()
  }

  const handleBatchDelete = async () => {
    await ElMessageBox.confirm(
      t('tenant.batchDeleteConfirm', { count: selectedIds.value.length }),
      t('common.tips'),
      { type: 'warning' }
    )

    await deleteTenantList(selectedIds.value)
    selectedIds.value = []
    ElMessage.success(t('common.deleteSuccess'))
    await fetchData()
  }

  const inviteDialogVisible = ref(false)
  const currentInviteTenantId = ref('')
  const currentInviteTenantName = ref('')
  const inviteInfo = reactive({
    invite_code: null as string | null,
    invite_link: null as string | null,
    allow_register: false
  })

  const resetInviteInfo = () => {
    Object.assign(inviteInfo, {
      invite_code: null,
      invite_link: null,
      allow_register: false
    })
  }

  const openInviteDialog = (row: TenantInfo) => {
    currentInviteTenantId.value = row.id
    currentInviteTenantName.value = row.name
    inviteDialogVisible.value = true
  }

  const handleGenerateInviteCode = async (row: TenantInfo) => {
    openInviteDialog(row)
    const res = await generateInviteCode(row.id)
    Object.assign(inviteInfo, res.data)
    ElMessage.success(t('tenant.inviteCodeGenerated'))
    await fetchData()
  }

  const handleViewInvite = async (row: TenantInfo) => {
    openInviteDialog(row)
    resetInviteInfo()
    try {
      const res = await fetchInviteCodeInfo(row.id)
      Object.assign(inviteInfo, res.data)
    } catch {
      ElMessage.warning(t('tenant.noInviteCode'))
    }
  }

  const handleRegenerateInviteCode = async () => {
    if (!currentInviteTenantId.value) {
      return
    }

    const res = await generateInviteCode(currentInviteTenantId.value)
    Object.assign(inviteInfo, res.data)
    ElMessage.success(t('tenant.inviteCodeRegenerated'))
    await fetchData()
  }

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      ElMessage.success(t('common.copySuccess'))
    } catch {
      ElMessage.error(t('common.copyFailed'))
    }
  }

  const handleToggleRegister = async (row: TenantRow) => {
    row._toggleLoading = true
    try {
      await toggleInviteRegister(row.id)
      if (currentInviteTenantId.value === row.id) {
        inviteInfo.allow_register = row.allow_register
      }
      ElMessage.success(
        row.allow_register ? t('tenant.allowRegisterEnabled') : t('tenant.allowRegisterDisabled')
      )
    } catch {
      row.allow_register = !row.allow_register
      ElMessage.error(t('common.updateFailed'))
    } finally {
      row._toggleLoading = false
    }
  }

  onMounted(async () => {
    await fetchData()
  })
</script>
