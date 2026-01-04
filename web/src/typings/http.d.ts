declare namespace Http {
  /** 基础响应 */
  interface BaseResponse<T = any> {
    // 状态码
    code: number
    // 消息
    msg: string
    // 数据
    data: T
    // 操作是否成功
    success: boolean
    // 响应时间
    time: string
  }
}
