/**
 * 通知管理 API
 */

import request from '@/utils/http'

/** 通知类型 */
export enum NotificationType {
  LOGIN = 0,        // 登录通知
  ANNOUNCEMENT = 1, // 全局公告
  MESSAGE = 2       // 系统消息
}

/** 通知范围 */
export enum NotificationScope {
  ALL = 0,          // 全部用户
  DEPARTMENT = 1,   // 指定部门
  USER = 2          // 指定用户
}

/** 通知状态 */
export enum NotificationStatus {
  DRAFT = 0,        // 草稿
  PUBLISHED = 1,    // 已发布
  REVOKED = 2       // 已撤回
}

/** 通知优先级 */
export enum NotificationPriority {
  NORMAL = 0,       // 普通
  IMPORTANT = 1,    // 重要
  URGENT = 2        // 紧急
}

/** 通知信息 */
export interface NotificationInfo {
  id: string
  title: string
  content: string
  type: NotificationType
  scope: NotificationScope
  scope_ids: string[]
  status: NotificationStatus
  priority: NotificationPriority
  publish_time?: string
  expire_time?: string
  created_at: string
  updated_at: string
  creator_id?: string
  creator_name?: string
  statistics?: {
    total: number
    read: number
    unread: number
  }
}

/** 用户通知信息 */
export interface UserNotificationInfo {
  id: string
  notification_id: string
  title: string
  content: string
  notification_type: NotificationType
  priority: NotificationPriority
  publish_time: string
  creator_name: string
  is_read: boolean
  read_time?: string
  created_at: string
}

/** 创建通知参数 */
export interface CreateNotificationParams {
  title: string
  content: string
  type?: NotificationType
  scope?: NotificationScope
  scope_ids?: string[]
  priority?: NotificationPriority
  expire_time?: string
}

/** 更新通知参数 */
export interface UpdateNotificationParams {
  title?: string
  content?: string
  type?: NotificationType
  scope?: NotificationScope
  scope_ids?: string[]
  priority?: NotificationPriority
  expire_time?: string
}

// ==================== 通知管理 API ====================

/** 获取通知列表（管理端） */
export const fetchNotificationList = (params: {
  page?: number
  pageSize?: number
  type?: NotificationType
  status?: NotificationStatus
  title?: string
}) => {
  return request.get<{
    result: NotificationInfo[]
    total: number
    page: number
    pageSize: number
  }>({
    url: '/api/notification/list',
    params
  })
}

/** 获取通知详情 */
export const fetchNotificationInfo = (id: string) => {
  return request.get<NotificationInfo>({
    url: `/api/notification/info/${id}`
  })
}

/** 创建通知 */
export const createNotification = (data: CreateNotificationParams) => {
  return request.post<{ id: string }>({
    url: '/api/notification/create',
    data
  })
}

/** 更新通知 */
export const updateNotification = (id: string, data: UpdateNotificationParams) => {
  return request.put<null>({
    url: `/api/notification/update/${id}`,
    data
  })
}

/** 发布通知 */
export const publishNotification = (id: string) => {
  return request.post<{
    total_users: number
    online_count: number
    offline_count: number
  }>({
    url: `/api/notification/publish/${id}`
  })
}

/** 撤回通知 */
export const revokeNotification = (id: string) => {
  return request.post<null>({
    url: `/api/notification/revoke/${id}`
  })
}

/** 删除通知 */
export const deleteNotification = (id: string) => {
  return request.delete<null>({
    url: `/api/notification/delete/${id}`
  })
}

// ==================== 用户通知 API ====================

/** 获取我的通知列表 */
export const fetchMyNotifications = (params: {
  page?: number
  pageSize?: number
  is_read?: boolean
  type?: NotificationType
}) => {
  return request.get<{
    result: UserNotificationInfo[]
    total: number
    page: number
    pageSize: number
  }>({
    url: '/api/notification/my/list',
    params
  })
}

/** 标记通知已读 */
export const markNotificationRead = (id: string) => {
  return request.post<null>({
    url: `/api/notification/my/read/${id}`
  })
}

/** 全部标记已读 */
export const markAllNotificationsRead = () => {
  return request.post<null>({
    url: '/api/notification/my/read-all'
  })
}

/** 获取未读数量 */
export const fetchUnreadCount = () => {
  return request.get<{ count: number }>({
    url: '/api/notification/my/unread-count'
  })
}

/** 获取待推送通知（HTTP轮询） */
export const fetchPendingNotifications = () => {
  return request.get<{ notifications: any[] }>({
    url: '/api/notification/my/pending'
  })
}
