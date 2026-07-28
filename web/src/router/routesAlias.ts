/**
 * 路由别名，方便快速找到页面，同时可以用作路由跳转
 */
export enum RoutesAlias {
  // 布局和认证
  Layout = '/index/index',
  Login = '/auth/login',
  SelectTenant = '/auth/select-tenant',
  Register = '/auth/register',
  ForgetPassword = '/auth/forget-password',

  // 异常页面
  Exception403 = '/exception/403',
  Exception404 = '/exception/404',
  Exception500 = '/exception/500',

  // 结果页面
  Success = '/result/success',
  Fail = '/result/fail',

  // 仪表盘
  Dashboard = '/dashboard/console',

  // 系统管理
  User = '/system/user',
  Role = '/system/role',
  UserCenter = '/user-center',
  Menu = '/system/menu',
  Permission = '/system/permission'
}
