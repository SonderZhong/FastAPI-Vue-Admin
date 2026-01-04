import axios, { AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { useUserStore } from '@/store/modules/user'
import { ApiStatus } from './status'
import { HttpError, handleError, showError, showSuccess } from './error'
import { $t } from '@/locales'

/** 请求配置常量 */
const REQUEST_TIMEOUT = 1800000
const LOGOUT_DELAY = 500
const MAX_RETRIES = 0
const RETRY_DELAY = 1000
const UNAUTHORIZED_DEBOUNCE_TIME = 3000

/** 401防抖状态 */
let isUnauthorizedErrorShown = false
let unauthorizedTimer: NodeJS.Timeout | null = null

/** 扩展 AxiosRequestConfig */
interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  showErrorMessage?: boolean
  showSuccessMessage?: boolean
}

const { VITE_BASE_URL, VITE_WITH_CREDENTIALS } = import.meta.env

/** Axios实例 */
const axiosInstance = axios.create({
  timeout: REQUEST_TIMEOUT,
  baseURL: VITE_BASE_URL,
  withCredentials: VITE_WITH_CREDENTIALS === 'true',
  validateStatus: (status) => status >= 200 && status < 300,
  transformResponse: [
    (data, headers) => {
      const contentType = headers['content-type']
      if (contentType?.includes('application/json')) {
        try {
          return JSON.parse(data)
        } catch {
          return data
        }
      }
      return data
    }
  ]
})

/** 请求拦截器 */
axiosInstance.interceptors.request.use(
  (request: InternalAxiosRequestConfig) => {
    const { accessToken } = useUserStore()
    if (accessToken) request.headers.set('Authorization', `Bearer ${accessToken}`)

    if (request.data && !(request.data instanceof FormData) && !request.headers['Content-Type']) {
      request.headers.set('Content-Type', 'application/json')
      request.data = JSON.stringify(request.data)
    }

    return request
  },
  (error) => {
    showError(createHttpError($t('httpMsg.requestConfigError'), ApiStatus.error))
    return Promise.reject(error)
  }
)

/** 响应拦截器 */
axiosInstance.interceptors.response.use(
  (response: AxiosResponse<Http.BaseResponse>) => {
    // 如果响应类型是 blob，直接返回（用于文件下载）
    if (response.config.responseType === 'blob') {
      return response
    }

    const { code, msg } = response.data
    if (code === ApiStatus.success) return response
    if (code === ApiStatus.unauthorized) handleUnauthorizedError(msg)
    throw createHttpError(msg || $t('httpMsg.requestFailed'), code)
  },
  (error) => {
    if (error.response?.status === ApiStatus.unauthorized) handleUnauthorizedError()
    return Promise.reject(handleError(error))
  }
)

/** 统一创建HttpError */
function createHttpError(message: string, code: number) {
  return new HttpError(message, code)
}

/** 处理401错误（带防抖） */
function handleUnauthorizedError(message?: string): never {
  const error = createHttpError(message || $t('httpMsg.unauthorized'), ApiStatus.unauthorized)

  if (!isUnauthorizedErrorShown) {
    isUnauthorizedErrorShown = true
    logOut()

    unauthorizedTimer = setTimeout(resetUnauthorizedError, UNAUTHORIZED_DEBOUNCE_TIME)

    showError(error, true)
    throw error
  }

  throw error
}

/** 重置401防抖状态 */
function resetUnauthorizedError() {
  isUnauthorizedErrorShown = false
  if (unauthorizedTimer) clearTimeout(unauthorizedTimer)
  unauthorizedTimer = null
}

/** 退出登录函数 */
function logOut() {
  setTimeout(() => {
    useUserStore().logOut()
  }, LOGOUT_DELAY)
}

/** 是否需要重试 */
function shouldRetry(statusCode: number) {
  return [
    ApiStatus.requestTimeout,
    ApiStatus.internalServerError,
    ApiStatus.badGateway,
    ApiStatus.serviceUnavailable,
    ApiStatus.gatewayTimeout
  ].includes(statusCode)
}

