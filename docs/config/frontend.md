# 🎨 前端配置

前端配置分为环境变量配置、Vite 构建配置和应用运行时配置。

## 📄 环境变量

环境变量文件位于 `web/` 目录下：

| 文件 | 说明 |
|------|------|
| `.env` | 所有环境通用配置 |
| `.env.development` | 开发环境配置 |
| `.env.production` | 生产环境配置 |

### 开发环境 `.env.development`

```bash
# 应用部署基础路径
VITE_BASE_URL = /

# API 请求地址（开发环境通过 Vite 代理）
VITE_API_URL = http://127.0.0.1:9090

# 代理目标地址
VITE_API_PROXY_URL = http://127.0.0.1:9090

# 是否移除 console
VITE_DROP_CONSOLE = false

# 开发服务器端口
VITE_PORT = 8080

# 应用版本
VITE_VERSION = 1.0.0
```

### 生产环境 `.env.production`

```bash
# 应用部署基础路径（如部署在子目录 /admin/）
VITE_BASE_URL = /

# API 请求地址（生产环境直接请求后端）
VITE_API_URL = https://api.example.com

# 是否移除 console
VITE_DROP_CONSOLE = true

# 应用版本
VITE_VERSION = 1.0.0
```

### 环境变量说明

| 变量 | 说明 |
|------|------|
| `VITE_BASE_URL` | 应用部署的基础路径，如部署在 `/admin/` 子目录则设置为 `/admin/` |
| `VITE_API_URL` | 后端 API 地址 |
| `VITE_PORT` | 开发服务器端口 |
| `VITE_DROP_CONSOLE` | 构建时是否移除 console 语句 |
| `VITE_VERSION` | 应用版本号 |

## ⚡ Vite 配置

Vite 配置文件 `web/vite.config.ts`：

```typescript
export default defineConfig({
  // 基础路径
  base: VITE_BASE_URL,
  
  // 开发服务器
  server: {
    port: 8080,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9090',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        ws: true  // WebSocket 代理
      }
    }
  },
  
  // 路径别名
  resolve: {
    alias: {
      '@': '/src',
      '@views': '/src/views',
      '@utils': '/src/utils',
      '@stores': '/src/store',
      '@styles': '/src/assets/styles'
    }
  },
  
  // 构建配置
  build: {
    target: 'es2015',
    outDir: 'dist',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
})
```

### 路径别名

| 别名 | 路径 | 说明 |
|------|------|------|
| `@` | `/src` | 源码目录 |
| `@views` | `/src/views` | 页面组件 |
| `@utils` | `/src/utils` | 工具函数 |
| `@stores` | `/src/store` | 状态管理 |
| `@styles` | `/src/assets/styles` | 样式文件 |
| `@imgs` | `/src/assets/img` | 图片资源 |
| `@icons` | `/src/assets/icons` | 图标资源 |

## 🎯 应用配置

### 系统配置

系统配置位于 `web/src/config/` 目录：

```typescript
// config/index.ts
export default {
  // 系统信息
  systemInfo: {
    name: 'FastAPI-Vue-Admin',
    version: '1.0.0'
  },
  
  // 默认首页路径
  homePath: '/dashboard/console',
  
  // 登录页路径
  loginPath: '/login',
  
  // 白名单路由（无需登录）
  whiteList: ['/login', '/register', '/forget-password'],
  
  // 请求超时时间（毫秒）
  requestTimeout: 30000
}
```

### 主题配置

主题配置通过 Pinia Store 管理，位于 `web/src/store/modules/setting.ts`：

```typescript
export const useSettingStore = defineStore('setting', {
  state: () => ({
    // 菜单布局类型
    menuType: 'left',
    
    // 主题模式：light/dark/system
    theme: 'light',
    
    // 主题色
    primaryColor: '#5D87FF',
    
    // 菜单是否展开
    menuOpen: true,
    
    // 是否显示进度条
    showNprogress: true,
    
    // 是否显示面包屑
    showBreadcrumb: true,
    
    // 是否显示标签页
    showWorktab: true,
    
    // 菜单手风琴模式
    uniqueOpened: true,
    
    // 是否显示页脚
    showFooter: true,
    
    // 是否固定头部
    fixedHeader: true
  }),
  
  persist: true  // 持久化存储
})
```

### 菜单布局类型

| 类型 | 值 | 说明 |
|------|-----|------|
| 左侧菜单 | `left` | 经典左侧导航布局 |
| 顶部菜单 | `top` | 顶部水平导航布局 |
| 混合菜单 | `top-left` | 顶部+左侧混合布局 |
| 双列菜单 | `dual-menu` | 双列导航布局 |

### 主题模式

| 模式 | 值 | 说明 |
|------|-----|------|
| 亮色 | `light` | 浅色主题 |
| 暗色 | `dark` | 深色主题 |
| 跟随系统 | `system` | 自动跟随系统设置 |

## 🌍 国际化配置

国际化配置位于 `web/src/locales/`：

```
locales/
├── index.ts          # 国际化入口
├── zh.ts             # 中文语言包
└── en.ts             # 英文语言包
```

### 语言包结构

```typescript
// locales/zh.ts
export default {
  common: {
    add: '新增',
    edit: '编辑',
    delete: '删除',
    search: '搜索',
    reset: '重置',
    confirm: '确认',
    cancel: '取消'
  },
  menus: {
    dashboard: '仪表盘',
    system: {
      title: '系统管理',
      user: '用户管理',
      role: '角色管理',
      department: '部门管理',
      permission: '权限管理'
    }
  },
  user: {
    username: '用户名',
    password: '密码',
    nickname: '昵称'
  }
}
```

### 使用国际化

```vue
<template>
  <!-- 模板中使用 -->
  <span>{{ $t('common.add') }}</span>
  <el-button>{{ $t('menus.system.user') }}</el-button>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 脚本中使用
const title = t('menus.dashboard')
</script>
```

## 🎨 UnoCSS 配置

UnoCSS 配置文件 `web/uno.config.ts`：

```typescript
import { defineConfig, presetUno, presetAttributify } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify()
  ],
  
  // 自定义快捷方式
  shortcuts: {
    'flex-center': 'flex items-center justify-center',
    'flex-between': 'flex items-center justify-between',
    'wh-full': 'w-full h-full'
  },
  
  // 主题配置
  theme: {
    colors: {
      primary: '#5D87FF',
      success: '#13DEB9',
      warning: '#FFAE1F',
      danger: '#FA896B'
    }
  }
})
```

### 常用原子类

| 类名 | 说明 |
|------|------|
| `flex` | display: flex |
| `items-center` | align-items: center |
| `justify-between` | justify-content: space-between |
| `w-full` | width: 100% |
| `h-full` | height: 100% |
| `p-4` | padding: 1rem |
| `m-2` | margin: 0.5rem |
| `text-primary` | color: var(--primary) |
| `bg-white` | background: white |
| `rounded` | border-radius: 0.25rem |

## 📝 TypeScript 配置

TypeScript 配置文件 `web/tsconfig.json`：

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ESNext", "DOM"],
    "skipLibCheck": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "exclude": ["node_modules", "dist"]
}
```
