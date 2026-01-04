import { RoutesAlias } from '@/router/routesAlias'
import { AppRouteRecord } from '@/types/router'

export const routes: AppRouteRecord[] = [
  {
    name: 'LogManager',
    path: '/log-manager',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.logManager.title',
      icon: '&#xe6ce;', // 日志图标
      order: 3
    },
    children: [
      {
        path: 'login-log',
        name: 'LoginLog',
        component: '/log-manager/login-log/index',
        meta: {
          title: 'menus.logManager.loginLog.title',
          icon: '&#xe6ce;', // 登录图标
          auth: ['login:btn:list']
        }
      },
      {
        path: 'operation-log',
        name: 'OperationLog',
        component: '/log-manager/operation-log/index',
        meta: {
          title: 'menus.logManager.operationLog.title',
          icon: '&#xe6df;', // 操作图标
          auth: ['operation:btn:list']
        }
      }
    ]
  }
]

export default routes
