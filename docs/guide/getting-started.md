# 快速开始

本文将帮助你从零开始搭建 FastAPI-Vue-Admin 开发环境。

## 📋 环境要求

在开始之前，请确保你的开发环境满足以下要求：

| 环境 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.9+ | 推荐 3.11+ |
| Node.js | 20.19.0+ | 推荐使用 LTS 版本 |
| pnpm | 8.8.0+ | 前端包管理器 |
| MySQL | 8.0+ | 关系型数据库 |
| Redis | 6.0+ | 缓存数据库 |

::: tip 💡 版本检查
```bash
python --version    # Python 3.11.x
node --version      # v20.19.x
pnpm --version      # 8.x.x
mysql --version     # mysql Ver 8.0.x
redis-server -v     # Redis server v=7.x.x
```
:::

## 📥 获取代码

```bash
# 克隆仓库
git clone <repository-url>
cd fastapi-vue-admin
```

## 🔧 后端配置

### 1. 创建虚拟环境

::: code-group

```bash [Windows]
cd server
python -m venv venv
venv\Scripts\activate
```

```bash [Linux/Mac]
cd server
python -m venv venv
source venv/bin/activate
```

:::

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

::: warning ⚠️ 首次启动
首次启动时，系统会检测到 `config.yaml` 不存在，自动进入**初始化向导页面**：

1. 访问 http://localhost:9090
2. 按照页面提示配置数据库连接
3. 配置 Redis 连接
4. 设置管理员账号
5. 完成初始化

初始化完成后，系统会自动创建 `config.yaml` 配置文件。
:::

## 🎨 前端配置

### 1. 安装依赖

```bash
cd web
pnpm install
```

### 2. 启动开发服务器

```bash
pnpm dev
```

### 3. 环境变量配置

前端环境变量位于 `web/.env.*` 文件中：

```bash
# .env.development - 开发环境
VITE_BASE_API = /api           # API 基础路径
VITE_ACCESS_MODE = backend     # 权限模式：frontend/backend
```

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:8080 | Vue 开发服务器 |
| 后端 API | http://127.0.0.1:9090 | FastAPI 服务 |
| API 文档 | http://127.0.0.1:9090/docs | Swagger UI |
| ReDoc | http://127.0.0.1:9090/redoc | ReDoc 文档 |

## 🔑 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 超级管理员 |

::: danger 🔒 安全提示
生产环境部署前，请务必修改默认密码！
:::

## 🐳 Docker 快速部署

如果你更喜欢使用 Docker，可以一键启动所有服务：

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

::: details 📦 查看 docker-compose.yml 配置

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./server
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "9090:9090"
    depends_on:
      - mysql
      - redis
    environment:
      - DATABASE_HOST=mysql
      - REDIS_HOST=redis

  frontend:
    build:
      context: ./web
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: fva
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

:::

## ❓ 常见问题

### Q: 后端启动报错 "ModuleNotFoundError"

确保已激活虚拟环境并安装了所有依赖：

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 重新安装依赖
pip install -r requirements.txt
```

### Q: 前端启动报错 "pnpm: command not found"

安装 pnpm：

```bash
npm install -g pnpm
```

### Q: 数据库连接失败

1. 确保 MySQL 服务已启动
2. 检查 `config.yaml` 中的数据库配置
3. 确保数据库用户有足够权限

### Q: Redis 连接失败

1. 确保 Redis 服务已启动
2. 检查 `config.yaml` 中的 Redis 配置
3. 如果 Redis 设置了密码，确保配置正确

## 📚 下一步

恭喜你完成了环境搭建！接下来可以：

- 📁 了解 [项目结构](./structure.md) - 熟悉代码组织方式
- 🛣️ 学习 [路由和菜单](./router.md) - 配置系统菜单
- 🔐 掌握 [权限控制](./permission.md) - 理解权限机制
- 🤖 探索 [MCP 服务](./mcp.md) - 使用 AI 辅助开发