/** 请求重试逻辑 */
async function retryRequest<TData>(
  config: ExtendedAxiosRequestConfig,
  retries: number = MAX_RETRIES
): Promise<Http.BaseResponse<TData>> {
  try {
    return await request<TData>(config)
  } catch (error) {
    if (retries > 0 && error instanceof HttpError && shouldRetry(error.code)) {
      await delay(RETRY_DELAY)
      return retryRequest<TData>(config, retries - 1)
    }
    throw error
  }
}

/** 延迟函数 */
function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * 请求函数
 * @template TData - data字段的类型
 * @param config - 请求配置
 * @returns Promise<Http.BaseResponse<TData>> - 完整的响应对象
 */
async function request<TData = any>(
  config: ExtendedAxiosRequestConfig
): Promise<Http.BaseResponse<TData>> {
  // POST | PUT 参数自动填充
  if (
    ['POST', 'PUT'].includes(config.method?.toUpperCase() || '') &&
    config.params &&
    !config.data
  ) {
    config.data = config.params
    config.params = undefined
  }

  try {
    const res = await axiosInstance.request<Http.BaseResponse<TData>>(config)

    // 如果是 blob 类型响应（文件下载），直接返回整个响应对象
    if (config.responseType === 'blob') {
      return res as any
    }

    // 显示成功消息
    if (config.showSuccessMessage && res.data.msg) {
      showSuccess(res.data.msg)
    }

    // 返回完整响应数据，包含code、msg、data、success、time等所有字段
    return res.data
  } catch (error) {
    if (error instanceof HttpError && error.code !== ApiStatus.unauthorized) {
      const showMsg = config.showErrorMessage !== false
      showError(error, showMsg)
    }
    return Promise.reject(error)
  }
}

/**过滤字典中的空值字段 */
export const filterEmptyObject = (data: { [key: string]: any }): object => {
  // 初始化一个空对象用于存储非空值字段
  return Object.keys(data).reduce(
    (acc, cur) => {
      // 检查当前字段的值是否为空
      if (data[cur] !== null && data[cur] !== undefined && data[cur] !== '') {
        // 如果不为空，则将其添加到结果对象中
        acc[cur] = data[cur]
      }
      // 返回累积的结果对象
      return acc
    },
    {} as { [key: string]: any }
  )
}

/** API方法集合 */
const api = {
  /**
   * GET请求
   * @template TData - data字段的类型
   * @param config - 请求配置
   * @returns Promise<Http.BaseResponse<TData>> - 完整的响应对象，包含code、msg、data、success、time
   */
  get<TData = any>(config: ExtendedAxiosRequestConfig): Promise<Http.BaseResponse<TData>> {
    // 过滤掉值为空的参数
    if (config.params) {
      config.params = filterEmptyObject(config.params)
    }
    return retryRequest<TData>({ ...config, method: 'GET' })
  },

  /**
   * POST请求
   * @template TData - data字段的类型
   * @param config - 请求配置
   * @returns Promise<Http.BaseResponse<TData>> - 完整的响应对象，包含code、msg、data、success、time
   */
  post<TData = any>(config: ExtendedAxiosRequestConfig): Promise<Http.BaseResponse<TData>> {
    return retryRequest<TData>({ ...config, method: 'POST' })
  },

  /**
   * PUT请求
   * @template TData - data字段的类型
   * @param config - 请求配置
   * @returns Promise<Http.BaseResponse<TData>> - 完整的响应对象，包含code、msg、data、success、time
   */
  put<TData = any>(config: ExtendedAxiosRequestConfig): Promise<Http.BaseResponse<TData>> {
    return retryRequest<TData>({ ...config, method: 'PUT' })
  },

  /**
   * DELETE请求
   * @template TData - data字段的类型
   * @param config - 请求配置
   * @returns Promise<Http.BaseResponse<TData>> - 完整的响应对象，包含code、msg、data、success、time
   */
  delete<TData = any>(config: ExtendedAxiosRequestConfig): Promise<Http.BaseResponse<TData>> {
    return retryRequest<TData>({ ...config, method: 'DELETE' })
  },

  /**
   * 通用请求
   * @template TData - data字段的类型
   * @param config - 请求配置
   * @returns Promise<Http.BaseResponse<TData>> - 完整的响应对象，包含code、msg、data、success、time
   */
  request<TData = any>(config: ExtendedAxiosRequestConfig): Promise<Http.BaseResponse<TData>> {
    return retryRequest<TData>(config)
  }
}

export default api
