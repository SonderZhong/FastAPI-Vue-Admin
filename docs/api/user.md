# 用户管理

## 获取用户列表

### 请求

```
GET /user/list
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 10 |
| username | string | 否 | 用户名筛选 |
| nickname | string | 否 | 昵称筛选 |
| department_id | string | 否 | 部门 ID |
| status | int | 否 | 状态（1启用，0禁用） |

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 10,
    "result": [
      {
        "id": "uuid",
        "username": "admin",
        "nickname": "管理员",
        "email": "admin@example.com",
        "phone": "13800138000",
        "gender": 1,
        "status": 1,
        "department_name": "系统管理",
        "created_at": "2024-01-01T00:00:00"
      }
    ]
  }
}
```

## 获取用户详情

### 请求

```
GET /user/{user_id}
```

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "id": "uuid",
    "username": "admin",
    "nickname": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "avatar": "/files/avatar.png",
    "gender": 1,
    "user_type": 0,
    "department_id": "uuid",
    "status": 1,
    "remark": "备注",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

## 创建用户

### 请求

```
POST /user
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| nickname | string | 是 | 昵称 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机号 |
| gender | int | 否 | 性别（1男，2女） |
| department_id | string | 是 | 部门 ID |
| user_type | int | 否 | 用户类型 |
| status | int | 否 | 状态 |

### 响应

```json
{
  "code": 200,
  "msg": "创建成功",
  "success": true
}
```

## 更新用户

### 请求

```
PUT /user/{user_id}
```

### 参数

同创建用户，所有字段可选。

### 响应

```json
{
  "code": 200,
  "msg": "更新成功",
  "success": true
}
```

## 删除用户

### 请求

```
DELETE /user/{user_id}
```

### 响应

```json
{
  "code": 200,
  "msg": "删除成功",
  "success": true
}
```

## 重置密码

### 请求

```
PUT /user/{user_id}/reset-password
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| password | string | 否 | 新密码，不传则使用默认密码 |

### 响应

```json
{
  "code": 200,
  "msg": "密码重置成功",
  "success": true
}
```
