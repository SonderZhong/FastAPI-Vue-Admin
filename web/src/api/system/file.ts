/**
 * 文件管理 API
 */

import request from '@/utils/http'

/** 文件类型常量 */
export const FileType = {
  IMAGE: 'image',
  DOCUMENT: 'document',
  VIDEO: 'video',
  AUDIO: 'audio',
  ARCHIVE: 'archive',
  OTHER: 'other'
} as const

/** 存储类型常量 */
export const StorageType = {
  LOCAL: 'local',
  ALIYUN_OSS: 'aliyun_oss',
  TENCENT_COS: 'tencent_cos',
  QINIU: 'qiniu',
  MINIO: 'minio'
} as const

/** 存储类型标签 */
export const StorageTypeLabels: Record<string, string> = {
  local: '本地存储',
  aliyun_oss: '阿里云OSS',
  tencent_cos: '腾讯云COS',
  qiniu: '七牛云',
  minio: 'MinIO'
}

/** 文件类型标签 */
export const FileTypeLabels: Record<string, string> = {
  image: '图片',
  document: '文档',
  video: '视频',
  audio: '音频',
  archive: '压缩包',
  other: '其他'
}

/** 文件信息接口 */
export interface FileInfo {
  id: string
  name: string
  key: string
  url: string
  size: number
  file_type: string
  mime_type?: string
  extension?: string
  hash?: string
  storage_type: string
  folder: string
  uploader_id?: string
  uploader_name?: string
  remark?: string
  created_at: string
  updated_at: string
}

/** 文件搜索参数 */
export interface FileSearchParams {
  page?: number
  pageSize?: number
  name?: string
  file_type?: string
  folder?: string
  storage_type?: string
}

/** 文件列表响应 */
export interface FileListResponse {
  total: number
  page: number
  pageSize: number
  result: FileInfo[]
}

/** 上传响应 */
export interface UploadResponse {
  id: string
  name: string
  url: string
  key: string
  size: number
  file_type: string
}

/** 批量上传响应 */
export interface BatchUploadResponse {
  success: UploadResponse[]
  errors: Array<{ name: string; error: string }>
}

/** 文件统计 */
export interface FileStatistics {
  total_count: number
  total_size: number
  type_stats: Array<{ file_type: string; count: number }>
  storage_stats: Array<{ storage_type: string; count: number }>
}

/** 存储配置 */
export interface StorageConfig {
  storage_type: string
  max_size: number
  allowed_extensions: string[]
}

/**
 * 获取文件列表
 */
export const fetchFileList = (params: FileSearchParams) =>
  request.get<FileListResponse>({
    url: '/api/file/list',
    params
  })

/**
 * 获取文件详情
 */
export const fetchFileInfo = (id: string) =>
  request.get<FileInfo>({
    url: `/api/file/info/${id}`
  })

/**
 * 上传文件
 */
export const fetchUploadFile = (file: File, folder: string = '') => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<UploadResponse>({
    url: '/api/file/upload',
    params: { folder },
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 批量上传文件
 */
export const fetchUploadFiles = (files: File[], folder: string = '') => {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))
  return request.post<BatchUploadResponse>({
    url: '/api/file/upload/batch',
    params: { folder },
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除文件
 */
export const fetchDeleteFile = (id: string) =>
  request.delete<null>({
    url: `/api/file/delete/${id}`
  })

/**
 * 批量删除文件
 */
export const fetchDeleteFileList = (ids: string[]) =>
  request.post<null>({
    url: '/api/file/deleteList',
    data: { ids }
  })

/**
 * 获取文件统计
 */
export const fetchFileStatistics = () =>
  request.get<FileStatistics>({
    url: '/api/file/statistics'
  })

/**
 * 获取存储配置
 */
export const fetchStorageConfig = () =>
  request.get<StorageConfig>({
    url: '/api/file/storage-config'
  })

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 获取文件图标
 */
export const getFileIcon = (fileType: string): string => {
  const icons: Record<string, string> = {
    image: 'i-carbon-image',
    document: 'i-carbon-document',
    video: 'i-carbon-video',
    audio: 'i-carbon-music',
    archive: 'i-carbon-zip',
    other: 'i-carbon-document-unknown'
  }
  return icons[fileType] || icons.other
}

/** 头像上传响应 */
export interface AvatarUploadResponse {
  file_id?: string
  file_url: string
  file_size?: number
  file_type?: string
  id?: string
  avatar_url?: string
}

/**
 * 上传头像（调用用户头像专用接口）
 * @param file 头像文件
 * @param userId 用户ID（可选，默认当前用户）
 * @returns 上传结果
 */
export const uploadAvatar = async (file: File, userId?: string): Promise<{ success: boolean; data?: AvatarUploadResponse; msg?: string }> => {
  const formData = new FormData()
  formData.append('file', file)
  
  // 如果没有传userId，需要从store获取当前用户ID
  // 这里使用通用文件上传接口，然后需要单独更新用户头像
  // 或者调用专门的用户头像接口
  if (userId) {
    // 调用用户头像专用接口
    const response = await request.post<any>({
      url: `/api/user/avatar/${userId}`,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response?.success && response.data) {
      return {
        success: true,
        data: {
          file_url: response.data.avatar_url,
          file_id: response.data.id,
          file_size: response.data.size,
          file_type: response.data.file_type
        }
      }
    }
    return { success: false, msg: response?.msg || '上传失败' }
  }
  
  // 没有userId时使用通用上传接口
  const response = await request.post<UploadResponse>({
    url: '/api/file/upload',
    params: { folder: 'avatars' },
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  if (response?.success && response.data) {
    return {
      success: true,
      data: {
        file_id: response.data.id,
        file_url: response.data.url,
        file_size: response.data.size,
        file_type: response.data.file_type
      }
    }
  }
  return { success: false, msg: response?.msg || '上传失败' }
}
