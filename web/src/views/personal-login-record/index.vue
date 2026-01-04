<template>
  <div class="page-content personal-login-record">
    <div class="content">
      <!-- 左侧用户信息卡片 -->
      <div class="left-wrap">
        <div class="user-wrap box-style">
          <div class="profile-header">
            <img class="bg" src="@imgs/user/bg.webp" />
            <div class="avatar-section">
              <!-- 如果有头像则使用el-avatar显示头像，否则使用el-avatar显示用户名作为文字头像 -->
              <ElAvatar :size="60" :src="getAvatarUrl(userInfo?.avatar) || '@imgs/user/avatar.webp'">
                {{ userInfo?.username }}
              </ElAvatar>
              <div class="status-indicator"></div>
            </div>
          </div>

          <div class="profile-info">
            <h2 class="name">{{ userInfo?.nickname || userInfo?.username }}</h2>
            <p class="position">{{
              userInfo?.department_name || t('personalLoginRecord.noDepartment')
            }}</p>

            <div class="quick-stats">
              <div class="stat-item">
                <span class="stat-number">{{ totalRecords }}</span>
                <span class="stat-label">{{ t('personalLoginRecord.totalLogins') }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ onlineCount }}</span>
                <span class="stat-label">{{ t('personalLoginRecord.onlineSessions') }}</span>
              </div>
            </div>
          </div>

          <div class="outer-info">
            <div class="info-item">
              <i class="iconfont-sys">&#xe72e;</i>
              <span>{{ userInfo?.email || t('personalLoginRecord.noEmail') }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe6f5;</i>
              <span>{{ userInfo?.phone || t('personalLoginRecord.noPhone') }}</span>
            </div>
            <div class="info-item">
              <i class="iconfont-sys">&#xe811;</i>
              <span>{{ userInfo?.department_name || t('personalLoginRecord.noDepartment') }}</span>
            </div>
          </div>
        </div>

        <!-- 快捷导航卡片 -->
        <div class="quick-nav box-style">
          <div class="nav-header">
            <h3>快捷导航</h3>
          </div>
          <div class="nav-items">
            <div class="nav-item" @click="goToUserCenter">
              <div class="nav-icon user-icon">
                <i class="iconfont-sys">&#xe7ae;</i>
              </div>
              <div class="nav-content">
                <h4>个人中心</h4>
                <p>管理个人信息</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
            <div class="nav-item" @click="goToOperationRecord">
              <div class="nav-icon operation-icon">
                <i class="iconfont-sys">&#xe694;</i>
              </div>
              <div class="nav-content">
                <h4>操作记录</h4>
                <p>查看操作日志</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
            <div class="nav-item" @click="goToMyNotification">
              <div class="nav-icon notification-icon">
                <i class="iconfont-sys">&#xe6c2;</i>
              </div>
              <div class="nav-content">
                <h4>我的通知</h4>
                <p>查看系统通知</p>
              </div>
              <i class="iconfont-sys arrow">&#xe66c;</i>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录记录 -->
      <div class="right-wrap">
        <div class="login-records box-style">
          <div class="section-header">
            <div class="header-title">
              <div class="title-icon">
                <i class="iconfont-sys">&#xe6e0;</i>
              </div>
              <h3>{{ t('personalLoginRecord.loginRecords') }}</h3>
            </div>
            <div class="header-actions">
              <ElButton @click="refreshData" :loading="loading" size="small" type="primary" plain>
                <i class="iconfont-sys mr-1">&#xe6cf;</i>
                {{ t('common.refresh') }}
              </ElButton>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <ElForm :model="searchForm" inline>
              <ElFormItem :label="t('personalLoginRecord.timeRange')">
                <ElDatePicker
                  v-model="dateRange"
                  type="datetimerange"
                  :range-separator="t('common.to')"
                  :start-placeholder="t('common.startTime')"
                  :end-placeholder="t('common.endTime')"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                  @change="handleDateRangeChange"
                />
              </ElFormItem>
              <ElFormItem :label="t('personalLoginRecord.status')" class="w-30%">
                <ElSelect
                  v-model="searchForm.status"
                  :placeholder="t('common.pleaseSelect')"
                  clearable
                  class="w-full"
                  @change="handleSearch"
                >
                  <ElOption :label="t('personalLoginRecord.success')" :value="1" />
                  <ElOption :label="t('personalLoginRecord.failed')" :value="0" />
                </ElSelect>
              </ElFormItem>
              <ElFormItem>
                <ElButton type="primary" @click="handleSearch">
                  {{ t('table.searchBar.search') }}
                </ElButton>
                <ElButton @click="handleReset">
                  {{ t('table.searchBar.reset') }}
                </ElButton>
              </ElFormItem>
            </ElForm>
          </div>

          <!-- 登录记录表格 -->
          <ArtTable
            :data="data"
            :loading="loading"
            :columns="columns"
            :pagination="pagination"
            row-key="id"
            @pagination:size-change="handleSizeChange"
            @pagination:current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted, h } from 'vue'
  import { useRouter } from 'vue-router'
  import {
    ElMessageBox,
    ElButton,
    ElTag,
    ElForm,
    ElFormItem,
    ElDatePicker,
    ElSelect,
    ElOption
  } from 'element-plus'
  import { useI18n } from 'vue-i18n'
  import { useTable } from '@/composables/useTable'
  import { useUserStore } from '@/store/modules/user'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import {
    fetchPersonalLoginLogList,
    fetchPersonalLogout,
    type LoginLogInfo,
    type PersonalLoginLogSearchParams
  } from '@/api/system/log'
  import { getAvatarUrl } from '@/utils'

  defineOptions({ name: 'PersonalLoginRecord' })

  const router = useRouter()
  const { t } = useI18n()
  const userStore = useUserStore()

  // 用户信息
  const userInfo = computed(() => userStore.getUserInfo)

  // 搜索表单
  const searchForm = ref<PersonalLoginLogSearchParams>({
    status: undefined
  })

  // 日期范围
  const dateRange = ref<[string, string] | undefined>(undefined)

  // 统计信息
  const totalRecords = ref(0)
  const onlineCount = computed(() => {
    return data.value.filter((record: LoginLogInfo) => record.online).length
  })

  const {
    columns,
    data,
    loading,
    pagination,
    getData,
    searchParams,
    handleSizeChange,
    handleCurrentChange,
    refreshData
  } = useTable({
    // 核心配置
    core: {
      apiFn: fetchPersonalLoginLogList,
      apiParams: {
        page: 1,
        pageSize: 10
      },
      // 配置分页字段映射
      paginationKey: {
        current: 'page',
        size: 'pageSize'
      },
      columnsFactory: () => [
        {
          prop: 'login_ip',
          label: t('personalLoginRecord.loginIp'),
          align: 'center',
          width: 140
        },
        {
          prop: 'login_location',
          label: t('personalLoginRecord.location'),
          align: 'center',
          width: 120
        },
        {
          prop: 'browser',
          label: t('personalLoginRecord.browser'),
          align: 'center',
          showOverflowTooltip: true
        },
        {
          prop: 'os',
          label: t('personalLoginRecord.os'),
          align: 'center',
          width: 120
        },
        {
          prop: 'status',
          label: t('personalLoginRecord.status'),
          align: 'center',
          width: 100,
          formatter: (row: LoginLogInfo) => {
            const isSuccess = String(row.status) === '1'
            return h(ElTag, { type: isSuccess ? 'success' : 'danger' }, () =>
              isSuccess ? t('personalLoginRecord.success') : t('personalLoginRecord.failed')
            )
          }
        },
        {
          prop: 'online',
          label: t('personalLoginRecord.onlineStatus'),
          align: 'center',
          width: 100,
          formatter: (row: LoginLogInfo) => {
            return h(ElTag, { type: row.online ? 'success' : 'info' }, () =>
              row.online ? t('personalLoginRecord.online') : t('personalLoginRecord.offline')
            )
          }
        },
        {
          prop: 'created_at',
          label: t('personalLoginRecord.loginTime'),
          align: 'center',
          width: 180,
          formatter: (row: LoginLogInfo) => {
            return new Date(row.created_at).toLocaleString('zh-CN')
          }
        },
        {
          prop: 'actions',
          label: t('common.actions'),
          width: 120,
          align: 'center',
          fixed: 'right',
          formatter: (row: LoginLogInfo) => {
            return h('div', { class: 'flex gap-2 justify-center' }, [
              h(
                ElButton,
                {
                  type: 'danger',
                  size: 'small',
                  disabled: !row.online,
                  onClick: () => handleLogout(row)
                },
                () => [t('personalLoginRecord.forceLogout')]
              )
            ])
          }
        }
      ]
    },
    hooks: {
      onSuccess: (data, response) => {
        totalRecords.value = response.total || 0
      }
    }
  })

  // 处理日期范围变化
  const handleDateRangeChange = (dates: [string, string] | undefined) => {
    if (dates) {
      searchForm.value.startTime = dates[0]
      searchForm.value.endTime = dates[1]
    } else {
      searchForm.value.startTime = undefined
      searchForm.value.endTime = undefined
    }
    handleSearch()
  }

  // 搜索处理
  const handleSearch = () => {
    Object.assign(searchParams, searchForm.value)
    getData()
  }

  // 重置搜索
  const handleReset = () => {
    searchForm.value = {
      status: undefined,
      startTime: undefined,
      endTime: undefined
    }
    dateRange.value = undefined
    Object.assign(searchParams, searchForm.value)
    getData()
  }

  // 强制退出
  const handleLogout = async (row: LoginLogInfo) => {
    try {
      await ElMessageBox.confirm(t('personalLoginRecord.logoutConfirm'), t('common.warning'), {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      })

      await fetchPersonalLogout(row.session_id)
      refreshData()
    } catch (error: any) {
      if (error !== 'cancel') {
        console.error('强制退出失败:', error)
      }
    }
  }

  // 跳转到个人中心
  const goToUserCenter = () => {
    router.push('/user-center')
  }

  // 跳转到操作记录
  const goToOperationRecord = () => {
    router.push('/personal-operation-record')
  }

  // 跳转到我的通知
  const goToMyNotification = () => {
    router.push('/my-notification')
  }

  onMounted(() => {
    // getData()
  })
