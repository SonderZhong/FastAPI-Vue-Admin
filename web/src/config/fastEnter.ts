/**
 * 快速入口配置
 * 包含：应用列表、快速链接等配置
 */
import { RoutesAlias } from '@/router/routesAlias'
import type { FastEnterConfig } from '@/types/config'

const fastEnterConfig: FastEnterConfig = {
  // 显示条件（屏幕宽度）
  minWidth: 1200,

  // 应用列表 - 核心功能快捷入口
  applications: [
    {
      name: 'fastEnter.applications.dashboard',
      description: 'fastEnter.applications.dashboardDesc',
      icon: '&#xe721;',
      iconColor: '#377dff',
      path: RoutesAlias.Dashboard,
      enabled: true,
      order: 1
    },
    {
      name: 'fastEnter.applications.userCenter',
      description: 'fastEnter.applications.userCenterDesc',
      icon: '&#xe608;',
      iconColor: '#00d4bd',
      path: RoutesAlias.UserCenter,
      enabled: true,
      order: 2
    },
    {
      name: 'fastEnter.applications.userManage',
      description: 'fastEnter.applications.userManageDesc',
      icon: '&#xe6bd;',
      iconColor: '#ff6b6b',
      path: '/system/user',
      enabled: true,
      order: 3,
      minUserType: 1 // 需要管理员权限
    },
    {
      name: 'fastEnter.applications.departmentManage',
      description: 'fastEnter.applications.departmentManageDesc',
      icon: '&#xe811;',
      iconColor: '#4dabf7',
      path: '/system/department',
      enabled: true,
      order: 4,
      minUserType: 1 // 需要管理员权限
    },
    {
      name: 'fastEnter.applications.roleManage',
      description: 'fastEnter.applications.roleManageDesc',
      icon: '&#xe6e5;',
      iconColor: '#9775fa',
      path: '/system/role',
      enabled: true,
      order: 5,
      minUserType: 1 // 需要管理员权限
    },
    {
      name: 'fastEnter.applications.permissionManage',
      description: 'fastEnter.applications.permissionManageDesc',
      icon: '&#xe7ba;',
      iconColor: '#ffd43b',
      path: '/system/permission',
      enabled: true,
      order: 6,
      minUserType: 1 // 需要管理员权限
    }
  ],

  // 快速链接 - 常用功能快速访问
  quickLinks: [
    {
      name: 'fastEnter.quickLinks.personalLoginRecord',
      path: '/personal-login-record',
      icon: '&#xe608;',
      enabled: true,
      order: 1
    },
    {
      name: 'fastEnter.quickLinks.personalOperationRecord',
      path: '/personal-operation-record',
      icon: '&#xe7a8;',
      enabled: true,
      order: 2
    },
    {
      name: 'fastEnter.quickLinks.loginLog',
      path: '/log-manager/login-log',
      icon: '&#xe6f4;',
      enabled: true,
      order: 3,
      minUserType: 2 // 需要部门管理员及以上
    },
    {
      name: 'fastEnter.quickLinks.operationLog',
      path: '/log-manager/operation-log',
      icon: '&#xe859;',
      enabled: true,
      order: 4,
      minUserType: 2 // 需要部门管理员及以上
    },
    {
      name: 'fastEnter.quickLinks.systemConfig',
      path: '/system/config',
      icon: '&#xe651;',
      enabled: true,
      order: 5,
      minUserType: 1 // 需要管理员权限
    },
    {
      name: 'fastEnter.quickLinks.cacheManage',
      path: '/system/cache',
      icon: '&#xe70a;',
      enabled: true,
      order: 6,
      minUserType: 1 // 需要管理员权限
    },
    {
      name: 'fastEnter.quickLinks.serverMonitor',
      path: '/system/server',
      icon: '&#xe81d;',
      enabled: true,
      order: 7,
      minUserType: 1 // 需要管理员权限
    }
  ]
}

export default Object.freeze(fastEnterConfig)
