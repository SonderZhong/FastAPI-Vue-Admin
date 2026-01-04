import request from '@/utils/http'
import { notificationWs } from '@/utils/websocket'

/**
 * 获取验证码
 * @returns 验证码信息
 */
export function fetchCaptcha() {
  return request.get<Auth.CaptchaResponse>({
    url: '/api/auth/captcha'
  })
}

/**
 * 登录
 * @param params 登录参数
 * @returns 登录响应
 */
export function fetchLogin(params: Auth.LoginParams) {
  return request.post<Auth.LoginResponse>({
    url: '/api/auth/login',
    data: params,
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  })
}

/**
 * 注册
 * @param params 注册参数
 * @returns 注册响应
 */
export function fetchRegister(params: Auth.RegisterParams) {
  return request.post<null>({
    url: '/api/auth/register',
    data: params
  })
}

/**
 * 获取邮箱验证码
 * @param params 邮箱验证码参数
 * @returns 响应
 */
export function fetchEmailCode(params: Auth.EmailCodeParams) {
  return request.post<null>({
    url: '/api/auth/code',
    data: params
  })
}

/**
 * 忘记密码
 * @param params 忘记密码参数
 * @returns 响应
 */
export function fetchForgetPassword(params: Auth.ForgetPasswordParams) {
  return request.post<null>({
    url: '/api/auth/forget-password',
    data: params
  })
}

/**
 * 获取用户信息
 * 优先使用 WebSocket，失败时回退到 HTTP
 * @returns 用户信息
 */
export async function fetchGetUserInfo() {
  // 优先使用 WebSocket
  if (notificationWs.isConnected()) {
    try {
      const data = await notificationWs.getUserInfo()
      return { success: true, data, msg: 'ok' }
    } catch (e) {
      console.warn('[Auth] WebSocket 获取用户信息失败，回退到 HTTP:', e)
    }
  }
  
  // 回退到 HTTP
  return request.get<Auth.UserInfo>({
    url: '/api/auth/info'
  })
}

/**
 * 获取用户路由
 * 优先使用 WebSocket，失败时回退到 HTTP
 * @returns 用户动态路由数据
 */
export async function fetchGetUserRoutes() {
  // 优先使用 WebSocket
  if (notificationWs.isConnected()) {
    try {
      const data = await notificationWs.getUserRoutes()
      return { success: true, data, msg: 'ok' }
    } catch (e) {
      console.warn('[Auth] WebSocket 获取路由失败，回退到 HTTP:', e)
    }
  }
  
  // 回退到 HTTP
  return request.get<Api.Auth.UserRoutes>({
    url: '/api/auth/routes'
  })
}

/**
 * 退出系统
 */
export function fetchLogout() {
  return request.post<null>({
    url: '/api/auth/logout'
  })
}

/**
 * 更新用户密码
 * @param params 更新密码参数
 * @returns 响应
 */
export function updateUserPassword(params: { oldPassword: string; newPassword: string }) {
  return request.post<null>({
    url: '/api/user/updatePassword',
    data: params,
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  })
}

/**
 * 更新用户邮箱
 * @param params 更新邮箱参数
 * @returns 响应
 */
export function updateUserEmail(params: { password: string; email: string }) {
  return request.post<null>({
    url: '/api/user/updateEmail',
    data: params,
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  })
}

/**
 * 更新用户手机号
 * @param params 更新手机号参数
 * @returns 响应
 */
export function updateUserPhone(params: { password: string; phone: string }) {
  return request.post<null>({
    url: '/api/user/updatePhone',
    data: params,
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  })
}

/**
 * 更新基础用户信息
 * @param params 更新参数
 * @returns 响应
 */
export function updateBaseUserInfo(params: { name?: string; gender: number }) {
  return request.post<null>({
    url: '/api/user/updateBaseUserInfo',
    data: params
  })
}
