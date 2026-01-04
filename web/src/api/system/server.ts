/**
 * 服务器信息管理 API
 */

import request from '@/utils/http'

/** CPU信息接口 */
export interface CpuInfo {
  /** 核心数 */
  cpu_num?: number
  /** 物理核心数 */
  physical_cpu_num?: number
  /** CPU用户使用率 */
  used?: number
  /** CPU系统使用率 */
  sys?: number
  /** CPU当前空闲率 */
  free?: number
  /** CPU总使用率 */
  total_usage?: number
  /** CPU型号 */
  cpu_model?: string
  /** CPU频率 */
  cpu_freq?: string
}

/** 内存信息接口 */
export interface MemoryInfo {
  /** 内存总量 */
  total?: string
  /** 已用内存 */
  used?: string
  /** 剩余内存 */
  free?: string
  /** 可用内存 */
  available?: string
  /** 使用率 */
  usage?: number
  /** 交换内存总量 */
  swap_total?: string
  /** 交换内存已用 */
  swap_used?: string
  /** 交换内存剩余 */
  swap_free?: string
  /** 交换内存使用率 */
  swap_usage?: number
}

/** 系统信息接口 */
export interface SystemInfo {
  /** 服务器IP */
  computer_ip?: string
  /** 服务器名称 */
  computer_name?: string
  /** 系统架构 */
  os_arch?: string
  /** 操作系统 */
  os_name?: string
  /** 系统版本 */
  os_version?: string
  /** 项目路径 */
  user_dir?: string
  /** 系统启动时间 */
  boot_time?: string
  /** 系统运行时长 */
  system_uptime?: string
  /** 当前时间 */
  current_time?: string
}

/** Python信息接口 */
export interface PythonInfo extends MemoryInfo {
  /** Python名称 */
  name?: string
  /** Python版本 */
  version?: string
  /** 启动时间 */
  start_time?: string
  /** 运行时长 */
  run_time?: string
  /** 安装路径 */
  home?: string
}

/** 系统磁盘信息接口 */
export interface SystemFiles {
  /** 盘符路径 */
  dir_name?: string
  /** 盘符类型 */
  sys_type_name?: string
  /** 文件类型 */
  type_name?: string
  /** 挂载点 */
  mount_point?: string
  /** 总大小 */
  total?: string
  /** 已经使用量 */
  used?: string
  /** 剩余大小 */
  free?: string
  /** 资源的使用率 */
  usage?: string
}

/** 网络信息接口 */
export interface NetworkInfo {
  /** 网卡名称 */
  interface_name?: string
  /** IP地址 */
  ip_address?: string
  /** MAC地址 */
  mac_address?: string
  /** 发送字节数 */
  bytes_sent?: string
  /** 接收字节数 */
  bytes_recv?: string
  /** 发送包数 */
  packets_sent?: number
  /** 接收包数 */
  packets_recv?: number
}

/** 磁盘IO信息接口 */
export interface DiskIOInfo {
  /** 读取次数 */
  read_count?: number
  /** 写入次数 */
  write_count?: number
  /** 读取字节数 */
  read_bytes?: string
  /** 写入字节数 */
  write_bytes?: string
  /** 读取时间(ms) */
  read_time?: number
  /** 写入时间(ms) */
  write_time?: number
}

/** 服务器信息响应接口 */
export interface ServerInfoData {
  /** CPU相关信息 */
  cpu?: CpuInfo
  /** Python相关信息 */
  python?: PythonInfo
  /** 內存相关信息 */
  memory?: MemoryInfo
  /** 服务器相关信息 */
  system?: SystemInfo
  /** 磁盘相关信息 */
  system_files?: SystemFiles[]
  /** 网络相关信息 */
  network?: NetworkInfo[]
  /** 磁盘IO信息 */
  disk_io?: DiskIOInfo
}

/**
 * 获取服务器信息
 * @returns 服务器信息数据
 */
export const fetchServerInfo = () =>
  request.get<ServerInfoData>({
    url: '/api/server'
  })
