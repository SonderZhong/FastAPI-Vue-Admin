# 🎨 前端知识库

FastAPI-Vue-Admin 前端基于 **Vue 3 + TypeScript + Vite + Element Plus** 构建，采用现代化的前端开发技术栈。

## 🚀 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| 核心框架 | Vue 3 | Composition API |
| 开发语言 | TypeScript | 类型安全 |
| 构建工具 | Vite 5 | 极速热更新 |
| UI 组件 | Element Plus | Vue 3 组件库 |
| 状态管理 | Pinia | Vue 官方状态管理 |
| 路由 | Vue Router 4 | 官方路由 |
| CSS 引擎 | UnoCSS | 原子化 CSS |
| HTTP 请求 | Axios | 请求封装 |
| 图表 | ECharts | 数据可视化 |
| 国际化 | Vue I18n | 多语言支持 |

## 📁 目录结构

```
web/
├── src/
│   ├── api/                # API 接口
│   ├── assets/             # 静态资源
│   │   ├── icons/          # 图标字体
│   │   ├── img/            # 图片资源
│   │   └── styles/         # 样式文件
│   ├── components/         # 公共组件
│   │   └── core/           # 核心组件
│   ├── composables/        # 组合式函数
│   ├── config/             # 配置文件
│   ├── directives/         # 自定义指令
│   ├── enums/              # 枚举定义
│   ├── locales/            # 国际化
│   ├── router/             # 路由配置
│   │   ├── guards/         # 路由守卫
│   │   ├── routes/         # 路由模块
│   │   └── utils/          # 路由工具
│   ├── store/              # 状态管理
│   │   └── modules/        # Store 模块
│   ├── types/              # 类型定义
│   ├── utils/              # 工具函数
│   ├── views/              # 页面组件
│   ├── App.vue             # 根组件
│   └── main.ts             # 入口文件
├── .env                    # 环境变量
├── .env.development        # 开发环境变量
├── .env.production         # 生产环境变量
├── vite.config.ts          # Vite 配置
├── uno.config.ts           # UnoCSS 配置
└── package.json            # 依赖配置
```

## 🎯 启动流程

### 入口文件 `main.ts`

```typescript
import App from './App.vue'
import { createApp } from 'vue'
import { initStore } from './store'       // 初始化 Store
import { initRouter } from './router'     // 初始化路由
import language from './locales'          // 国际化
import { setupGlobDirectives } from './directives'  // 全局指令

const app = createApp(App)
initStore(app)           // 注册 Pinia
initRouter(app)          // 注册路由
setupGlobDirectives(app) // 注册指令
app.use(language)        // 注册国际化
app.mount('#app')
```

## 📂 核心模块详解

### 1. API 接口层 (`api/`)

API 接口按功能模块组织：

| 文件/目录 | 说明 |
|-----------|------|
| `auth.ts` | 认证接口（登录、登出、刷新Token） |
| `dashboard.ts` | 仪表盘接口（统计数据） |
| `system-manage.ts` | 系统管理接口 |
| `system/` | 系统管理模块接口 |
| `common/` | 通用接口 |

**接口定义示例：**

```typescript
// api/system/user.ts
import request from '@/utils/http/request'

// 获取用户列表
export function fetchUserList(params: UserListParams) {
  return request.get<UserListResponse>('/user/list', { params })
}

// 创建用户
export function createUser(data: CreateUserParams) {
  return request.post<BaseResponse>('/user', data)
}

// 更新用户
export function updateUser(id: string, data: UpdateUserParams) {
  return request.put<BaseResponse>(`/user/${id}`, data)
}

// 删除用户
export function deleteUser(id: string) {
  return request.delete<BaseResponse>(`/user/${id}`)
}
```

### 2. Store 状态管理 (`store/`)

基于 Pinia 的状态管理：

| 模块 | 说明 |
|------|------|
| `auth.ts` | 认证状态（Token、登录状态） |
| `user.ts` | 用户信息（用户数据、权限） |
| `menu.ts` | 菜单状态（菜单列表、展开状态） |
| `setting.ts` | 系统设置（主题、布局） |
| `worktab.ts` | 工作标签页 |
| `table.ts` | 表格状态 |

**Store 示例：**

