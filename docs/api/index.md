# API 接口文档

## 在线文档

项目集成了 Swagger UI 交互式 API 文档，可以直接在线测试接口。

::: tip 访问地址
- **后端直接访问**: `http://localhost:9090/docs`
- **前端代理访问**: `http://localhost/api/docs`

生产环境请将 `localhost` 替换为实际域名。
:::

## 认证接口

## 登录

### 请求

```
POST /auth/login
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名/邮箱/手机号 |
| password | string | 是 | 密码 |
| captcha | string | 否 | 验证码 |
| captcha_key | string | 否 | 验证码 Key |

### 响应

```json
{
  "code": 200,
  "msg": "登录成功",
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

## 获取用户信息

### 请求

```
GET /auth/info
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
    "department_name": "系统管理",
    "status": 1
  }
}
```

## 获取用户路由

### 请求

```
GET /auth/routes
```

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "routes": [
      {
        "name": "Dashboard",
        "path": "/dashboard",
        "component": "Layout",
        "meta": {
          "title": "仪表盘",
          "icon": "&#xe721;"
        },
        "children": []
      }
    ]
  }
}
```

## 退出登录

### 请求

```
POST /auth/logout
```

### 响应

```json
{
  "code": 200,
  "msg": "退出成功",
  "success": true
}
```

## 获取验证码

### 请求

```
GET /auth/captcha
```

### 响应

```json
{
  "code": 200,
  "success": true,
  "data": {
    "key": "captcha_key",
    "image": "data:image/png;base64,..."
  }
}
```

## 注册

### 请求

```
POST /auth/register
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| email | string | 是 | 邮箱 |
| email_code | string | 是 | 邮箱验证码 |
| nickname | string | 否 | 昵称 |
| phone | string | 否 | 手机号 |

### 响应

```json
{
  "code": 200,
  "msg": "注册成功",
  "success": true
}
```
