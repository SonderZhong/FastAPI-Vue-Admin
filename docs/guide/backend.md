# 后端说明

FastAPI-Vue-Admin 后端位于 `server/`，当前结构以 `modules/` 为核心，而不是旧文档里的 `apis/`、`models/`、`schemas/` 三层拆分。

## 技术栈

- FastAPI
- Tortoise ORM
- Pydantic
- JWT
- Redis
- Loguru

## 当前目录结构

```text
server/
├── main.py
├── app.py
├── config.yaml
├── annotation/
├── core/
├── exceptions/
├── middlewares/
├── modules/
├── resources/
├── setup/
├── utils/
└── fva_mcp/
```

## 启动方式

`server/main.py` 会先检查 `server/config.yaml` 中的 `initialized` 字段。

- `initialized: false` 时，启动初始化向导
- `initialized: true` 时，启动正式后端服务

这也是当前仓库适合上传到 Git 的默认状态：仓库内保留一份安全模板配置，由初始化流程写入真实配置。

## 初始化流程

首次部署时建议这样启动：

```bash
cd server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

然后访问初始化向导页面，完成数据库、Redis、管理员账号等配置。初始化完成后，向导会覆写 `server/config.yaml`。

## 应用入口

`server/app.py` 是正式服务入口，负责：

- 注册中间件
- 注册异常处理
- 注册业务路由
- 初始化数据库与 Redis
- 挂载 API 文档与静态资源

## 模块组织

业务代码集中在 `server/modules/` 下，按领域拆分，例如：

- `modules/user`
- `modules/role`
- `modules/department`
- `modules/permission`
- `modules/config`
- `modules/notification`

每个模块通常包含：

- `model.py`
- `schema.py`
- `service.py`
- `router.py`

这种组织方式更贴近“按业务模块聚合”的开发模式，新增功能时优先沿用这个结构。

## 配置文件约定

仓库中的 `server/config.yaml` 应保持为可提交的模板状态：

- `initialized: false`
- 不包含真实 JWT 密钥
- 不包含生产数据库凭据

本地初始化或部署后的真实配置不建议直接提交回仓库。

## 权限与认证

权限控制主要通过这些位置协作完成：

- `annotation/auth.py`
- `middlewares/`
- `modules/permission/`
- `utils/permission*.py`

接口通常通过装饰器声明权限要求，数据权限则在服务层和过滤参数中生效。

## 上传 Git 前建议

在准备提交仓库前，至少确认这几件事：

- `server/config.yaml` 仍是模板配置
- `server/fva.db`、日志、上传文件未被提交
- 本地调试截图和浏览器缓存目录已被 `.gitignore` 忽略
- 文档描述与当前 `modules/` 架构一致
