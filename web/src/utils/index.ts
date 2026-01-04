/**
 * Utils 工具函数统一导出
 * 提供向后兼容性和便捷导入
 */

// UI 相关
export * from './ui'

// 浏览器相关
export * from './browser'

// 数据处理相关
export * from './dataprocess'

// 路由导航相关
export * from './navigation'

// 系统管理相关
export * from './sys'

// 常量定义相关
export * from './constants'

// 存储相关
export * from './storage'

// 主题相关
export * from './theme'

// HTTP 相关
export * from './http'

// webSocket 相关
export * from './socket'

// 验证相关
export * from './validation'

/**
 * 获取文件/头像URL（智能处理路径）
 * @param url 文件URL
 * @returns 处理后的URL
 */
export const getFileUrl = (url: string | undefined | null): string => {
  if (!url) return ''
  // 如果已经是完整URL，直接返回
  if (url.startsWith('http')) return url
  // 处理重复的/api前缀（如 /api/api/files/...）
  while (url.startsWith('/api/api')) {
    url = url.replace('/api/api', '/api')
  }
  // 如果以/api/files开头，去掉/api前缀（后端不应该返回/api前缀）
  if (url.startsWith('/api/files')) {
    return url.replace('/api', '')
  }
  // 如果以/files开头，直接返回
  if (url.startsWith('/files')) return url
  // 否则加上/api前缀（兼容旧的/uploads路径）
  return `/api${url}`
}

/**
 * 获取头像URL
 * @param avatar 头像URL
 * @returns 处理后的URL
 */
export const getAvatarUrl = getFileUrl
