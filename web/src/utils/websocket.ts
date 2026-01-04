/**
 * WebSocket 通知服务
 * 支持通知推送和请求-响应模式
 */
import { useUserStore } from '@/store/modules/user'

export interface NotificationMessage {
  type: 'notification' | 'login_notification' | 'connected' | 'unread_count' | 'response'
  data: any
  requestId?: string
}

type MessageHandler = (message: NotificationMessage) => void
type ResponseResolver = { resolve: (data: any) => void; reject: (error: any) => void; timeout: number }

class NotificationWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private handlers: Set<MessageHandler> = new Set()
  private pendingRequests: Map<string, ResponseResolver> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private heartbeatInterval = 30000
  private requestTimeout = 10000

  /**
   * 连接 WebSocket
   */
  connect() {
    const userStore = useUserStore()
    const token = userStore.accessToken

    if (!token) {
      console.warn('[WS] 未登录，无法连接 WebSocket')
      return
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WS] 已连接，无需重复连接')
      return
    }

    // 构建 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/notification/ws/${token}`

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('[WS] 连接成功')
        this.reconnectAttempts = 0
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: NotificationMessage = JSON.parse(event.data)
          
          // 处理请求响应
          if (message.type === 'response' && message.requestId) {
            const pending = this.pendingRequests.get(message.requestId)
            if (pending) {
              clearTimeout(pending.timeout)
              this.pendingRequests.delete(message.requestId)
              if (message.data?.success === false) {
                pending.reject(new Error(message.data?.msg || '请求失败'))
              } else {
                pending.resolve(message.data)
              }
            }
            return
          }
          
          this.notifyHandlers(message)
        } catch (e) {
          // 可能是 pong 响应
          if (event.data !== 'pong') {
            console.warn('[WS] 消息解析失败:', e)
          }
        }
      }

      this.ws.onclose = (event) => {
        console.log('[WS] 连接关闭:', event.code, event.reason)
        this.stopHeartbeat()
        this.rejectAllPending('WebSocket 连接已关闭')
        this.scheduleReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('[WS] 连接错误:', error)
      }
    } catch (e) {
      console.error('[WS] 创建连接失败:', e)
      this.scheduleReconnect()
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.stopHeartbeat()
    this.cancelReconnect()
    this.rejectAllPending('WebSocket 已断开')
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 发送请求并等待响应
   */
  request<T = any>(action: string, data?: any): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('WebSocket 未连接'))
        return
      }

      const requestId = this.generateRequestId()
      const timeout = window.setTimeout(() => {
        this.pendingRequests.delete(requestId)
        reject(new Error('请求超时'))
      }, this.requestTimeout)

      this.pendingRequests.set(requestId, { resolve, reject, timeout })

      try {
        this.ws!.send(JSON.stringify({
          type: 'request',
          action,
          requestId,
          data
        }))
      } catch (e) {
        clearTimeout(timeout)
        this.pendingRequests.delete(requestId)
        reject(e)
      }
    })
  }

  /**
   * 通过 WebSocket 获取用户信息
   */
  async getUserInfo(): Promise<any> {
    return this.request('getUserInfo')
  }

  /**
   * 通过 WebSocket 获取用户路由
   */
  async getUserRoutes(): Promise<any> {
    return this.request('getUserRoutes')
  }

  /**
   * 添加消息处理器
   */
  addHandler(handler: MessageHandler) {
    this.handlers.add(handler)
  }

  /**
   * 移除消息处理器
   */
  removeHandler(handler: MessageHandler) {
    this.handlers.delete(handler)
  }

  /**
   * 通知所有处理器
   */
  private notifyHandlers(message: NotificationMessage) {
    this.handlers.forEach(handler => {
      try {
        handler(message)
      } catch (e) {
        console.error('[WS] 处理器执行错误:', e)
      }
    })
  }

  /**
   * 生成请求ID
   */
  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 拒绝所有待处理请求
   */
  private rejectAllPending(reason: string) {
    this.pendingRequests.forEach((pending, requestId) => {
      clearTimeout(pending.timeout)
      pending.reject(new Error(reason))
    })
    this.pendingRequests.clear()
  }

  /**
   * 开始心跳
   */
  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping')
      }
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 计划重连
   */
  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('[WS] 达到最大重连次数，停止重连')
      return
    }

    this.cancelReconnect()
    
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts)
    console.log(`[WS] ${delay}ms 后尝试重连 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
    
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }

  /**
   * 取消重连
   */
  private cancelReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// 导出单例
export const notificationWs = new NotificationWebSocket()
