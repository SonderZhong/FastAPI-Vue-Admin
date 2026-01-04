/**
 * 权限标记配置
 * 根据后端 @Auth 装饰器中的权限标记整理
 * 格式：模块:操作:具体权限
 *
 * ⚠️ 重要说明：
 * - 权限完全由后端控制，通过用户的 permission_marks 字段返回
 * - 前端只做简单的权限标记检查，不做额外的权限限制
 * - minUserType 仅供参考，实际权限判断在后端完成
 */

/**
 * 权限配置接口
 */
export interface PermissionConfig {
  /** 权限标记 */
  mark: string
  /** 权限名称 */
  name: string
  /** 权限描述 */
  description?: string
  /** 参考：最低用户身份要求（仅用于文档说明，实际权限由后端控制） */
  minUserType?: number
}

/**
 * 编码查询模块权限
 */
export const CodePermissions = {
  // 模板相关
  UPLOAD_TEMPLATE: 'code:btn:uploadTemplate',
  QUERY_TEMPLATE: 'code:btn:queryTemplate',

  // 编码基础操作
  ADD: 'code:btn:add',
  DELETE: 'code:btn:delete',
  UPDATE: 'code:btn:update',
  INFO: 'code:btn:info',
  LIST: 'code:btn:list',
  IMPORT: 'code:btn:import',

  // 查询相关
  QUERY: 'code:btn:query',
  IMPORT_QUERY: 'code:btn:importQuery',

  // 日志相关
  LOG_LIST: 'code:btn:logList',
  LOG_INFO: 'code:btn:logInfo',
  LOG_ADMIN: 'code:btn:logAdmin',
  EXPORT: 'code:btn:export',

  // 反馈相关
  ADD_FEEDBACK: 'code:btn:addFeedback',
  DELETE_FEEDBACK: 'code:btn:deleteFeedback',
  UPDATE_FEEDBACK: 'code:btn:updateFeedback',
  FEEDBACK_INFO: 'code:btn:feedbackInfo',
  FEEDBACK_LIST: 'code:btn:feedbackList',
  FEEDBACK_AUDIT: 'code:btn:feedbackAudit',
  FEEDBACK_ADMIN: 'code:btn:feedbackAdmin',

  // 编码导入相关
  DELETE_CODE_IMPORT: 'code:btn:deleteCodeImport',
  UPDATE_CODE_IMPORT: 'code:btn:updateCodeImport',
  CODE_IMPORT_LIST: 'code:btn:codeImportList',
  CODE_IMPORT_AUDIT: 'code:btn:codeImportAudit',
  CODE_IMPORT_AUDIT_ALL: 'code:btn:codeImportAuditAll'
}

/**
 * 版本管理模块权限
 */
export const VersionPermissions = {
  ADD: 'version:btn:add',
  DELETE: 'version:btn:delete',
  UPDATE: 'version:btn:update',
  INFO: 'version:btn:info',
  LIST: 'version:btn:list',
  FETCH: 'version:btn:fetch',
  SYNC: 'version:btn:sync',
  CRAWL: 'version:btn:crawl'
}

/**
 * HTS分类模块权限
 */
export const HtsClassPermissions = {
  ADD: 'htsclass:btn:add',
  DELETE: 'htsclass:btn:delete',
  UPDATE: 'htsclass:btn:update',
  INFO: 'htsclass:btn:info',
  LIST: 'htsclass:btn:list'
}

/**
 * HTS项目模块权限
 */
export const HtsItemPermissions = {
  ADD: 'htsitem:btn:add',
  DELETE: 'htsitem:btn:delete',
  UPDATE: 'htsitem:btn:update',
  INFO: 'htsitem:btn:info',
  LIST: 'htsitem:btn:list',
  IMPORT: 'htsitem:btn:import'
}

/**
 * 调度器模块权限
 */
export const SchedulerPermissions = {
  START: 'scheduler:btn:start',
  STOP: 'scheduler:btn:stop',
  STATUS: 'scheduler:btn:status',
  RUN: 'scheduler:btn:run'
}

