# 权限控制

## 权限模型

当前项目采用基于角色的访问控制模型，权限来源可以概括为：

`用户 -> 角色 -> 权限`

系统中的权限主要分为三类：

- 菜单权限：控制用户能看到哪些页面和导航项
- 按钮权限：控制用户能执行哪些页面操作
- 接口权限：控制后端接口是否允许访问

## 前端权限控制

前端常见的权限使用方式有两种。

### `v-auth` 指令

```vue
<template>
  <el-button v-auth="'user:btn:add'">新增用户</el-button>
  <el-button v-auth="['user:btn:edit', 'user:btn:delete']">编辑/删除</el-button>
</template>
```

### 组合式权限判断

```ts
import { usePermission } from '@/composables/usePermission'

const { hasPermission } = usePermission()

if (hasPermission('user:btn:add')) {
  // ...
}

if (hasPermission(['user:btn:edit', 'user:btn:delete'])) {
  // ...
}
```

## 后端权限控制

后端接口通过装饰器和权限服务控制访问。

### 接口权限装饰器

```python
from annotation.auth import Auth

@router.get("/list")
@Auth(permission_list=["user:btn:list", "GET:/user/list"])
async def get_user_list():
    ...
```

项目中也会结合登录态、租户信息与数据范围做进一步判断。

## 数据权限

当前项目包含数据范围控制能力，后端会根据角色配置决定用户可访问的数据集合。

示例：

```python
from utils.permission import PermissionService

data_scope = await PermissionService.get_data_scope(user_id)
```

常见语义包括：

- 全部数据
- 本部门及下级部门
- 仅本部门
- 仅本人

具体取值与实现以当前后端服务代码为准，不建议在文档里硬编码旧版常量说明而不校验代码。

## 权限标识建议

当前项目中的权限标识通常遵循以下约定：

- 菜单权限：`module:menu`
- 按钮权限：`module:btn:action`
- 接口权限：`METHOD:/path`

示例：

- `user:btn:add`
- `user:btn:edit`
- `role:btn:assign`
- `GET:/user/list`
- `POST:/role/add`

## 路由来源

项目支持根据运行模式加载路由：

- 前端模式：使用本地定义的异步路由
- 后端模式：通过后端接口返回当前用户可访问路由

这意味着“是否能看到某个系统管理菜单”不仅取决于前端页面本身，也取决于：

- 当前登录账号绑定的角色
- 后端返回的用户路由
- 前端路由守卫是否已完成动态注册

## 初始化前的注意点

准备把项目作为模板仓库上传 Git 时，权限文档应尽量描述“当前代码真实存在的行为”，避免继续保留以下不准确内容：

- 旧接口路径示例
- 已移除字段或旧版用户类型逻辑
- 未经验证的固定角色说明

如果后续继续调整权限模型，建议同步检查：

- `server/modules/permission/`
- `server/modules/role/`
- `server/modules/user/`
- `web/src/router/`
- `web/src/store/`
