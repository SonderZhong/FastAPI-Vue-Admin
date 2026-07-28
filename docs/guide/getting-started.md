# 快速开始

本文档以当前仓库中已经存在并验证过的启动方式为准。

## 环境要求

- Python 3.9+
- Node.js 20+
- pnpm 8+
- Redis（可选，是否使用取决于初始化配置）

## 获取代码

```bash
git clone <your-repo-url>
cd FastAPI-Vue-Admin
```

## 后端启动

```bash
cd server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 初始化说明

仓库中的 `server/config.yaml` 默认应保持模板状态：

```yaml
initialized: false
```

这意味着首次运行 `python main.py` 时，会进入初始化向导，而不是直接加载正式业务配置。

初始化前后的行为如下：

- 未初始化：启动 setup 服务
- 已初始化：启动正式 FastAPI 服务

如果你准备把项目上传到 Git，请不要把本地初始化后生成的真实密钥、数据库配置和运行态数据一并提交回仓库。

## 前端启动

```bash
cd web
pnpm install
pnpm dev
```

默认本地开发地址通常为：

- 前端：`http://localhost:8080`
- 后端：由初始化完成后的 `server/config.yaml` 决定

环境变量默认值说明：

- `web/.env.development` 用于本地开发，默认指向 `http://127.0.0.1:9090`
- `web/.env.production` 用于生产构建，默认使用相对路径 `/api`
- 如果生产环境不是通过反向代理把 `/api` 转发到后端，需要在部署时自行覆盖 `VITE_API_URL`

## 路由模式

当前前端默认使用后端路由模式，相关配置见：

```text
web/.env
```

关键项为：

```env
VITE_ACCESS_MODE=backend
```

## 上传到 Git 前的最小检查项

- `server/config.yaml` 仍是模板配置
- Redis 默认模式保持为 `memory`
- `.gitignore` 已忽略本地缓存、截图、虚拟环境和依赖目录
- `server/fva.db` 等本地数据库文件未纳入版本控制
- 登录页、租户选择页和关键入口页面可以正常打开
- 关键文档不包含乱码和真实敏感配置
