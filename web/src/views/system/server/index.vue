<template>
  <div class="server-monitor">
    <!-- 刷新按钮和当前时间 -->
    <div class="flex justify-between items-center mb-4">
      <div v-if="serverInfo.system?.current_time" class="flex items-center text-gray-600">
        <ElIcon class="mr-2"><Clock /></ElIcon>
        <span>{{ $t('server.system.currentTime') }}: {{ serverInfo.system.current_time }}</span>
      </div>
      <ElButton
        v-auth="'server:btn:info'"
        @click="handleRefresh"
        type="primary"
        :loading="loading"
        v-ripple
      >
        <ElIcon><Refresh /></ElIcon>
        {{ $t('buttons.refresh') }}
      </ElButton>
    </div>

    <!-- 系统信息卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <!-- 服务器信息 -->
      <ElCard class="server-info-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-blue-500" :size="20"><Monitor /></ElIcon>
            <span class="font-semibold text-base">{{ $t('server.system.title') }}</span>
          </div>
        </template>
        <div v-loading="loading" class="space-y-3">
          <div class="info-item">
            <span class="label">{{ $t('server.system.serverName') }}</span>
            <span class="value">{{ serverInfo.system?.computer_name || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.system.serverIp') }}</span>
            <span class="value">{{ serverInfo.system?.computer_ip || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.system.os') }}</span>
            <span class="value">{{ serverInfo.system?.os_name || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.system.arch') }}</span>
            <span class="value">{{ serverInfo.system?.os_arch || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.system.bootTime') }}</span>
            <span class="value">{{ serverInfo.system?.boot_time || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.system.uptime') }}</span>
            <ElTag type="success" size="small">{{
              serverInfo.system?.system_uptime || 'N/A'
            }}</ElTag>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.system.projectPath') }}</span>
            <ElTooltip :content="serverInfo.system?.user_dir || 'N/A'" placement="top">
              <span class="value truncate">{{ serverInfo.system?.user_dir || 'N/A' }}</span>
            </ElTooltip>
          </div>
        </div>
      </ElCard>

      <!-- Python运行环境信息 -->
      <ElCard class="python-info-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-green-500" :size="20">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path
                  fill="currentColor"
                  d="M499.2 0c-54.4 0-105.6 5.12-145.92 14.336-119.808 27.648-140.8 84.992-140.8 191.488V307.2h281.6v35.84H212.48c-81.92 0-153.6 49.152-176.128 142.848-25.6 107.52-26.624 174.08 0 287.744 19.456 84.992 66.56 142.848 148.48 142.848h96.256V793.6c0-93.184 80.896-174.08 176.128-174.08h281.6c78.848 0 140.8-64 140.8-142.848V205.824c0-76.8-64.512-134.144-140.8-153.6-48.128-12.288-98.304-17.408-145.92-17.408zM368.64 122.88c29.696 0 53.248 24.576 53.248 54.272 0 30.72-23.552 54.272-53.248 54.272-28.672 0-53.248-23.552-53.248-54.272 0-29.696 24.576-54.272 53.248-54.272z"
                />
                <path
                  fill="currentColor"
                  d="M890.88 307.2c-20.48-83.968-58.368-142.848-140.8-142.848h-107.52v117.76c0 97.28-82.944 180.224-176.128 180.224H184.32c-78.848 0-140.8 65.536-140.8 142.848v281.6c0 76.8 66.56 122.88 140.8 142.848 89.088 23.552 174.08 28.672 281.6 0 71.68-19.456 140.8-58.368 140.8-142.848V785.408h-281.6v-35.84H747.52c81.92 0 112.64-56.32 140.8-142.848 29.696-89.088 28.672-174.08 0-287.744zM655.36 901.12c28.672 0 53.248 23.552 53.248 54.272 0 29.696-24.576 54.272-53.248 54.272-29.696 0-53.248-24.576-53.248-54.272 0-30.72 23.552-54.272 53.248-54.272z"
                />
              </svg>
            </ElIcon>
            <span class="font-semibold text-base">{{ $t('server.python.title') }}</span>
          </div>
        </template>
        <div v-loading="loading" class="space-y-3">
          <div class="info-item">
            <span class="label">{{ $t('server.python.name') }}</span>
            <span class="value">{{ serverInfo.python?.name || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.python.version') }}</span>
            <ElTag type="success" size="small">{{ serverInfo.python?.version || 'N/A' }}</ElTag>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.python.startTime') }}</span>
            <span class="value">{{ serverInfo.python?.start_time || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.python.runTime') }}</span>
            <ElTag type="warning" size="small">{{ serverInfo.python?.run_time || 'N/A' }}</ElTag>
          </div>
          <div class="info-item">
            <span class="label">{{ $t('server.python.home') }}</span>
            <ElTooltip :content="serverInfo.python?.home || 'N/A'" placement="top">
              <span class="value truncate">{{ serverInfo.python?.home || 'N/A' }}</span>
            </ElTooltip>
          </div>
        </div>
      </ElCard>
    </div>

    <!-- CPU 和内存信息 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <!-- CPU信息 -->
      <ElCard class="cpu-info-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-purple-500" :size="20"><Cpu /></ElIcon>
            <span class="font-semibold text-base">{{ $t('server.cpu.title') }}</span>
          </div>
        </template>
        <div v-loading="loading">
          <div class="grid grid-cols-2 gap-3 mb-4">
            <div class="info-item">
              <span class="label">{{ $t('server.cpu.cores') }}</span>
              <ElTag type="info" size="small"
                >{{ serverInfo.cpu?.cpu_num || 0 }} {{ $t('server.cpu.coreUnit') }}</ElTag
              >
            </div>
            <div class="info-item">
              <span class="label">{{ $t('server.cpu.physicalCores') }}</span>
              <ElTag type="info" size="small"
                >{{ serverInfo.cpu?.physical_cpu_num || 0 }} {{ $t('server.cpu.coreUnit') }}</ElTag
              >
            </div>
          </div>
          <div v-if="serverInfo.cpu?.cpu_model" class="info-item mb-3">
            <span class="label">{{ $t('server.cpu.model') }}</span>
            <ElTooltip :content="serverInfo.cpu.cpu_model" placement="top">
              <span class="value truncate text-xs">{{ serverInfo.cpu.cpu_model }}</span>
            </ElTooltip>
          </div>
          <div v-if="serverInfo.cpu?.cpu_freq" class="info-item mb-4">
            <span class="label">{{ $t('server.cpu.freq') }}</span>
            <span class="value text-xs">{{ serverInfo.cpu.cpu_freq }}</span>
          </div>
          <div class="space-y-4">
            <div class="usage-item">
              <div class="flex justify-between mb-2">
                <span class="text-sm text-gray-600">{{ $t('server.cpu.totalUsage') }}</span>
                <span class="text-sm font-semibold text-purple-600"
                  >{{ serverInfo.cpu?.total_usage?.toFixed(2) || 0 }}%</span
                >
              </div>
              <ElProgress
                :percentage="Number(serverInfo.cpu?.total_usage?.toFixed(2)) || 0"
                :stroke-width="12"
                color="#a855f7"
              />
            </div>
            <div class="usage-item">
              <div class="flex justify-between mb-2">
                <span class="text-sm text-gray-600">{{ $t('server.cpu.userUsage') }}</span>
                <span class="text-sm font-semibold text-blue-600"
                  >{{ serverInfo.cpu?.used?.toFixed(2) || 0 }}%</span
                >
              </div>
              <ElProgress
                :percentage="Number(serverInfo.cpu?.used?.toFixed(2)) || 0"
                :stroke-width="12"
              />
            </div>
            <div class="usage-item">
              <div class="flex justify-between mb-2">
                <span class="text-sm text-gray-600">{{ $t('server.cpu.systemUsage') }}</span>
                <span class="text-sm font-semibold text-green-600"
                  >{{ serverInfo.cpu?.sys?.toFixed(2) || 0 }}%</span
                >
              </div>
              <ElProgress
                :percentage="Number(serverInfo.cpu?.sys?.toFixed(2)) || 0"
                :stroke-width="12"
                status="success"
              />
            </div>
          </div>
        </div>
      </ElCard>

      <!-- 内存信息 -->
      <ElCard class="memory-info-card">
        <template #header>
          <div class="flex items-center">
            <ElIcon class="mr-2 text-orange-500" :size="20"><Memo /></ElIcon>
            <span class="font-semibold text-base">{{ $t('server.memory.title') }}</span>
          </div>
        </template>
        <div v-loading="loading">
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="stat-box">
              <div class="stat-label">{{ $t('server.memory.total') }}</div>
              <div class="stat-value text-blue-600">{{ serverInfo.memory?.total || 'N/A' }}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">{{ $t('server.memory.used') }}</div>
              <div class="stat-value text-red-600">{{ serverInfo.memory?.used || 'N/A' }}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">{{ $t('server.memory.available') }}</div>
              <div class="stat-value text-green-600">{{
                serverInfo.memory?.available || 'N/A'
              }}</div>
            </div>
          </div>
          <div class="usage-item mb-4">
            <div class="flex justify-between mb-2">
              <span class="text-sm text-gray-600">{{ $t('server.memory.usage') }}</span>
              <span class="text-sm font-semibold" :class="getUsageClass(serverInfo.memory?.usage)">
                {{ serverInfo.memory?.usage?.toFixed(2) || 0 }}%
              </span>
            </div>
            <ElProgress
              :percentage="Number(serverInfo.memory?.usage?.toFixed(2)) || 0"
              :stroke-width="12"
              :status="getProgressStatus(serverInfo.memory?.usage)"
            />
          </div>
          <!-- 交换内存 -->
          <div v-if="serverInfo.memory?.swap_total && serverInfo.memory.swap_total !== '0 B'">
            <ElDivider>{{ $t('server.memory.swapMemory') }}</ElDivider>
            <div class="grid grid-cols-3 gap-3 mb-3">
              <div class="stat-box-small">
                <div class="stat-label-small">{{ $t('server.memory.total') }}</div>
                <div class="stat-value-small">{{ serverInfo.memory.swap_total }}</div>
              </div>
              <div class="stat-box-small">
                <div class="stat-label-small">{{ $t('server.memory.used') }}</div>
                <div class="stat-value-small">{{ serverInfo.memory.swap_used }}</div>
              </div>
              <div class="stat-box-small">
                <div class="stat-label-small">{{ $t('server.memory.free') }}</div>
                <div class="stat-value-small">{{ serverInfo.memory.swap_free }}</div>
              </div>
            </div>
            <div class="usage-item">
              <div class="flex justify-between mb-2">
                <span class="text-sm text-gray-600">{{ $t('server.memory.usage') }}</span>
                <span
                  class="text-sm font-semibold"
                  :class="getUsageClass(serverInfo.memory?.swap_usage)"
                >
                  {{ serverInfo.memory?.swap_usage?.toFixed(2) || 0 }}%
                </span>
              </div>
              <ElProgress
                :percentage="Number(serverInfo.memory?.swap_usage?.toFixed(2)) || 0"
                :stroke-width="10"
                :status="getProgressStatus(serverInfo.memory?.swap_usage)"
              />
            </div>
          </div>
        </div>
      </ElCard>
    </div>

    <!-- Python内存使用 -->
    <ElCard class="python-memory-card mb-4">
      <template #header>
        <div class="flex items-center">
          <ElIcon class="mr-2 text-cyan-500" :size="20"><DataLine /></ElIcon>
          <span class="font-semibold text-base">{{ $t('server.python.memoryTitle') }}</span>
        </div>
      </template>
      <div v-loading="loading">
        <div class="grid grid-cols-3 gap-3 mb-4">
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.python.totalMemory') }}</div>
            <div class="stat-value text-blue-600">{{ serverInfo.python?.total || 'N/A' }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.python.usedMemory') }}</div>
            <div class="stat-value text-red-600">{{ serverInfo.python?.used || 'N/A' }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.python.freeMemory') }}</div>
            <div class="stat-value text-green-600">{{ serverInfo.python?.free || 'N/A' }}</div>
          </div>
        </div>
        <div class="usage-item">
          <div class="flex justify-between mb-2">
            <span class="text-sm text-gray-600">{{ $t('server.python.memoryUsage') }}</span>
            <span class="text-sm font-semibold" :class="getUsageClass(serverInfo.python?.usage)">
              {{ serverInfo.python?.usage?.toFixed(2) || 0 }}%
            </span>
          </div>
          <ElProgress
            :percentage="Number(serverInfo.python?.usage?.toFixed(2)) || 0"
            :stroke-width="12"
            :status="getProgressStatus(serverInfo.python?.usage)"
          />
        </div>
      </div>
    </ElCard>

    <!-- 磁盘信息 -->
    <ElCard class="disk-info-card mb-4">
      <template #header>
        <div class="flex items-center">
          <ElIcon class="mr-2 text-indigo-500" :size="20"><FolderOpened /></ElIcon>
          <span class="font-semibold text-base">{{ $t('server.disk.title') }}</span>
        </div>
      </template>
      <div v-loading="loading">
        <div v-if="serverInfo.system_files && serverInfo.system_files.length > 0" class="space-y-4">
          <div v-for="(disk, index) in serverInfo.system_files" :key="index" class="disk-item">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center">
                <ElIcon class="mr-2 text-blue-500" :size="18"><Folder /></ElIcon>
                <span class="font-medium">{{ disk.type_name }}</span>
                <ElTag class="ml-2" size="small" type="info">{{ disk.sys_type_name }}</ElTag>
              </div>
              <span class="text-sm text-gray-600">{{ disk.dir_name }}</span>
            </div>
            <div class="grid grid-cols-3 gap-3 mb-3">
              <div class="stat-box-small">
                <div class="stat-label-small">{{ $t('server.disk.total') }}</div>
                <div class="stat-value-small">{{ disk.total }}</div>
              </div>
              <div class="stat-box-small">
                <div class="stat-label-small">{{ $t('server.disk.used') }}</div>
                <div class="stat-value-small">{{ disk.used }}</div>
              </div>
              <div class="stat-box-small">
                <div class="stat-label-small">{{ $t('server.disk.free') }}</div>
                <div class="stat-value-small">{{ disk.free }}</div>
              </div>
            </div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm text-gray-600">{{ $t('server.disk.usage') }}</span>
              <span
                class="text-sm font-semibold"
                :class="getUsageClass(parseFloat(disk.usage || '0'))"
              >
                {{ disk.usage }}
              </span>
            </div>
            <ElProgress
              :percentage="parseFloat(disk.usage || '0')"
              :stroke-width="10"
              :status="getProgressStatus(parseFloat(disk.usage || '0'))"
            />
          </div>
        </div>
        <ElEmpty v-else :description="$t('server.disk.noDisk')" />
      </div>
    </ElCard>

    <!-- 磁盘IO信息 -->
    <ElCard v-if="serverInfo.disk_io" class="disk-io-card mb-4">
      <template #header>
        <div class="flex items-center">
          <ElIcon class="mr-2 text-pink-500" :size="20"><Reading /></ElIcon>
          <span class="font-semibold text-base">{{ $t('server.diskIO.title') }}</span>
        </div>
      </template>
      <div v-loading="loading">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.diskIO.readCount') }}</div>
            <div class="stat-value text-blue-600">{{
              serverInfo.disk_io.read_count?.toLocaleString() || 0
            }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.diskIO.writeCount') }}</div>
            <div class="stat-value text-orange-600">{{
              serverInfo.disk_io.write_count?.toLocaleString() || 0
            }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.diskIO.readBytes') }}</div>
            <div class="stat-value text-green-600">{{
              serverInfo.disk_io.read_bytes || 'N/A'
            }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.diskIO.writeBytes') }}</div>
            <div class="stat-value text-red-600">{{ serverInfo.disk_io.write_bytes || 'N/A' }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.diskIO.readTime') }}</div>
            <div class="stat-value text-purple-600">{{ serverInfo.disk_io.read_time || 0 }} ms</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">{{ $t('server.diskIO.writeTime') }}</div>
            <div class="stat-value text-indigo-600"
              >{{ serverInfo.disk_io.write_time || 0 }} ms</div
            >
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 网络信息 -->
    <ElCard v-if="serverInfo.network && serverInfo.network.length > 0" class="network-card">
      <template #header>
        <div class="flex items-center">
          <ElIcon class="mr-2 text-teal-500" :size="20"><Connection /></ElIcon>
          <span class="font-semibold text-base">{{ $t('server.network.title') }}</span>
        </div>
      </template>
      <div v-loading="loading">
        <div class="space-y-4">
          <div v-for="(net, index) in serverInfo.network" :key="index" class="network-item">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center">
                <ElIcon class="mr-2 text-teal-500" :size="18"><Connection /></ElIcon>
                <span class="font-medium text-base">{{ net.interface_name }}</span>
              </div>
              <ElTag v-if="net.ip_address && net.ip_address !== 'N/A'" type="success" size="small">
                {{ net.ip_address }}
              </ElTag>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
              <div class="info-item-small">
                <span class="label-small">{{ $t('server.network.macAddress') }}</span>
                <span class="value-small">{{ net.mac_address || 'N/A' }}</span>
              </div>
              <div class="info-item-small">
                <span class="label-small">{{ $t('server.network.bytesSent') }}</span>
                <span class="value-small text-blue-600">{{ net.bytes_sent || 'N/A' }}</span>
              </div>
              <div class="info-item-small">
                <span class="label-small">{{ $t('server.network.bytesRecv') }}</span>
                <span class="value-small text-green-600">{{ net.bytes_recv || 'N/A' }}</span>
              </div>
              <div class="info-item-small">
                <span class="label-small">{{ $t('server.network.packetsSent') }}</span>
                <span class="value-small">{{ net.packets_sent?.toLocaleString() || 0 }}</span>
              </div>
              <div class="info-item-small">
                <span class="label-small">{{ $t('server.network.packetsRecv') }}</span>
                <span class="value-small">{{ net.packets_recv?.toLocaleString() || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import {
    ElMessage,
    ElIcon,
    ElButton,
    ElCard,
    ElTag,
    ElProgress,
    ElEmpty,
    ElTooltip,
    ElDivider
  } from 'element-plus'
  import {
    Refresh,
    Monitor,
    Cpu,
    Memo,
    DataLine,
    FolderOpened,
    Folder,
    Reading,
    Connection,
    Clock
  } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { fetchServerInfo, type ServerInfoData } from '@/api/system/server'

  defineOptions({ name: 'ServerMonitor' })

  const { t } = useI18n()

  // 响应式数据
  const loading = ref(false)
  const serverInfo = ref<ServerInfoData>({})

  // 获取服务器信息
  const getServerInfo = async () => {
    loading.value = true
    try {
      const response = await fetchServerInfo()
      if (response?.success) {
        serverInfo.value = response.data || {}
      } else {
        ElMessage.error(response?.msg || t('server.messages.fetchError'))
      }
    } catch (error) {
      console.error('获取服务器信息失败:', error)
      ElMessage.error(t('server.messages.fetchError'))
    } finally {
      loading.value = false
    }
  }

  // 刷新服务器信息
  const handleRefresh = async () => {
    await getServerInfo()
    ElMessage.success(t('server.messages.refreshSuccess'))
  }

  // 根据使用率获取样式类
  const getUsageClass = (usage?: number) => {
    if (!usage) return 'text-gray-600'
    if (usage >= 90) return 'text-red-600'
    if (usage >= 70) return 'text-orange-600'
    return 'text-green-600'
  }

  // 根据使用率获取进度条状态
  const getProgressStatus = (usage?: number) => {
    if (!usage) return undefined
    if (usage >= 90) return 'exception'
    if (usage >= 70) return 'warning'
    return 'success'
  }

  // 初始化
  onMounted(() => {
    getServerInfo()
  })
</script>

<style lang="scss" scoped>
  .server-monitor {
    padding: 20px;

    .el-card {
      border-radius: 12px;
      transition: all 0.3s ease;
      box-shadow: var(--art-card-shadow);
      border: 1px solid var(--art-card-border);

      &:hover {
        transform: translateY(-2px);
        box-shadow: var(--art-box-shadow-sm);
      }

      :deep(.el-card__header) {
        padding: 16px 20px;
        border-bottom: 1px solid var(--art-border-color);
        background: var(--art-main-bg-color);
      }

      :deep(.el-card__body) {
        padding: 20px;
      }
    }

    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;

      .label {
        font-size: 14px;
        color: var(--art-text-gray-600);
        font-weight: 500;
      }

      .value {
        font-size: 14px;
        color: var(--art-text-gray-800);
        font-weight: 600;
        max-width: 60%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .info-item-small {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .label-small {
        font-size: 12px;
        color: var(--art-text-gray-600);
      }

      .value-small {
        font-size: 13px;
        color: var(--art-text-gray-800);
        font-weight: 600;
      }
    }

    .stat-box {
      background: rgb(var(--art-grey100));
      padding: 12px;
      border-radius: 8px;
      text-align: center;
      border: 1px solid var(--art-card-border);

      .stat-label {
        font-size: 12px;
        color: var(--art-text-gray-600);
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 18px;
        font-weight: bold;
      }
    }

    .stat-box-small {
      background: rgb(var(--art-grey100));
      padding: 8px;
      border-radius: 6px;
      text-align: center;
      border: 1px solid var(--art-card-border);

      .stat-label-small {
        font-size: 11px;
        color: var(--art-text-gray-600);
        margin-bottom: 4px;
      }

      .stat-value-small {
        font-size: 14px;
        font-weight: bold;
        color: var(--art-text-gray-800);
      }
    }

    .usage-item {
      margin-top: 16px;
    }

    .disk-item,
    .network-item {
      padding: 16px;
      background: rgb(var(--art-grey100));
      border-radius: 8px;
      border: 1px solid var(--art-card-border);

      &:hover {
        background: rgb(var(--art-hoverColor));
        border-color: var(--art-border-color);
      }
    }

    // 卡片颜色主题 - 使用项目主题色
    .server-info-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-primary));
        color: rgb(var(--art-primary));

        .el-icon {
          color: rgb(var(--art-primary));
        }
      }
    }

    .python-info-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-success));
        color: rgb(var(--art-success));

        .el-icon {
          color: rgb(var(--art-success));
        }
      }
    }

    .cpu-info-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-secondary));
        color: rgb(var(--art-secondary));

        .el-icon {
          color: rgb(var(--art-secondary));
        }
      }
    }

    .memory-info-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-warning));
        color: rgb(var(--art-warning));

        .el-icon {
          color: rgb(var(--art-warning));
        }
      }
    }

    .python-memory-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-info));
        color: rgb(var(--art-info));

        .el-icon {
          color: rgb(var(--art-info));
        }
      }
    }

    .disk-info-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-error));
        color: rgb(var(--art-error));

        .el-icon {
          color: rgb(var(--art-error));
        }
      }
    }

    .disk-io-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-danger));
        color: rgb(var(--art-danger));

        .el-icon {
          color: rgb(var(--art-danger));
        }
      }
    }

    .network-card {
      :deep(.el-card__header) {
        background: rgb(var(--art-bg-secondary));
        color: rgb(var(--art-secondary));

        .el-icon {
          color: rgb(var(--art-secondary));
        }
      }
    }
  }
</style>
