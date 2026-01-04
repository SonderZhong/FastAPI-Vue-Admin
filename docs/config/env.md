# 环境变量

前端环境变量配置文件位于 `web/` 目录下。

## 配置文件

| 文件 | 说明 |
|------|------|
| `.env` | 通用环境变量 |
| `.env.development` | 开发环境变量 |
| `.env.production` | 生产环境变量 |

## 通用变量 (.env)

```bash
# 版本号
VITE_VERSION = 1.0.0

# 端口号
VITE_PORT = 8080

# 应用部署基础路径
VITE_BASE_URL = /

# API 地址
VITE_API_URL = http://127.0.0.1:9090

# 权限模式 frontend / backend
VITE_ACCESS_MODE = frontend

# 是否携带 Cookie
VITE_WITH_CREDENTIALS = false
```

## 开发环境 (.env.development)

```bash
# API 请求基础路径
VITE_API_URL = http://127.0.0.1:9090

# 代理目标地址
VITE_API_PROXY_URL = http://127.0.0.1:9090

# 是否删除 console
VITE_DROP_CONSOLE = false
```

## 生产环境 (.env.production)

```bash
# API 请求基础路径
VITE_API_URL = /api

# 是否删除 console
VITE_DROP_CONSOLE = true
```

## 变量说明

| 变量 | 说明 |
|------|------|
| VITE_VERSION | 应用版本号 |
| VITE_PORT | 开发服务器端口 |
| VITE_BASE_URL | 部署基础路径 |
| VITE_API_URL | API 请求地址 |
| VITE_ACCESS_MODE | 权限模式 |
| VITE_DROP_CONSOLE | 是否移除 console |

## 使用方式

在代码中通过 `import.meta.env` 访问：

```typescript
const apiUrl = import.meta.env.VITE_API_URL
const version = import.meta.env.VITE_VERSION
```

::: warning 注意
只有以 `VITE_` 开头的变量才会暴露给客户端代码。
:::