</script>

<style lang="scss" scoped>
  .personal-login-record {
    .content {
      display: flex;
      gap: 20px;
      height: 100%;

      .left-wrap {
        width: 300px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        gap: 20px;

        .user-wrap {
          padding: 0;
          border-radius: 12px;
          overflow: hidden;
          background: var(--el-bg-color);

          .profile-header {
            position: relative;
            height: 120px;

            .bg {
              width: 100%;
              height: 100%;
              object-fit: cover;
            }

            .avatar-section {
              position: absolute;
              bottom: -30px;
              left: 50%;
              transform: translateX(-50%);

              .avatar {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
              }

              .status-indicator {
                position: absolute;
                bottom: 5px;
                right: 5px;
                width: 12px;
                height: 12px;
                background: var(--el-color-success);
                border: 2px solid white;
                border-radius: 50%;
              }
            }
          }

          .profile-info {
            padding: 40px 20px 20px;
            text-align: center;

            .name {
              margin: 0 0 5px;
              font-size: 18px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }

            .position {
              margin: 0 0 20px;
              color: var(--el-text-color-regular);
              font-size: 14px;
            }

            .quick-stats {
              display: flex;
              justify-content: space-around;
              padding: 15px 0;
              border-top: 1px solid var(--el-border-color-light);

              .stat-item {
                text-align: center;

                .stat-number {
                  display: block;
                  font-size: 20px;
                  font-weight: 600;
                  color: var(--el-color-primary);
                  margin-bottom: 5px;
                }

                .stat-label {
                  font-size: 12px;
                  color: var(--el-text-color-regular);
                }
              }
            }
          }

          .outer-info {
            padding: 0 20px 20px;

            .info-item {
              display: flex;
              align-items: center;
              padding: 8px 0;
              color: var(--el-text-color-regular);

              i {
                margin-right: 10px;
                color: var(--el-color-primary);
                font-size: 16px;
              }

              span {
                font-size: 14px;
              }
            }
          }
        }

        .quick-nav {
          background: var(--el-bg-color);
          border-radius: 12px;
          padding: 20px;

          .nav-header {
            margin-bottom: 16px;

            h3 {
              margin: 0;
              font-size: 16px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }
          }

          .nav-items {
            display: flex;
            flex-direction: column;
            gap: 12px;

            .nav-item {
              display: flex;
              align-items: center;
              padding: 16px;
              background: var(--el-fill-color-light);
              border: 1px solid var(--el-border-color);
              border-radius: 10px;
              cursor: pointer;
              transition: all 0.3s ease;

              &:hover {
                border-color: var(--el-color-primary-light-5);
                background: var(--el-color-primary-light-9);
                transform: translateX(4px);
              }

              .nav-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
                margin-right: 12px;

                i {
                  font-size: 18px;
                  color: #fff;
                }

                &.user-icon {
                  background: rgb(var(--art-primary));
                }

                &.operation-icon {
                  background: rgb(var(--art-warning));
                }

                &.notification-icon {
                  background: rgb(var(--art-info));
                }
              }

              .nav-content {
                flex: 1;

                h4 {
                  margin: 0 0 4px;
                  font-size: 14px;
                  font-weight: 600;
                  color: var(--el-text-color-primary);
                }

                p {
                  margin: 0;
                  font-size: 12px;
                  color: var(--el-text-color-regular);
                }
              }

              .arrow {
                font-size: 14px;
                color: var(--el-text-color-secondary);
                transition: transform 0.3s ease;
              }

              &:hover .arrow {
                transform: translateX(4px);
                color: var(--el-color-primary);
              }
            }
          }
        }
      }

      .right-wrap {
        flex: 1;

        .login-records {
          padding: 20px;
          border-radius: 12px;
          background: var(--el-bg-color);

          .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--el-border-color-lighter);

            .header-title {
              display: flex;
              align-items: center;
              gap: 12px;

              .title-icon {
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: rgb(var(--art-primary));

                i {
                  font-size: 18px;
                  color: #fff;
                }
              }

              h3 {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
            }
          }

          .search-bar {
            margin-bottom: 20px;
            padding: 15px;
            background: var(--el-fill-color-light);
            border-radius: 8px;

            :deep(.el-form-item) {
              margin-bottom: 0;
            }
          }
        }
      }
    }
  }

  @media (max-width: 768px) {
    .personal-login-record .content {
      flex-direction: column;

      .left-wrap {
        width: 100%;
      }
    }
  }
</style>
