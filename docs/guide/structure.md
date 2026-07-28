# 项目结构

本文档描述当前仓库的实际结构，重点以 2026-07-27 的工作树为准。

## 根目录

```text
FastAPI-Vue-Admin/
├── server/                 # 后端服务
├── web/                    # 前端项目
├── docs/                   # VitePress 文档
├── docker/                 # Docker 相关文件
├── README.md
├── README.en.md
└── docker-compose.yml
```

## 后端结构

```text
server/
├── main.py                 # 启动入口，检测是否已初始化
├── app.py                  # FastAPI 应用入口
├── config.yaml             # 仓库安全模板，初始化后会被覆写
├── annotation/             # 认证、日志等装饰器
├── core/                   # 核心业务与公共能力
├── exceptions/             # 异常定义和处理
├── middlewares/            # 中间件
├── modules/                # 按业务域组织的模块
├── resources/              # 静态资源、模板、数据文件
├── setup/                  # 初始化向导
├── utils/                  # 配置、数据库、缓存、响应等工具
└── fva_mcp/                # MCP 服务
```

### `modules/` 组织方式

当前后端不是旧版的平铺 `apis/` 结构，而是按业务聚合：

```text
modules/
├── user/
├── role/
├── department/
├── permission/
├── config/
├── notification/
└── ...
```

一个典型模块会包含：

```text
module-name/
├── model.py
├── schema.py
├── service.py
└── router.py
```

## 前端结构

```text
web/
├── .env
├── package.json
├── vite.config.ts
└── src/
    ├── api/
    ├── components/
    ├── composables/
    ├── config/
    ├── directives/
    ├── enums/
    ├── locales/
    ├── router/
    ├── store/
    ├── utils/
    └── views/
```

### 与当前项目状态相关的几点

- 国际化资源位于 `web/src/locales/langs/*.json`
- 当前前端默认使用后端路由模式，见 `web/.env`
- 登录、租户选择、系统管理页面都在 `web/src/views/` 下

## 初始化相关文件

准备首次运行时，重点关注：

- `server/main.py`
- `server/config.yaml`
- `server/setup/`

当前设计是：

1. 仓库内提交模板配置
2. 启动时检测 `initialized`
3. 未初始化则进入 setup
4. setup 完成后写入真实配置并切换到正式服务

## 文档与代码对齐原则

如果后续再调整结构，文档应优先和下面这些事实保持一致：

- 后端是否仍然以 `modules/` 为核心
- `server/config.yaml` 是否仍作为模板提交
- 前端是否仍默认后端路由模式
- 初始化入口是否仍由 `server/main.py` 控制
