# 项目介绍

## 📖 简介

[FastAPI-Vue-Admin](https://github.com/SonderZhong/FastAPI-Vue-Admin) 是一个基于 **FastAPI + Tortoise-ORM + Vue 3 + Element Plus** 的现代化全栈后台管理系统框架。

项目采用前后端分离架构，后端使用 Python 异步生态，前端使用 Vue 3 全家桶，旨在提供一套开箱即用、高效开发的企业级解决方案。

::: tip 🎯 设计理念
- **开箱即用** - 零配置快速启动，内置最佳实践
- **AI 驱动** - 深度集成 MCP 协议，AI 辅助代码生成
- **架构优雅** - 分层架构设计，目录结构清晰，模块职责明确
- **高性能** - 全异步架构，轻松应对高并发场景
:::

## ✨ 核心特性

<div class="feature-grid">

### 🚀 高性能异步架构
基于 FastAPI + Tortoise-ORM 的全异步技术栈，充分利用 Python 协程优势，API 响应快如闪电，轻松应对高并发场景。

### 🎯 TypeScript 全栈开发
Vue 3 + TypeScript + Vite 现代化前端技术栈，完整的类型支持，智能代码提示，开发体验丝滑流畅。

### 🛡️ 企业级权限控制
基于 Casbin 的 RBAC 权限引擎，支持菜单权限、按钮权限、API 权限三级管控，灵活配置，安全可靠。

### 🤖 AI 智能辅助
内置 FVA Helper MCP 服务，支持 AI 辅助生成 Model、Schema、API 代码，显著提升开发效率。

### 🎨 精美 UI 组件
Element Plus + UnoCSS 组件库，响应式布局，支持暗黑模式，视觉体验一流。

### 🐳 一键容器部署
完善的 Docker Compose 编排配置，前后端分离部署，运维省心省力。

</div>

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.100+ | 高性能异步 Web 框架 |
| [Tortoise-ORM](https://tortoise.github.io/) | 0.20+ | 异步 ORM 框架 |
| [Pydantic](https://docs.pydantic.dev/) | 2.0+ | 数据验证和序列化 |
| [Casbin](https://casbin.org/) | 1.0+ | 权限控制框架 |
| [MySQL](https://www.mysql.com/) | 8.0+ | 关系型数据库 |
| [Redis](https://redis.io/) | 6.0+ | 缓存和会话存储 |
| [Uvicorn](https://www.uvicorn.org/) | 0.23+ | ASGI 服务器 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| [Vue 3](https://vuejs.org/) | 3.4+ | 渐进式 JavaScript 框架 |
| [TypeScript](https://www.typescriptlang.org/) | 5.0+ | JavaScript 超集 |
| [Vite](https://vitejs.dev/) | 5.0+ | 下一代前端构建工具 |
| [Element Plus](https://element-plus.org/) | 2.4+ | Vue 3 UI 组件库 |
| [Pinia](https://pinia.vuejs.org/) | 2.1+ | Vue 状态管理 |
| [Vue Router](https://router.vuejs.org/) | 4.2+ | Vue 官方路由 |
| [UnoCSS](https://unocss.dev/) | 0.58+ | 原子化 CSS 引擎 |
| [Axios](https://axios-http.com/) | 1.6+ | HTTP 请求库 |

## 📦 功能模块

### 系统管理
- **用户管理** - 用户增删改查、状态管理、角色分配
- **角色管理** - 角色配置、权限分配、数据权限
- **部门管理** - 组织架构、树形结构、部门负责人
- **权限管理** - 菜单配置、按钮权限、API 权限

### 系统监控
- **操作日志** - 用户操作记录、请求追踪
- **登录日志** - 登录记录、IP 地址、设备信息
- **服务监控** - 服务器状态、CPU/内存/磁盘监控
- **缓存管理** - Redis 缓存查看、清理

### 系统工具
- **配置管理** - 系统参数配置、动态配置
- **文件管理** - 文件上传、存储管理
- **通知管理** - 系统通知、消息推送

### AI 辅助
- **MCP 服务** - AI 辅助开发工具集成
- **代码生成** - Model/Schema/API 一键生成

## 🖼️ 系统预览

::: tip 💡 在线体验
访问 [在线演示](https://fva.hygc.site) 查看完整系统功能。

默认账号：`admin` / `admin123@*`
:::

### 工作台
![工作台](/screenshots/dashboard.png)

### 用户管理
![用户管理](/screenshots/user.png)

### 权限管理
![权限管理](/screenshots/permission.png)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 参与项目贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 开源协议

本项目基于 [MIT](https://opensource.org/licenses/MIT) 协议开源。

## 🙏 鸣谢

感谢以下开源项目的启发和参考：

- [Gin-Vue-Admin](https://github.com/flipped-aurora/gin-vue-admin) - Go + Vue 全栈后台管理系统
- [Art Design Pro](https://github.com/Daymychen/art-design-pro) - Vue 3 企业级中后台前端解决方案
- [FastAPI](https://github.com/tiangolo/fastapi) - 高性能 Python Web 框架

<style>
.feature-grid {
  display: grid;
  gap: 1rem;
}

.feature-grid h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.feature-grid p {
  margin: 0;
  color: var(--vp-c-text-2);
  font-size: 0.95rem;
  line-height: 1.6;
}
</style>
