/**
 * 工作台 API
 */

import request from '@/utils/http'

/**
 * 工作台统计数据接口
 */
export interface DashboardStatistics {
  /** 未读通知数 */
  unreadNotifications: number
  /** 全部通知数 */
  totalNotifications: number
  /** 今日登录次数 */
  todayLogins: number
  /** 今日操作次数 */
  todayOperations: number
}

/**
 * 获取工作台统计数据
 * @returns 统计数据
 */
export const fetchDashboardStatistics = () => {
  return request.get<DashboardStatistics>({
    url: '/api/dashboard/statistics'
  })
}

/**
 * 登录统计数据接口
 */
export interface LoginStatistics {
  /** 操作系统分布 */
  osDistribution: Array<{ name: string; value: number }>
  /** 浏览器分布 */
  browserDistribution: Array<{ name: string; value: number }>
  /** 登录地区分布 */
  locationDistribution: Array<{ name: string; value: number }>
}

/**
 * 获取登录统计数据（操作系统、浏览器、地区分布）
 * @returns 登录统计数据
 */
export const fetchLoginStatistics = () => {
  return request.get<LoginStatistics>({
    url: '/api/dashboard/login-statistics'
  })
}

/**
 * 登录趋势数据接口
 */
export interface LoginTrend {
  /** 日期列表 */
  dates: string[]
  /** 登录次数列表 */
  loginCounts: number[]
  /** 地区趋势系列 */
  locationSeries: Array<{
    name: string
    data: number[]
  }>
}

/**
 * 获取登录趋势数据（近7天）
 * @returns 登录趋势数据
 */
export const fetchLoginTrend = () => {
  return request.get<LoginTrend>({
    url: '/api/dashboard/login-trend'
  })
}

/**
 * 操作统计数据接口
 */
export interface OperationStatistics {
  /** 日期列表 */
  dates: string[]
  /** 操作类型分布 */
  typeDistribution: Array<{ name: string; value: number }>
  /** 每日操作趋势 */
  dailyTrend: number[]
  /** 模块操作分布 */
  moduleDistribution: Array<{ name: string; value: number }>
}

/**
 * 获取操作统计数据（近7天）
 * @returns 操作统计数据
 */
export const fetchOperationStatistics = () => {
  return request.get<OperationStatistics>({
    url: '/api/dashboard/operation-statistics'
  })
}
