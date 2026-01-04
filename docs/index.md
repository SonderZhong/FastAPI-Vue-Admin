---
layout: home

hero:
  name: FastAPI-Vue-Admin
  text: 轻量级全栈后台管理框架
  tagline: 🔥 FastAPI + Vue 3 + Element Plus，开箱即用的企业级解决方案
  image:
    src: /logo.svg
    alt: FastAPI-Vue-Admin
  actions:
    - theme: brand
      text: 🚀 快速开始
      link: /guide/getting-started
    - theme: alt
      text: ⭐ GitHub
      link: https://github.com/SonderZhong/FastAPI-Vue-Admin
    - theme: alt
      text: 📖 在线预览
      link: https://fva.hygc.site

features:
  - icon: ⚡
    title: 高性能异步
    details: FastAPI + Tortoise-ORM 异步架构，轻松应对高并发场景，API 响应快如闪电
  - icon: 🎯
    title: TypeScript 全栈
    details: Vue 3 + TypeScript + Vite，完整的类型支持，开发体验丝滑流畅
  - icon: 🛡️
    title: 企业级权限
    details: Casbin RBAC 权限引擎，菜单/按钮/API 三级管控，安全可靠
  - icon: 🤖
    title: AI 驱动开发
    details: 内置 MCP 服务，AI 辅助生成 Model、Schema、API，效率翻倍
  - icon: 🎨
    title: 精美 UI 组件
    details: Element Plus + UnoCSS，响应式布局，暗黑模式，视觉体验一流
  - icon: 🐳
    title: 一键部署
    details: Docker Compose 编排，前后端分离部署，运维省心省力
---

<style>
:root {
  --vp-home-hero-name-color: transparent;
  --vp-home-hero-name-background: linear-gradient(135deg, #5D87FF 0%, #38C0FC 50%, #667eea 100%);
  --vp-home-hero-image-background-image: linear-gradient(135deg, rgba(93, 135, 255, 0.2) 0%, rgba(56, 192, 252, 0.2) 100%);
  --vp-home-hero-image-filter: blur(56px);
}

.dark {
  --vp-home-hero-image-background-image: linear-gradient(135deg, rgba(93, 135, 255, 0.15) 0%, rgba(56, 192, 252, 0.15) 100%);
}

/* Features 悬停效果 */
.VPFeature {
  transition: all 0.3s ease;
}

.VPFeature:hover {
  background: linear-gradient(135deg, rgba(93, 135, 255, 0.1) 0%, rgba(56, 192, 252, 0.1) 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(93, 135, 255, 0.15);
}

.dark .VPFeature:hover {
  background: linear-gradient(135deg, rgba(93, 135, 255, 0.15) 0%, rgba(56, 192, 252, 0.15) 100%) !important;
  box-shadow: 0 8px 24px rgba(93, 135, 255, 0.2);
}
</style>
