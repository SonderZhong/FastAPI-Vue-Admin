import request from '@/utils/http'

export interface DashboardStatistics {
  unreadNotifications: number
  totalNotifications: number
  todayLogins: number
  todayOperations: number
  weekLogins?: number
  weekOperations?: number
  notificationReadRate?: number
}

export const fetchDashboardStatistics = () => {
  return request.get<DashboardStatistics>({
    url: '/api/dashboard/statistics'
  })
}

export interface LoginStatistics {
  osDistribution: Array<{ name: string; value: number }>
  browserDistribution: Array<{ name: string; value: number }>
  locationDistribution: Array<{ name: string; value: number }>
}

export const fetchLoginStatistics = () => {
  return request.get<LoginStatistics>({
    url: '/api/dashboard/login-statistics'
  })
}

export interface LoginTrend {
  dates: string[]
  loginCounts: number[]
  locationSeries: Array<{
    name: string
    data: number[]
  }>
}

export const fetchLoginTrend = () => {
  return request.get<LoginTrend>({
    url: '/api/dashboard/login-trend'
  })
}

export interface OperationStatistics {
  dates: string[]
  typeDistribution: Array<{ name: string; value: number }>
  dailyTrend: number[]
  moduleDistribution: Array<{ name: string; value: number }>
}

export const fetchOperationStatistics = () => {
  return request.get<OperationStatistics>({
    url: '/api/dashboard/operation-statistics'
  })
}
