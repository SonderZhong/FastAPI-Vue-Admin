# 项目介绍

## 简介

FastAPI-Vue-Admin 是一个面向后台管理场景的前后端分离项目，当前技术栈主要包括：

- 后端：FastAPI、Tortoise ORM、Pydantic
- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia

项目目标是提供一套可直接二次开发的后台基础框架，而不是只展示静态页面。

## 当前仓库的真实结构

当前后端以 `server/modules/` 为核心组织业务模块，常见模块包括：

- `auth`
- `user`
- `role`
- `permission`
- `department`
- `notification`
- `config`
- `file`
- `tenant`

前端页面位于 `web/src/views/`，路由与权限控制在 `web/src/router/` 与 `web/src/store/` 中完成。

## 已验证的关键能力

结合当前代码与本地联调结果，已经确认以下能力存在并可工作：

- 登录页可正常加载
- 登录成功后，如账号关联多个租户，会进入租户选择页
- 系统支持后端返回用户路由
- 页面标题与登录相关页面已接入 i18n
- 项目支持未初始化状态启动初始化流程

## 初始化与模板分发

这个仓库现在适合作为“未初始化模板”上传 Git，前提是保留以下约束：

- `server/config.yaml` 中 `initialized` 必须为 `false`
- 不提交真实的 JWT 密钥、数据库密码、邮件密码等敏感配置
- 不提交本地数据库文件、缓存文件、临时截图与调试目录

初始化完成后，部署环境会生成自己的实际配置与运行数据。

## 默认账号说明

当前文档中提到的默认账号仅适用于本地示例数据或开发环境，不应被视为生产环境约定。上传模板仓库时，更重要的是：

- 保证初始化入口可用
- 保证未初始化状态下不会泄露真实密钥
- 保证 README 与文档能正确指导首次部署

## 下一步阅读

- [快速开始](./getting-started.md)
- [项目结构](./structure.md)
- [后端架构](./backend.md)
- [权限控制](./permission.md)
## 更新记录
- [2026-07-28 版本更新](./changelog-2026-07-28.md)
