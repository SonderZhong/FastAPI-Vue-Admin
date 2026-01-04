# 路由和菜单

## 路由配置

前端路由配置位于 `web/src/router/routes/modules/` 目录下。

### 基本结构

```typescript
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
      }
    ]
  }
]
```

### Meta 配置项

| 属性 | 类型 | 说明 |
|------|------|------|
| title | string | 菜单标题（支持 i18n） |
| icon | string | 菜单图标 |
| order | number | 排序（数字越小越靠前） |
| auth | string[] | 权限标识列表 |
| isHide | boolean | 是否隐藏菜单 |
| keepAlive | boolean | 是否缓存页面 |
| fixedTab | boolean | 是否固定标签页 |
| link | string | 外部链接 |
| isIframe | boolean | 是否内嵌 iframe |

## 权限模式

系统支持两种权限模式：

### 前端模式

在 `.env` 中设置：

```
VITE_ACCESS_MODE = frontend
```

前端模式下，路由配置在前端代码中定义，通过 `auth` 字段控制菜单显示。

### 后端模式

在 `.env` 中设置：

```
VITE_ACCESS_MODE = backend
```

后端模式下，路由配置从后端接口获取，支持动态菜单。

## 动态路由

后端模式下，系统会调用 `/auth/routes` 接口获取用户路由，并动态注册到 Vue Router。

```typescript
// 后端返回的路由数据会自动转换为前端路由格式
const routes = await fetchGetUserRoutes()
```