/**
 * 用户管理模块权限
 */
export const UserPermissions = {
  ADD_USER: 'user:btn:addUser',
  DELETE_USER: 'user:btn:deleteUser',
  UPDATE_USER: 'user:btn:updateUser',
  USER_INFO: 'user:btn:Userinfo',
  USER_LIST: 'user:btn:userList',

  // 角色管理
  ADD_ROLE: 'user:btn:addRole',
  DELETE_ROLE: 'user:btn:deleteRole',
  UPDATE_ROLE: 'user:btn:updateRole',
  ROLE_INFO: 'user:btn:roleInfo',
  ROLE_LIST: 'user:btn:roleList',
  PERMISSION_LIST: 'user:btn:permissionList',

  // 其他
  UPLOAD_AVATAR: 'user:btn:uploadAvatar',
  RESET_PASSWORD: 'user:btn:reset_password'
}

/**
 * 角色管理模块权限
 */
export const RolePermissions = {
  ADD: 'role:btn:add',
  DELETE: 'role:btn:delete',
  UPDATE: 'role:btn:update',
  INFO: 'role:btn:info',
  LIST: 'role:btn:list',

  // 权限分配
  ADD_PERMISSION: 'role:btn:addPermission',
  DELETE_PERMISSION: 'role:btn:deletePermission',
  UPDATE_PERMISSION: 'role:btn:updatePermission',
  PERMISSION_INFO: 'role:btn:permissionInfo',
  PERMISSION_LIST: 'role:btn:permissionList'
}

/**
 * 权限管理模块权限
 */
export const PermissionManagePermissions = {
  ADD: 'permission:btn:add',
  DELETE: 'permission:btn:delete',
  UPDATE: 'permission:btn:update',
  INFO: 'permission:btn:info',
  LIST: 'permission:btn:list'
}

/**
 * 部门管理模块权限
 */
export const DepartmentPermissions = {
  ADD: 'department:btn:add',
  DELETE: 'department:btn:delete',
  UPDATE: 'department:btn:update',
  INFO: 'department:btn:info',
  LIST: 'department:btn:list'
}

/**
 * 登录日志模块权限
 */
export const LoginLogPermissions = {
  LIST: 'login:btn:list',
  LOGOUT: 'login:btn:logout',
  DELETE: 'login:btn:delete'
}

/**
 * 操作日志模块权限
 */
export const OperationLogPermissions = {
  LIST: 'operation:btn:list',
  DELETE: 'operation:btn:delete'
}

/**
 * 缓存管理模块权限
 */
export const CachePermissions = {
  INFO_LIST: 'cache:btn:infoList',
  LIST: 'cache:btn:list',
  INFO: 'cache:btn:info',
  UPDATE: 'cache:btn:update',
  DELETE: 'cache:btn:delete'
}

/**
 * 配置管理模块权限
 */
export const ConfigPermissions = {
  ADD: 'config:btn:add',
  DELETE: 'config:btn:delete',
  UPDATE: 'config:btn:update',
  INFO: 'config:btn:info',
  LIST: 'config:btn:list'
}

/**
 * 服务器监控模块权限
 */
export const ServerPermissions = {
  INFO: 'server:btn:info'
}

/**
 * 所有权限配置
 */
export const AllPermissions = {
  Code: CodePermissions,
  Version: VersionPermissions,
  HtsClass: HtsClassPermissions,
  HtsItem: HtsItemPermissions,
  Scheduler: SchedulerPermissions,
  User: UserPermissions,
  Role: RolePermissions,
  Permission: PermissionManagePermissions,
  Department: DepartmentPermissions,
  LoginLog: LoginLogPermissions,
  OperationLog: OperationLogPermissions,
  Cache: CachePermissions,
  Config: ConfigPermissions,
  Server: ServerPermissions
}

/**
 * 权限详细配置（包含名称和描述）
 */
