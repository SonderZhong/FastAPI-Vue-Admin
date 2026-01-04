<div align="center">
  <h1>FastAPI-Vue-Admin</h1>
  <p>A modern admin system based on FastAPI + Vue 3 + Element Plus</p>
  <p>
    English | <a href="./README.md">简体中文</a>
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

## 📖 Introduction

FastAPI-Vue-Admin is a modern full-stack admin framework based on **FastAPI + Tortoise-ORM + Vue 3 + Element Plus**, featuring a separated frontend and backend architecture with an out-of-the-box enterprise solution.

- 📚 [Documentation](https://sonderzhong.github.io/FastAPI-Vue-Admin/)
- 🎯 [Live Demo](https://fva.hygc.site)

## ✨ Features

- 🚀 **High Performance** - FastAPI + Tortoise-ORM async architecture
- 🎯 **TypeScript Full Stack** - Vue 3 + TypeScript + Vite
- 🛡️ **Enterprise RBAC** - Casbin-based menu/button/API permission control
- 🤖 **AI-Driven Development** - Built-in MCP service for AI-assisted code generation
- 🎨 **Beautiful UI** - Element Plus + UnoCSS with dark mode support
- 🐳 **One-Click Deploy** - Docker Compose orchestration

## 🛠️ Tech Stack

| Backend | Frontend |
|---------|----------|
| FastAPI | Vue 3 |
| Tortoise-ORM | Element Plus |
| MySQL 8.0+ | TypeScript |
| Redis 6.0+ | Vite |
| Casbin | Pinia |
| Pydantic | UnoCSS |

## 🚀 Quick Start

### Requirements

- Python 3.9+
- Node.js 20+
- MySQL 8.0+
- Redis 6.0+
- pnpm 8+

### Start Backend

```bash
cd server
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py
```

First launch will redirect to the setup wizard at http://localhost:9090

### Start Frontend

```bash
cd web
pnpm install
pnpm dev
```

## 📦 Features

- User, Role, Department, Permission Management
- Operation Logs, Login Logs, Server Monitor, Cache Management
- Config Management, File Management, Notification Management
- MCP Service, AI-Assisted Code Generation

## 🙏 Acknowledgements

- [Gin-Vue-Admin](https://github.com/flipped-aurora/gin-vue-admin)
- [Art Design Pro](https://github.com/Daymychen/art-design-pro)
- [FastAPI](https://github.com/tiangolo/fastapi)

## 📄 License

[MIT License](./LICENSE) © 2026 SonderZhong
