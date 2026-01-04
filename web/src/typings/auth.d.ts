/** 认证类型 */
declare namespace Auth {
  /** 验证码响应 */
  interface CaptchaResponse {
    uuid: string | null
    captcha: string | null
    captcha_enabled: boolean
    register_enabled: boolean
    captcha_type: string // 验证码类型：0=算术题，1=字母数字
  }

  /** 登录参数 */
  interface LoginParams {
    username: string
    password: string
    login_days?: number
    code?: string
    uuid?: string
  }

  /** 登录响应 */
  interface LoginResponse {
    accessToken: string
    refreshToken: string
    expiresTime?: number
  }

  /** 注册参数 */
  interface RegisterParams {
    username: string
    password: string
    email: string
    phone?: string
    nickname?: string
    gender?: number
    department_id?: string
    code: string
  }

  /** 邮箱验证码参数 */
  interface EmailCodeParams {
    username: string
    title: string
    mail: string
  }

  /** 忘记密码参数 */
  interface ForgetPasswordParams {
    username: string
    email: string
    code: string
    new_password: string
  }

  /** API 权限项 */
  interface ApiPermission {
    path: string
    method: string
  }

  /** 用户信息 - 适配 Casbin 方案C */
  interface UserInfo {
    id: string
    username: string
    nickname: string
    email: string
    phone: string
    avatar: string
    gender: number
    status: number
    user_type: number // 0:超级管理员, 1:管理员, 2:部门管理员, 3:普通用户
    department_id: string
    department_name: string
    created_at: string
    updated_at: string
    // Casbin 权限数据
    sub_departments: string[] // 可访问的部门ID列表
    data_scope: number // 数据权限范围: 1=全部, 2=本部门及下属, 3=仅本部门, 4=仅本人
    casbin_roles: string[] // Casbin 角色编码列表
    menus: string[] // 菜单权限ID列表
    buttons: string[] // 按钮权限ID列表
    apis: ApiPermission[] // API权限列表
    // 兼容字段
    permission_ids: string[] // 等同于 buttons
    permission_marks: string[] // 按钮权限的 authMark 列表
  }

  /** 登录天数选项 */
  interface LoginDaysOption {
    label: string
    value: number
  }

  /** 表单验证规则 */
  interface ValidationRule {
    required?: boolean
    message: string
    trigger?: string
    min?: number
    max?: number
    len?: number
    validator?: (rule: any, value: any, callback: any) => void
  }
}
