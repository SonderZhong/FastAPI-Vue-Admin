/**
 * 文件上传 API
 */
import request from '@/utils/http'

/**
 * 上传文件
 */
export const fetchUploadFile = (data: FormData) =>
  request.post({
    url: '/api/file/upload',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
