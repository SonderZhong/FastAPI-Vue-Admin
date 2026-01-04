/**
 * namespace: Api
 *
 * 所有接口相关类型定义
 * 在.vue文件使用会报错，需要在 eslint.config.mjs 中配置 globals: { Api: 'readonly' }
 */

declare namespace Api {
  /** 通用类型 */
  namespace Common {
    /** 分页参数 */
    interface PaginationParams {
      /** 当前页码 */
      current: number
      /** 每页条数 */
      size: number
      /** 总条数 */
      total: number
    }

    /** 通用搜索参数 */
    type CommonSearchParams = Pick<PaginationParams, 'current' | 'size'>

    /** 分页响应基础结构 */
    interface PaginatedResponse<T = any> {
      records: T[]
      current: number
      size: number
      total: number
    }

    /** 启用状态 */
    type EnableStatus = '1' | '2'
  }

  /** 认证相关类型 */
  namespace Auth {
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
      avatar: string | null
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

    /** 用户路由信息 */
    interface UserRoutes {
      routes: RouteItem[]
      permissions: string[]
    }

    /** 路由项 */
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

    /** 权限项 */
    interface AuthItem {
      authMark: string
      title: string
      minUserType?: number // 最低用户身份要求
    }

    /** 登录天数选项 */
    interface LoginDaysOption {
      label: string
      value: number
    }
  }

  /** 系统管理类型 */
  namespace SystemManage {
    /** 用户列表 */
    type UserList = Api.Common.PaginatedResponse<UserListItem>

    /** 用户列表项 */
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

    /** 用户搜索参数 */
    type UserSearchParams = Partial<
      Pick<UserListItem, 'id' | 'userName' | 'userGender' | 'userPhone' | 'userEmail' | 'status'> &
        Api.Common.CommonSearchParams
    >

    /** 角色列表 */
    type RoleList = Api.Common.PaginatedResponse<RoleListItem>

    /** 角色列表项 */
    interface RoleListItem {
      roleId: number
      roleName: string
      roleCode: string
      description: string
      enabled: boolean
      createTime: string
    }

    /** 角色搜索参数 */
    type RoleSearchParams = Partial<
      Pick<RoleListItem, 'roleId' | 'roleName' | 'roleCode' | 'description' | 'enabled'> &
        Api.Common.CommonSearchParams
    >
  }
}