export const PermissionConfigs: Record<string, PermissionConfig> = {
  // 编码查询模块
  [CodePermissions.UPLOAD_TEMPLATE]: {
    mark: CodePermissions.UPLOAD_TEMPLATE,
    name: '上传模板',
    minUserType: 3
  },
  [CodePermissions.QUERY_TEMPLATE]: {
    mark: CodePermissions.QUERY_TEMPLATE,
    name: '查询模板',
    minUserType: 3
  },
  [CodePermissions.ADD]: { mark: CodePermissions.ADD, name: '添加编码', minUserType: 2 },
  [CodePermissions.DELETE]: { mark: CodePermissions.DELETE, name: '删除编码', minUserType: 2 },
  [CodePermissions.UPDATE]: { mark: CodePermissions.UPDATE, name: '更新编码', minUserType: 2 },
  [CodePermissions.INFO]: { mark: CodePermissions.INFO, name: '查看编码', minUserType: 3 },
  [CodePermissions.LIST]: { mark: CodePermissions.LIST, name: '编码列表', minUserType: 3 },
  [CodePermissions.IMPORT]: { mark: CodePermissions.IMPORT, name: '导入编码', minUserType: 2 },
  [CodePermissions.QUERY]: { mark: CodePermissions.QUERY, name: '查询编码', minUserType: 3 },
  [CodePermissions.IMPORT_QUERY]: {
    mark: CodePermissions.IMPORT_QUERY,
    name: '批量查询',
    minUserType: 3
  },
  [CodePermissions.LOG_LIST]: {
    mark: CodePermissions.LOG_LIST,
    name: '查询日志列表',
    minUserType: 2
  },
  [CodePermissions.LOG_INFO]: {
    mark: CodePermissions.LOG_INFO,
    name: '查询日志详情',
    minUserType: 2
  },
  [CodePermissions.LOG_ADMIN]: {
    mark: CodePermissions.LOG_ADMIN,
    name: '日志管理员',
    minUserType: 1
  },
  [CodePermissions.EXPORT]: { mark: CodePermissions.EXPORT, name: '导出数据', minUserType: 2 },
  [CodePermissions.ADD_FEEDBACK]: {
    mark: CodePermissions.ADD_FEEDBACK,
    name: '添加反馈',
    minUserType: 3
  },
  [CodePermissions.DELETE_FEEDBACK]: {
    mark: CodePermissions.DELETE_FEEDBACK,
    name: '删除反馈',
    minUserType: 2
  },
  [CodePermissions.UPDATE_FEEDBACK]: {
    mark: CodePermissions.UPDATE_FEEDBACK,
    name: '更新反馈',
    minUserType: 2
  },
  [CodePermissions.FEEDBACK_INFO]: {
    mark: CodePermissions.FEEDBACK_INFO,
    name: '查看反馈',
    minUserType: 3
  },
  [CodePermissions.FEEDBACK_LIST]: {
    mark: CodePermissions.FEEDBACK_LIST,
    name: '反馈列表',
    minUserType: 2
  },
  [CodePermissions.FEEDBACK_AUDIT]: {
    mark: CodePermissions.FEEDBACK_AUDIT,
    name: '反馈审核',
    minUserType: 1
  },
  [CodePermissions.FEEDBACK_ADMIN]: {
    mark: CodePermissions.FEEDBACK_ADMIN,
    name: '反馈管理员',
    minUserType: 1
  },
  [CodePermissions.DELETE_CODE_IMPORT]: {
    mark: CodePermissions.DELETE_CODE_IMPORT,
    name: '删除导入编码',
    minUserType: 2
  },
  [CodePermissions.UPDATE_CODE_IMPORT]: {
    mark: CodePermissions.UPDATE_CODE_IMPORT,
    name: '更新导入编码',
    minUserType: 2
  },
  [CodePermissions.CODE_IMPORT_LIST]: {
    mark: CodePermissions.CODE_IMPORT_LIST,
    name: '导入编码列表',
    minUserType: 2
  },
  [CodePermissions.CODE_IMPORT_AUDIT]: {
    mark: CodePermissions.CODE_IMPORT_AUDIT,
    name: '导入编码审核',
    minUserType: 1
  },
  [CodePermissions.CODE_IMPORT_AUDIT_ALL]: {
    mark: CodePermissions.CODE_IMPORT_AUDIT_ALL,
    name: '全部审核通过',
    minUserType: 0
  },

  // 版本管理模块
  [VersionPermissions.ADD]: { mark: VersionPermissions.ADD, name: '添加版本', minUserType: 0 },
  [VersionPermissions.DELETE]: {
    mark: VersionPermissions.DELETE,
    name: '删除版本',
    minUserType: 0
  },
  [VersionPermissions.UPDATE]: {
    mark: VersionPermissions.UPDATE,
    name: '更新版本',
    minUserType: 0
  },
  [VersionPermissions.INFO]: { mark: VersionPermissions.INFO, name: '查看版本', minUserType: 1 },
  [VersionPermissions.LIST]: { mark: VersionPermissions.LIST, name: '版本列表', minUserType: 1 },
  [VersionPermissions.FETCH]: {
    mark: VersionPermissions.FETCH,
    name: '获取版本数据',
    minUserType: 0
  },
  [VersionPermissions.SYNC]: { mark: VersionPermissions.SYNC, name: '同步版本', minUserType: 0 },
  [VersionPermissions.CRAWL]: { mark: VersionPermissions.CRAWL, name: '爬取数据', minUserType: 0 },

  // 用户管理模块
  [UserPermissions.ADD_USER]: { mark: UserPermissions.ADD_USER, name: '添加用户', minUserType: 1 },
  [UserPermissions.DELETE_USER]: {
    mark: UserPermissions.DELETE_USER,
    name: '删除用户',
    minUserType: 1
  },
  [UserPermissions.UPDATE_USER]: {
    mark: UserPermissions.UPDATE_USER,
    name: '更新用户',
    minUserType: 1
  },
  [UserPermissions.USER_INFO]: {
    mark: UserPermissions.USER_INFO,
    name: '查看用户',
    minUserType: 2
  },
  [UserPermissions.USER_LIST]: {
    mark: UserPermissions.USER_LIST,
    name: '用户列表',
    minUserType: 2
  },
  [UserPermissions.ADD_ROLE]: { mark: UserPermissions.ADD_ROLE, name: '添加角色', minUserType: 1 },
  [UserPermissions.DELETE_ROLE]: {
    mark: UserPermissions.DELETE_ROLE,
    name: '删除角色',
    minUserType: 1
  },
  [UserPermissions.UPDATE_ROLE]: {
    mark: UserPermissions.UPDATE_ROLE,
    name: '更新角色',
    minUserType: 1
  },
  [UserPermissions.ROLE_INFO]: {
    mark: UserPermissions.ROLE_INFO,
    name: '查看角色',
    minUserType: 2
  },
  [UserPermissions.ROLE_LIST]: {
    mark: UserPermissions.ROLE_LIST,
    name: '角色列表',
    minUserType: 2
  },
  [UserPermissions.PERMISSION_LIST]: {
    mark: UserPermissions.PERMISSION_LIST,
    name: '权限列表',
    minUserType: 1
  },
  [UserPermissions.UPLOAD_AVATAR]: {
    mark: UserPermissions.UPLOAD_AVATAR,
    name: '上传头像',
    minUserType: 3
  },
  [UserPermissions.RESET_PASSWORD]: {
    mark: UserPermissions.RESET_PASSWORD,
    name: '重置密码',
    minUserType: 1
  },

  // 角色管理模块
  [RolePermissions.ADD]: { mark: RolePermissions.ADD, name: '添加角色', minUserType: 0 },
  [RolePermissions.DELETE]: { mark: RolePermissions.DELETE, name: '删除角色', minUserType: 0 },
  [RolePermissions.UPDATE]: { mark: RolePermissions.UPDATE, name: '更新角色', minUserType: 0 },
  [RolePermissions.INFO]: { mark: RolePermissions.INFO, name: '查看角色', minUserType: 1 },
  [RolePermissions.LIST]: { mark: RolePermissions.LIST, name: '角色列表', minUserType: 1 },
  [RolePermissions.ADD_PERMISSION]: {
    mark: RolePermissions.ADD_PERMISSION,
    name: '添加权限',
    minUserType: 0
  },
  [RolePermissions.DELETE_PERMISSION]: {
    mark: RolePermissions.DELETE_PERMISSION,
    name: '删除权限',
    minUserType: 0
  },
  [RolePermissions.UPDATE_PERMISSION]: {
    mark: RolePermissions.UPDATE_PERMISSION,
    name: '更新权限',
    minUserType: 0
  },
  [RolePermissions.PERMISSION_INFO]: {
    mark: RolePermissions.PERMISSION_INFO,
    name: '查看权限',
    minUserType: 1
  },
  [RolePermissions.PERMISSION_LIST]: {
    mark: RolePermissions.PERMISSION_LIST,
    name: '权限列表',
    minUserType: 1
  },

  // 权限管理模块
  [PermissionManagePermissions.ADD]: {
    mark: PermissionManagePermissions.ADD,
    name: '添加权限',
    minUserType: 0
  },
  [PermissionManagePermissions.DELETE]: {
    mark: PermissionManagePermissions.DELETE,
    name: '删除权限',
    minUserType: 0
  },
  [PermissionManagePermissions.UPDATE]: {
    mark: PermissionManagePermissions.UPDATE,
    name: '更新权限',
    minUserType: 0
  },
  [PermissionManagePermissions.INFO]: {
    mark: PermissionManagePermissions.INFO,
    name: '查看权限',
    minUserType: 1
  },
  [PermissionManagePermissions.LIST]: {
    mark: PermissionManagePermissions.LIST,
    name: '权限列表',
    minUserType: 1
  },

  // 部门管理模块
  [DepartmentPermissions.ADD]: {
    mark: DepartmentPermissions.ADD,
    name: '添加部门',
    minUserType: 0
  },
  [DepartmentPermissions.DELETE]: {
    mark: DepartmentPermissions.DELETE,
    name: '删除部门',
    minUserType: 0
  },
  [DepartmentPermissions.UPDATE]: {
    mark: DepartmentPermissions.UPDATE,
    name: '更新部门',
    minUserType: 0
  },
  [DepartmentPermissions.INFO]: {
    mark: DepartmentPermissions.INFO,
    name: '查看部门',
    minUserType: 1
  },
  [DepartmentPermissions.LIST]: {
    mark: DepartmentPermissions.LIST,
    name: '部门列表',
    minUserType: 1
  },

  // 日志管理模块
  [LoginLogPermissions.LIST]: {
    mark: LoginLogPermissions.LIST,
    name: '登录日志列表',
    minUserType: 1
  },
  [LoginLogPermissions.LOGOUT]: {
    mark: LoginLogPermissions.LOGOUT,
    name: '强制登出',
    minUserType: 0
  },
  [LoginLogPermissions.DELETE]: {
    mark: LoginLogPermissions.DELETE,
    name: '删除日志',
    minUserType: 0
  },
  [OperationLogPermissions.LIST]: {
    mark: OperationLogPermissions.LIST,
    name: '操作日志列表',
    minUserType: 1
  },
  [OperationLogPermissions.DELETE]: {
    mark: OperationLogPermissions.DELETE,
    name: '删除日志',
    minUserType: 0
  },

  // 缓存管理模块
  [CachePermissions.INFO_LIST]: {
    mark: CachePermissions.INFO_LIST,
    name: '缓存信息列表',
    minUserType: 0
  },
  [CachePermissions.LIST]: { mark: CachePermissions.LIST, name: '缓存列表', minUserType: 0 },
  [CachePermissions.INFO]: { mark: CachePermissions.INFO, name: '查看缓存', minUserType: 0 },
  [CachePermissions.UPDATE]: { mark: CachePermissions.UPDATE, name: '更新缓存', minUserType: 0 },
  [CachePermissions.DELETE]: { mark: CachePermissions.DELETE, name: '删除缓存', minUserType: 0 },

  // 配置管理模块
  [ConfigPermissions.ADD]: { mark: ConfigPermissions.ADD, name: '添加配置', minUserType: 0 },
  [ConfigPermissions.DELETE]: { mark: ConfigPermissions.DELETE, name: '删除配置', minUserType: 0 },
  [ConfigPermissions.UPDATE]: { mark: ConfigPermissions.UPDATE, name: '更新配置', minUserType: 0 },
  [ConfigPermissions.INFO]: { mark: ConfigPermissions.INFO, name: '查看配置', minUserType: 1 },
  [ConfigPermissions.LIST]: { mark: ConfigPermissions.LIST, name: '配置列表', minUserType: 1 },

  // 服务器监控模块
  [ServerPermissions.INFO]: { mark: ServerPermissions.INFO, name: '服务器信息', minUserType: 0 },

  // HTS分类模块
  [HtsClassPermissions.ADD]: { mark: HtsClassPermissions.ADD, name: '添加分类', minUserType: 0 },
  [HtsClassPermissions.DELETE]: {
    mark: HtsClassPermissions.DELETE,
    name: '删除分类',
    minUserType: 0
  },
  [HtsClassPermissions.UPDATE]: {
    mark: HtsClassPermissions.UPDATE,
    name: '更新分类',
    minUserType: 0
  },
  [HtsClassPermissions.INFO]: { mark: HtsClassPermissions.INFO, name: '查看分类', minUserType: 1 },
  [HtsClassPermissions.LIST]: { mark: HtsClassPermissions.LIST, name: '分类列表', minUserType: 1 },

  // HTS项目模块
  [HtsItemPermissions.ADD]: { mark: HtsItemPermissions.ADD, name: '添加项目', minUserType: 0 },
  [HtsItemPermissions.DELETE]: {
    mark: HtsItemPermissions.DELETE,
    name: '删除项目',
    minUserType: 0
  },
  [HtsItemPermissions.UPDATE]: {
    mark: HtsItemPermissions.UPDATE,
    name: '更新项目',
    minUserType: 0
  },
  [HtsItemPermissions.INFO]: { mark: HtsItemPermissions.INFO, name: '查看项目', minUserType: 1 },
  [HtsItemPermissions.LIST]: { mark: HtsItemPermissions.LIST, name: '项目列表', minUserType: 1 },
  [HtsItemPermissions.IMPORT]: {
    mark: HtsItemPermissions.IMPORT,
    name: '导入项目',
    minUserType: 0
  },

  // 调度器模块
  [SchedulerPermissions.START]: {
    mark: SchedulerPermissions.START,
    name: '启动调度器',
    minUserType: 0
  },
  [SchedulerPermissions.STOP]: {
    mark: SchedulerPermissions.STOP,
    name: '停止调度器',
    minUserType: 0
  },
  [SchedulerPermissions.STATUS]: {
    mark: SchedulerPermissions.STATUS,
    name: '调度器状态',
    minUserType: 0
  },
  [SchedulerPermissions.RUN]: { mark: SchedulerPermissions.RUN, name: '运行调度器', minUserType: 0 }
}

/**
 * 获取权限配置
 * @param mark 权限标记
 * @returns 权限配置
 */
export function getPermissionConfig(mark: string): PermissionConfig | undefined {
  return PermissionConfigs[mark]
}

/**
 * 获取权限名称
 * @param mark 权限标记
 * @returns 权限名称
 */
export function getPermissionName(mark: string): string {
  const config = getPermissionConfig(mark)
  return config?.name || mark
}

/**
 * 检查权限标记是否存在
 * @param mark 权限标记
 * @returns 是否存在
 */
export function hasPermissionMark(mark: string): boolean {
  return mark in PermissionConfigs
}
