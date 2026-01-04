# 权限管理

## 获取权限列表

### 请求

```
GET /permission/list
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| menu_type | int | 否 | 权限类型（0菜单，1按钮，2接口） |

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": [
    {
      "id": "uuid",
      "menu_type": 0,
      "parent_id": null,
      "name": "System",
      "title": "系统管理",
      "path": "/system",
      "component": "Layout",
      "icon": "&#xe72b;",
      "order": 1,
      "children": [
        {
          "id": "uuid",
          "menu_type": 0,
          "parent_id": "uuid",
          "name": "User",
          "title": "用户管理",
          "path": "user",
          "component": "/system/user/index",
          "icon": "&#xe608;",
          "order": 1
        }
      ]
    }
  ]
}
```

## 获取权限详情

### 请求

```
GET /permission/{permission_id}
```

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "id": "uuid",
    "menu_type": 0,
    "parent_id": null,
    "name": "User",
    "title": "用户管理",
    "path": "/system/user",
    "component": "/system/user/index",
    "icon": "&#xe608;",
    "order": 1,
    "isHide": false,
    "keepAlive": true,
    "min_user_type": 3
  }
}
```

## 创建权限

### 请求

```
POST /permission
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| menu_type | int | 是 | 权限类型 |
| parent_id | string | 否 | 父权限 ID |
| name | string | 是 | 权限名称 |
| title | string | 否 | 显示标题 |
| path | string | 否 | 路由路径 |
| component | string | 否 | 组件路径 |
| icon | string | 否 | 图标 |
| order | int | 否 | 排序 |
| isHide | bool | 否 | 是否隐藏 |
| keepAlive | bool | 否 | 是否缓存 |
| authTitle | string | 否 | 按钮标题 |
| authMark | string | 否 | 权限标识 |
| api_path | string | 否 | API 路径 |
| api_method | string[] | 否 | HTTP 方法 |

### 响应

```json
{
  "code": 200,
  "msg": "创建成功",
  "success": true
}
```

## 更新权限

### 请求

```
PUT /permission/{permission_id}
```

### 参数

同创建权限，所有字段可选。

### 响应

```json
{
  "code": 200,
  "msg": "更新成功",
  "success": true
}
```

## 删除权限

### 请求

```
DELETE /permission/{permission_id}
```

### 响应

```json
{
  "code": 200,
  "msg": "删除成功",
  "success": true
}
```

## 权限类型说明

| 类型 | 值 | 说明 |
|------|---|------|
| 菜单 | 0 | 前端路由菜单 |
| 按钮 | 1 | 前端按钮权限 |
| 接口 | 2 | 后端 API 权限 |

## 数据权限范围

| 范围 | 值 | 说明 |
|------|---|------|
| 全部 | 1 | 可访问所有数据 |
| 本部门及下属 | 2 | 可访问本部门及下属部门数据 |
| 仅本部门 | 3 | 仅可访问本部门数据 |
| 仅本人 | 4 | 仅可访问本人数据 |
