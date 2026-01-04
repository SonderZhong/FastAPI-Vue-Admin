# 权限控制

## 权限模型

系统采用 RBAC（基于角色的访问控制）模型，支持三种权限类型：

- **菜单权限** - 控制用户可访问的页面
- **按钮权限** - 控制用户可执行的操作
- **API 权限** - 控制用户可调用的接口

## 权限架构

```
用户 -> 角色 -> 权限
```

- 一个用户可以拥有多个角色
- 一个角色可以拥有多个权限
- 权限通过 Casbin 进行管理

## 前端权限

### 按钮权限指令

使用 `v-auth` 指令控制按钮显示：

```vue
<template>
  <el-button v-auth="'user:btn:add'">新增用户</el-button>
  <el-button v-auth="['user:btn:edit', 'user:btn:delete']">编辑/删除</el-button>
</template>
```

### 权限判断函数

```typescript
import { usePermission } from '@/composables/usePermission'

const { hasPermission } = usePermission()

// 单个权限判断
if (hasPermission('user:btn:add')) {
  // ...
}

// 多个权限判断（满足其一）
if (hasPermission(['user:btn:edit', 'user:btn:delete'])) {
  // ...
}
```

## 后端权限

### API 权限装饰器

```python
from annotation.auth import Auth

@router.get("/users")
@Auth(permission_list=["user:btn:list", "GET:/user"])
async def get_users():
    pass
```

### 数据权限

系统支持四种数据权限范围：

| 值 | 说明 |
|---|------|
| 1 | 全部数据 |
| 2 | 本部门及下属部门 |
| 3 | 仅本部门 |
| 4 | 仅本人 |

```python
from utils.casbin import DataScope

# 获取用户数据权限范围
data_scope = await CasbinEnforcer.get_data_scope(user_id, permission_id)
```

## 权限标识规范

推荐使用以下格式：

- 菜单权限：`模块:menu`
- 按钮权限：`模块:btn:操作`
- API 权限：`METHOD:/path`

示例：
- `user:btn:add` - 用户新增按钮
- `user:btn:edit` - 用户编辑按钮
- `GET:/user` - 获取用户列表接口
- `POST:/user` - 创建用户接口
