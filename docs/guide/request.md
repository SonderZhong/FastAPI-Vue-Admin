# 请求和接口

## 请求封装

前端使用 Axios 进行 HTTP 请求，封装位于 `web/src/utils/request.ts`。

### 基本使用

```typescript
import request from '@/utils/request'

// GET 请求
const response = await request.get('/user/list', { params: { page: 1 } })

// POST 请求
const response = await request.post('/user', { username: 'admin' })

// PUT 请求
const response = await request.put('/user/1', { nickname: '管理员' })

// DELETE 请求
const response = await request.delete('/user/1')
```

### API 模块化

API 接口按模块组织在 `web/src/api/` 目录下：

```typescript
// api/system/user.ts
import request from '@/utils/request'

export function fetchUserList(params: UserListParams) {
  return request.get<UserListResponse>('/user/list', { params })
}

export function createUser(data: CreateUserParams) {
  return request.post<BaseResponse>('/user', data)
}
```

## 响应格式

后端统一响应格式：

```json
{
  "code": 200,
  "msg": "操作成功",
  "success": true,
  "data": {},
  "time": "2024-01-01T00:00:00"
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| code | number | 状态码 |
| msg | string | 提示信息 |
| success | boolean | 是否成功 |
| data | any | 响应数据 |
| time | string | 响应时间 |

## 错误处理

请求拦截器会自动处理常见错误：

- **401** - 未授权，跳转登录页
- **403** - 无权限访问
- **404** - 资源不存在
- **500** - 服务器错误

```typescript
// 自定义错误处理
try {
  const response = await fetchUserList({ page: 1 })
} catch (error) {
  console.error('请求失败:', error)
}
```

## 后端接口

### 路由定义

```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/user")

@router.get("/list")
async def get_user_list(
    page: int = 1,
    page_size: int = 10
):
    # 业务逻辑
    return ResponseUtil.success(data=result)
```

### 参数验证

使用 Pydantic 进行参数验证：

```python
from pydantic import BaseModel, Field

class CreateUserParams(BaseModel):
    username: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6)
    email: str | None = None
```
