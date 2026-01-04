# 角色管理

## 获取角色列表

### 请求

```
GET /role/list
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 10 |
| name | string | 否 | 角色名称筛选 |
| department_id | string | 否 | 部门 ID |
| status | int | 否 | 状态 |

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 10,
    "result": [
      {
        "id": "uuid",
        "name": "管理员",
        "code": "admin",
        "description": "系统管理员",
        "department_id": "uuid",
        "department_name": "系统管理",
        "status": 1,
        "created_at": "2024-01-01T00:00:00"
      }
    ]
  }
}
```

## 获取角色详情

### 请求

```
GET /role/{role_id}
```

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "id": "uuid",
    "name": "管理员",
    "code": "admin",
    "description": "系统管理员",
    "department_id": "uuid",
    "status": 1,
    "permissions": ["uuid1", "uuid2"]
  }
}
```

## 创建角色

### 请求

```
POST /role
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 角色名称 |
| code | string | 是 | 角色编码 |
| description | string | 否 | 描述 |
| department_id | string | 是 | 部门 ID |
| status | int | 否 | 状态 |

### 响应

```json
{
  "code": 200,
  "msg": "创建成功",
  "success": true
}
```

## 更新角色

### 请求

```
PUT /role/{role_id}
```

### 参数

同创建角色，所有字段可选。

### 响应

```json
{
  "code": 200,
  "msg": "更新成功",
  "success": true
}
```

## 删除角色

### 请求

```
DELETE /role/{role_id}
```

### 响应

```json
{
  "code": 200,
  "msg": "删除成功",
  "success": true
}
```

## 分配权限

### 请求

```
PUT /role/{role_id}/permissions
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| permission_ids | string[] | 是 | 权限 ID 列表 |

### 响应

```json
{
  "code": 200,
  "msg": "权限分配成功",
  "success": true
}
```

## 获取角色权限

### 请求

```
GET /role/{role_id}/permissions
```

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "permissions": ["uuid1", "uuid2", "uuid3"]
  }
}
```