```typescript
// store/modules/user.ts
import { defineStore } from  'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null as UserInfo | null,
    permissions: [] as string[],
    roles: [] as string[]
  }),

  getters: {
    // 获取用户名
    username: (state) => state.userInfo?.username || '',
    // 判断是否有权限
    hasPermission: (state) => (permission: string) => {
      return state.permissions.includes(permission)
    }
  },

  actions: {
    // 设置用户信息
    setUserInfo(info: UserInfo) {
      this.userInfo = info
      this.permissions = info.permissions || []
      this.roles = info.roles || []
    },
    // 清除用户信息
    clearUserInfo() {
      this.userInfo = null
      this.permissions = []
      this.roles = []
    }
  },

  persist: true  // 持久化存储
})
```

### 3. Router 路由 (`router/`)

| 文件/目录 | 说明 |
|-----------|------|
| `index.ts` | 路由实例 |
| `routesAlias.ts` | 路由别名配置 |
| `routes/` | 路由模块定义 |
| `guards/` | 路由守卫 |
| `utils/` | 路由工具函数 |

**路由配置示例：**

```typescript
// router/routes/modules/system.ts
import { RoutesAlias } from '@/router/routesAlias'
import type { AppRouteRecord } from '@/types/router'

export const routes: AppRouteRecord[] = [
  {
    name: 'System',
    path: '/system',
    component: RoutesAlias.Layout,
    meta: {
      title: 'menus.system.title',
      icon: '&#xe72b;',
      order: 2
    },
    children: [
      {
        path: 'user',
        name: 'User',
        component: '/system/user/index',
        meta: {
          title: 'menus.system.user',
          icon: '&#xe608;',
          auth: ['user:btn:list']
        }
      }
    ]
  }
]
```

**路由守卫：**

```typescript
// router/guards/permission.ts
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const userStore = useUserStore()

  // 白名单路由直接放行
  if (whiteList.includes(to.path)) {
    next()
    return
  }

  // 未登录跳转登录页
  if (!authStore.token) {
    next(`/login?redirect=${to.path}`)
    return
  }

  // 已登录但无用户信息，获取用户信息
  if (!userStore.userInfo) {
    await userStore.getUserInfo()
  }

  next()
})
```

### 4. Utils 工具函数 (`utils/`)

| 目录 | 说明 |
|------|------|
| `http/` | HTTP 请求封装 |
| `storage/` | 本地存储封装 |
| `permission/` | 权限判断工具 |
| `theme/` | 主题切换工具 |
| `validation/` | 表单验证工具 |
| `dataprocess/` | 数据处理工具 |
| `browser/` | 浏览器相关工具 |
| `navigation/` | 导航工具 |
| `socket/` | WebSocket 工具 |
| `table/` | 表格工具 |
| `ui/` | UI 相关工具 |
| `sys/` | 系统工具 |

**HTTP 请求封装：**

```typescript
// utils/http/request.ts
import axios from 'axios'
import { useAuthStore } from '@/store/modules/auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { code, msg, data } = response.data
    if (code === 200) {
      return data
    }
    // 401 未授权
    if (code === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    ElMessage.error(msg || '请求失败')
    return Promise.reject(new Error(msg))
  },
  (error) => {
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request
```

### 5. Directives 自定义指令 (`directives/`)

**权限指令 v-auth：**

```typescript
// directives/auth.ts
import type { Directive } from 'vue'
import { useUserStore } from '@/store/modules/user'

export const auth: Directive = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const permission = binding.value

    // 支持单个权限或权限数组
    const permissions = Array.isArray(permission) ? permission : [permission]
    
    // 检查是否有权限
    const hasPermission = permissions.some(p => 
      userStore.permissions.includes(p)
    )

    // 无权限则移除元素
    if (!hasPermission) {
      el.parentNode?.removeChild(el)
    }
  }
}
```

**使用示例：**

```vue
<template>
  <!-- 单个权限 -->
  <el-button v-auth="'user:btn:add'">新增</el-button>
  
  <!-- 多个权限（满足其一） -->
  <el-button v-auth="['user:btn:edit', 'user:btn:delete']">
    编辑/删除
  </el-button>
</template>
```

### 6. Composables 组合式函数 (`composables/`)

**权限判断：**

