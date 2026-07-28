---
layout: home

hero:
  name: FastAPI-Vue-Admin
  text: 轻量级全栈后台管理框架
  tagline: 基于 FastAPI、Tortoise ORM、Vue 3 与 Element Plus 的前后端分离管理系统
  image:
    src: /logo.png
    alt: FastAPI-Vue-Admin
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/getting-started
    - theme: alt
      text: 项目结构
      link: /guide/structure
    - theme: alt
      text: GitHub
      link: https://github.com/SonderZhong/FastAPI-Vue-Admin

features:
  - icon: API
    title: 异步后端
    details: 基于 FastAPI 与 Tortoise ORM，适合前后端分离的管理后台场景。
  - icon: TS
    title: Vue 3 + TypeScript
    details: 使用 Vite、Pinia、Vue Router 与 Element Plus 构建现代前端。
  - icon: RBAC
    title: 权限与租户
    details: 支持菜单、按钮、接口权限，以及租户与数据范围控制。
  - icon: Docs
    title: 初始化友好
    details: 仓库支持未初始化状态启动，便于二次部署、模板化分发与首次配置。
  - icon: UI
    title: 后台界面完整
    details: 覆盖用户、角色、权限、部门、通知、配置、缓存等常见后台模块。
  - icon: MCP
    title: 工程化扩展
    details: 保留清晰的模块边界，便于后续接入自动化生成、脚手架与自定义业务模块。
---

## 项目说明

FastAPI-Vue-Admin 是一个以后台管理为核心场景的全栈项目模板。当前仓库采用前后端分离结构：

- 后端位于 `server/`
- 前端位于 `web/`
- 文档位于 `docs/`

仓库支持“未初始化”状态提交与分发。首次部署时，后端会根据 `server/config.yaml` 的初始化标记决定进入初始化流程还是正常启动流程。

## 当前文档范围

本套文档重点说明当前仓库中已经存在并可验证的内容：

- 本地启动与初始化流程
- 前后端目录结构
- 后端模块组织方式
- 权限模型与路由模式

对于历史版本中已经移除或尚未在当前仓库中验证的能力，不在这里继续作为默认特性宣传。

## 推荐阅读顺序

1. [快速开始](/guide/getting-started)
2. [项目介绍](/guide/index)
3. [项目结构](/guide/structure)
4. [后端架构](/guide/backend)
5. [权限控制](/guide/permission)
