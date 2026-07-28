declare namespace Auth {
  interface TenantOption {
    id: string
    name: string
    code?: string
  }

  interface CaptchaResponse {
    uuid: string | null
    captcha: string | null
    captcha_enabled: boolean
    register_enabled: boolean
    captcha_type: string
  }

  interface LoginParams {
    username: string
    password: string
    login_days?: number
    code?: string
    uuid?: string
  }

  interface LoginResponse {
    accessToken: string
    refreshToken: string
    expiresTime?: number
    tenant_id?: string | null
    available_tenants?: TenantOption[]
  }

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

  interface EmailCodeParams {
    username: string
    title: string
    mail: string
  }

  interface ForgetPasswordParams {
    username: string
    email: string
    code: string
    new_password: string
  }

  interface UserInfo {
    id: string
    username: string
    nickname: string
    email: string
    phone: string
    avatar: string | null
    gender: number
    status: number
    user_type: number
    department_id: string | null
    department_name: string | null
    tenant_id: string | null
    available_tenants?: TenantOption[]
    created_at: string
    updated_at: string
    sub_departments: string[]
    data_scope: number
    roles: string[]
    menus: string[]
    buttons: string[]
    apis: string[]
    permission_ids: string[]
    permission_marks: string[]
    permission_codes?: string[]
  }

  interface LoginDaysOption {
    label: string
    value: number
  }

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
