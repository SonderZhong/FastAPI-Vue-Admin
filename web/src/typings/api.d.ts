declare namespace Api {
  namespace Common {
    interface PaginationParams {
      current: number
      size: number
      total: number
    }

    type CommonSearchParams = Pick<PaginationParams, 'current' | 'size'>

    interface PaginatedResponse<T = any> {
      records: T[]
      current: number
      size: number
      total: number
    }

    type EnableStatus = '1' | '2'
  }

  namespace Auth {
    interface TenantOption {
      id: string
      name: string
      code?: string
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

    interface UserRoutes {
      routes: RouteItem[]
      permissions: string[]
    }

    interface RouteItem {
      id: string
      name: string
      path: string
      component: string
      title: string
      icon: string | null
      order: number
      isHide: boolean
      keepAlive: boolean
      children?: RouteItem[]
      meta?: {
        authList?: AuthItem[]
        [key: string]: any
      }
    }

    interface AuthItem {
      authMark: string
      title: string
      minUserType?: number
    }

    interface LoginDaysOption {
      label: string
      value: number
    }
  }

  namespace SystemManage {
    type UserList = Api.Common.PaginatedResponse<UserListItem>

    interface UserListItem {
      id: number
      avatar: string
      status: string
      userName: string
      userGender: string
      nickName: string
      userPhone: string
      userEmail: string
      userRoles: string[]
      createBy: string
      createTime: string
      updateBy: string
      updateTime: string
    }

    type UserSearchParams = Partial<
      Pick<UserListItem, 'id' | 'userName' | 'userGender' | 'userPhone' | 'userEmail' | 'status'> &
        Api.Common.CommonSearchParams
    >

    type RoleList = Api.Common.PaginatedResponse<RoleListItem>

    interface RoleListItem {
      roleId: number
      roleName: string
      roleCode: string
      description: string
      enabled: boolean
      createTime: string
    }

    type RoleSearchParams = Partial<
      Pick<RoleListItem, 'roleId' | 'roleName' | 'roleCode' | 'description' | 'enabled'> &
        Api.Common.CommonSearchParams
    >
  }
}
