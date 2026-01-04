import { RoutesAlias } from '@/router/routesAlias'
import { AppRouteRecord } from '@/types/router'

export const routes: AppRouteRecord[] = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.dashboard.title',
      icon: '&#xe721;',
      order: 1,
      roles: ['R_SUPER', 'R_ADMIN']
    },
    children: [
      {
        path: 'console',
        name: 'Console',
        component: RoutesAlias.Dashboard,
        meta: {
          title: 'menus.dashboard.console',
          icon: '&#xe6cc;',
          keepAlive: false,
          fixedTab: true
        }
      }
    ]
  },
  {
    name: 'UserCenter_',
    path: '/user-center',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.system.userCenter',
      icon: '&#xe6bd;',
      order: 999
    },
    children: [
      {
        path: '',
        name: 'UserCenter',
        component: RoutesAlias.UserCenter,
        meta: {
          title: 'menus.system.userCenter',
          keepAlive: false,
          isHide: true
        }
      }
    ]
  },
  {
    name: 'PersonalLoginRecord_',
    path: '/personal-login-record',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.personalLoginRecord.title',
      icon: '&#xe6ce;',
      order: 999
    },
    children: [
      {
        path: '',
        name: 'PersonalLoginRecord',
        component: '/personal-login-record/index',
        meta: {
          title: 'menus.personalLoginRecord.title',
          icon: '&#xe6ce;',
          keepAlive: false,
          isHide: true
        }
      }
    ]
  },
  {
    name: 'PersonalOperationRecord_',
    path: '/personal-operation-record',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.personalOperationRecord.title',
      icon: '&#xe6df;',
      order: 999
    },
    children: [
      {
        path: '',
        name: 'PersonalOperationRecord',
        component: '/personal-operation-record/index',
        meta: {
          title: 'menus.personalOperationRecord.title',
          icon: '&#xe6df;',
          keepAlive: false,
          isHide: true
        }
      }
    ]
  },
  {
    name: 'MyNotification_',
    path: '/my-notification',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.myNotification.title',
      icon: '&#xe6c2;',
      order: 999
    },
    children: [
      {
        path: '',
        name: 'MyNotification',
        component: '/my-notification/index',
        meta: {
          title: 'menus.myNotification.title',
          icon: '&#xe6c2;',
          keepAlive: false,
          isHide: true
        }
      }
    ]
  }
]
export default routes
