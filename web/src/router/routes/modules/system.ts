import { RoutesAlias } from '@/router/routesAlias'
import { AppRouteRecord } from '@/types/router'

export const routes: AppRouteRecord[] = [
  {
    name: 'System',
    path: '/system',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.system.title',
      icon: '&#xe72b;',
      order: 2
    },
    children: [
      {
        path: 'user',
        name: 'User',
        component: '/system/user/index',
        meta: {
          title: 'menus.system.user',
          icon: '&#xe608;',
          auth: ['user:btn:list']
        }
      },
      {
        path: 'role',
        name: 'Role',
        component: '/system/role/index',
        meta: {
          title: 'menus.system.role',
          icon: '&#xe724;',
          auth: ['role:btn:list']
        }
      },
      {
        path: 'department',
        name: 'Department',
        component: '/system/department/index',
        meta: {
          title: 'menus.system.department',
          icon: '&#xe830;',
          auth: ['department:btn:list']
        }
      },
      {
        path: 'permission',
        name: 'Permission',
        component: '/system/permission/index',
        meta: {
          title: 'menus.system.permission',
          icon: '&#xe6f7;',
          auth: ['permission:btn:list']
        }
      },
      {
        path: 'config',
        name: 'Config',
        component: '/system/config/index',
        meta: {
          title: 'menus.system.config',
          icon: '&#xe614;',
          auth: ['config:btn:list']
        }
      },
      {
        path: 'cache',
        name: 'Cache',
        component: '/system/cache/index',
        meta: {
          title: 'menus.system.cache',
          icon: '&#xe6c8;',
          auth: ['cache:btn:list']
        }
      },
      {
        path: 'server',
        name: 'Server',
        component: '/system/server/index',
        meta: {
          title: 'menus.system.server',
          icon: '&#xe65f;',
          auth: ['server:btn:info']
        }
      },
      {
        path: 'notification',
        name: 'Notification',
        component: '/system/notification/index',
        meta: {
          title: 'menus.system.notification',
          icon: '&#xe6e8;',
          auth: ['notification:btn:list']
        }
      },
      {
        path: 'file',
        name: 'FileManagement',
        component: '/system/file/index',
        meta: {
          title: 'menus.system.file',
          icon: '&#xe6ce;',
          auth: ['file:btn:list']
        }
      }
    ]
  }
]

export default routes
