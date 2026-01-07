<div align="center">
  <h1>FastAPI-Vue-Admin</h1>
  <p>基于 FastAPI + Vue 3 + Element Plus 的现代化后台管理系统</p>
  <p>
    <a href="./README.en.md">English</a> | 简体中文
  </p>
  <p>
    <a href="https://github.com/SonderZhong/FastAPI-Vue-Admin/blob/main/LICENSE">
      <img src="https://img.shields.io/github/license/SonderZhong/FastAPI-Vue-Admin" alt="license">
    </a>
    <a href="https://github.com/SonderZhong/FastAPI-Vue-Admin/stargazers">
      <img src="https://img.shields.io/github/stars/SonderZhong/FastAPI-Vue-Admin" alt="stars">
    </a>
    <a href="https://github.com/SonderZhong/FastAPI-Vue-Admin/forks">
      <img src="https://img.shields.io/github/forks/SonderZhong/FastAPI-Vue-Admin" alt="forks">
    </a>
  </p>
</div>

## 📖 简介

FastAPI-Vue-Admin 是一个基于 **FastAPI + Tortoise-ORM + Vue 3 + Element Plus** 的现代化全栈后台管理系统框架，采用前后端分离架构，提供开箱即用的企业级解决方案。

- 📚 [在线文档](https://sonderzhong.github.io/FastAPI-Vue-Admin/)
- 🎯 [在线演示](https://fva.hygc.site) - 账号：`admin` 密码：`admin123@*`
- 📡 [API 文档 (Apifox)](https://6cpx06bzzy.apifox.cn)
- 📡 [API 文档 (内置)](https://fva.hygc.site/api/docs)

## ✨ 特性

- 🚀 **高性能异步** - FastAPI + Tortoise-ORM 全异步架构
- 🎯 **TypeScript 全栈** - Vue 3 + TypeScript + Vite
- 🛡️ **企业级权限** - Casbin RBAC，菜单/按钮/API 三级管控
- 🤖 **AI 驱动开发** - 内置 MCP 服务，AI 辅助生成代码
- 🎨 **精美 UI** - Element Plus + UnoCSS，支持暗黑模式
- 🐳 **一键部署** - Docker Compose 编排

## 🛠️ 技术栈

| 后端 | 前端 |
|------|------|
| FastAPI | Vue 3 |
| Tortoise-ORM | Element Plus |
| MySQL 8.0+ | TypeScript |
| Redis 6.0+ | Vite |
| Casbin | Pinia |
| Pydantic | UnoCSS |

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 20+
- MySQL 8.0+
- Redis 6.0+
- pnpm 8+

### 启动后端

```bash
cd server
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py
```

首次启动会自动进入初始化向导页面 http://localhost:9090

### 启动前端

```bash
cd web
pnpm install
pnpm dev
```

## 📦 功能模块

- 用户管理、角色管理、部门管理、权限管理
- 操作日志、登录日志、服务监控、缓存管理
- 配置管理、文件管理、通知管理
- MCP 服务、AI 辅助代码生成

## 🙏 鸣谢

- [Gin-Vue-Admin](https://github.com/flipped-aurora/gin-vue-admin)
- [Art Design Pro](https://github.com/Daymychen/art-design-pro)
- [FastAPI](https://github.com/tiangolo/fastapi)

## 📄 开源协议

[MIT License](./LICENSE) © 2026 SonderZhong