```typescript
// composables/usePermission.ts
import { useUserStore } from '@/store/modules/user'

export function usePermission() {
  const userStore = useUserStore()

  // 判断是否有权限
  const hasPermission = (permission: string | string[]) => {
    const permissions = Array.isArray(permission) ? permission : [permission]
    return permissions.some(p => userStore.permissions.includes(p))
  }

  // 判断是否有角色
  const hasRole = (role: string | string[]) => {
    const roles = Array.isArray(role) ? role : [role]
    return roles.some(r => userStore.roles.includes(r))
  }

  return { hasPermission, hasRole }
}
```

**使用示例：**

```vue
<script setup lang="ts">
import { usePermission } from '@/composables/usePermission'

const { hasPermission } = usePermission()

// 在逻辑中判断权限
if (hasPermission('user:btn:add')) {
  // 有权限的逻辑
}
</script>
```

## ⚙️ 配置文件

### 环境变量

```bash
# .env.development - 开发环境
VITE_BASE_URL = /                          # 应用基础路径
VITE_API_URL = http://127.0.0.1:9090       # API 地址
VITE_DROP_CONSOLE = false                  # 是否移除 console

# .env.production - 生产环境
VITE_BASE_URL = /
VITE_API_URL = https://api.example.com
VITE_DROP_CONSOLE = true
```

### Vite 配置

```typescript
// vite.config.ts
export default defineConfig({
  // 路径别名
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@views': resolvePath('src/views'),
      '@utils': resolvePath('src/utils'),
      '@stores': resolvePath('src/store')
    }
  },
  // 开发服务器
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9090',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  // 构建配置
  build: {
    target: 'es2015',
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

## 🎨 主题定制

### Element Plus 主题

```scss
// assets/styles/el-light.scss
@forward 'element-plus/theme-chalk/src/common/var.scss' with (
  $colors: (
    'primary': (
      'base': #5D87FF,
    ),
    'success': (
      'base': #13DEB9,
    ),
    'warning': (
      'base': #FFAE1F,
    ),
    'danger': (
      'base': #FA896B,
    )
  )
);
```

### 暗黑模式

```typescript
// utils/theme/dark.ts
export function toggleDarkMode(isDark: boolean) {
  if (isDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}
```

## 🛠️ 开发指南

### 新增页面

1. **创建页面组件** `views/example/index.vue`

```vue
<template>
  <div class="example-page">
    <el-card>
      <template #header>
        <span>示例页面</span>
      </template>
      <el-table :data="tableData" v-loading="loading">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button v-auth="'example:btn:edit'" @click="handleEdit(row)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchExampleList } from '@/api/example'

const loading = ref(false)
const tableData = ref([])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchExampleList()
    tableData.value = res.list
  } finally {
    loading.value = false
  }
}

const handleEdit = (row: any) => {
  // 编辑逻辑
}

onMounted(() => {
  loadData()
})
</script>
```

2. **添加路由配置** `router/routes/modules/example.ts`

```typescript
export const routes = [
  {
    name: 'Example',
    path: '/example',
    component: '/example/index',
    meta: {
      title: '示例页面',
      icon: '&#xe600;'
    }
  }
]
```

### 新增 API 接口

```typescript
// api/example.ts
import request from '@/utils/http/request'

export interface ExampleItem {
  id: string
  name: string
  status: number
}

export interface ExampleListResponse {
  list: ExampleItem[]
  total: number
}

// 获取列表
export function fetchExampleList(params?: any) {
  return request.get<ExampleListResponse>('/example/list', { params })
}

// 创建
export function createExample(data: Partial<ExampleItem>) {
  return request.post('/example', data)
}

// 更新
export function updateExample(id: string, data: Partial<ExampleItem>) {
  return request.put(`/example/${id}`, data)
}

// 删除
export function deleteExample(id: string) {
  return request.delete(`/example/${id}`)
}
```

## 📦 构建部署

### 开发环境

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 生产构建

```bash
# 构建生产版本
pnpm build

# 预览构建结果
pnpm preview
```

### 构建产物

```
dist/
├── assets/           # 静态资源（JS/CSS/图片）
├── index.html        # 入口 HTML
└── *.gz              # Gzip 压缩文件
```

## 📚 相关文档

- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)
- [UnoCSS 文档](https://unocss.dev/)
