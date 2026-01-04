# useTable 组合式函数说明文档

`useTable` 是一个功能强大的 Vue 3 组合式函数，专为管理表格数据而设计。它提供了完整的表格解决方案，包括数据获取、缓存管理、分页控制、搜索功能、智能刷新策略等。

## 特性

- 🚀 **自动类型推导** - 基于 API 函数自动推导数据类型
- 📊 **完整分页支持** - 内置分页逻辑，支持自定义分页字段
- 🔍 **智能搜索** - 支持多条件搜索和参数过滤
- 💾 **智能缓存** - 可选的 LRU 缓存机制，提升性能
- 🔄 **智能刷新** - 多种缓存失效策略
- 🎯 **防抖优化** - 防止频繁请求
- 📱 **响应式设计** - 完全响应式数据管理
- 🛡️ **错误处理** - 完善的错误捕获和处理机制
- 🔧 **高度可配置** - 丰富的配置选项满足各种需求

## 基础用法

### 简单示例

```typescript
import { useTable } from '@/composables/useTable'
import { fetchDepartmentList } from '@/api/system/department'

const {
  data,           // 表格数据
  loading,        // 加载状态
  pagination,     // 分页信息
  columns,        // 表格列配置
  getData,        // 手动获取数据
  refreshData     // 刷新数据
} = useTable({
  core: {
    apiFn: fetchDepartmentList,
    apiParams: {
      current: 1,
      size: 20
    }
  }
})
```

### 带搜索功能的示例

```typescript
const {
  data,
  loading,
  pagination,
  searchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData
} = useTable({
  core: {
    apiFn: fetchUserList,
    apiParams: {
      current: 1,
      size: 20,
      status: 1
    },
    excludeParams: ['daterange'], // 排除不需要传递给 API 的参数
    columnsFactory: () => [
      { type: 'selection' },
      { type: 'index', width: 60, label: '序号' },
      { prop: 'name', label: '姓名', minWidth: 120 },
      { prop: 'email', label: '邮箱', minWidth: 150 }
    ]
  },
  performance: {
    enableCache: true,
    cacheTime: 5 * 60 * 1000, // 5分钟缓存
    debounceTime: 300
  }
})
```

## 配置选项详解

### 核心配置 (core)

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `apiFn` | `Function` | ✅ | - | API 请求函数 |
| `apiParams` | `Object` | ❌ | `{}` | 默认请求参数 |
| `excludeParams` | `string[]` | ❌ | `[]` | 排除传递给 API 的参数名 |
| `immediate` | `boolean` | ❌ | `true` | 是否立即加载数据 |
| `columnsFactory` | `Function` | ❌ | - | 列配置工厂函数 |
| `paginationKey` | `Object` | ❌ | `{current: 'current', size: 'size'}` | 分页字段映射 |

#### paginationKey 说明

用于自定义分页字段名，适配不同的后端接口：

```typescript
// 示例1: 使用 page/pageSize 作为分页字段
{
  core: {
    paginationKey: {
      current: 'page',
      size: 'pageSize'
    },
    apiParams: {
      page: 1,
      pageSize: 20
    }
  }
}

// 示例2: 使用 pageNum/limit 作为分页字段
{
  core: {
    paginationKey: {
      current: 'pageNum',
      size: 'limit'
    },
    apiParams: {
      pageNum: 1,
      limit: 10
    }
  }
}
```

### 数据处理 (transform)

| 参数 | 类型 | 说明 |
|------|------|------|
| `dataTransformer` | `(data: T[]) => T[]` | 数据转换函数，可用于数据预处理 |
| `responseAdapter` | `(response: any) => ApiResponse<T>` | 响应适配器，适配不同的 API 响应格式 |

#### dataTransformer 示例

```typescript
{
  transform: {
    dataTransformer: (records) => {
      return records.map((item, index) => ({
        ...item,
        // 添加序号
        index: index + 1,
        // 格式化状态
        statusText: item.status === 1 ? '启用' : '禁用',
        // 替换头像
        avatar: AVATAR_LIST[index % AVATAR_LIST.length]
      }))
    }
  }
}
```

### 性能优化 (performance)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enableCache` | `boolean` | `false` | 是否启用缓存 |
| `cacheTime` | `number` | `300000` | 缓存时间（毫秒） |
| `debounceTime` | `number` | `300` | 防抖延迟时间（毫秒） |
| `maxCacheSize` | `number` | `50` | 最大缓存条数 |

### 生命周期钩子 (hooks)

| 参数 | 类型 | 说明 |
|------|------|------|
| `onSuccess` | `(data, response) => void` | 数据加载成功回调（仅网络请求成功时触发） |
| `onError` | `(error) => void` | 错误处理回调 |
| `onCacheHit` | `(data, response) => void` | 缓存命中回调 |
| `onLoading` | `(loading) => void` | 加载状态变化回调 |
| `resetFormCallback` | `() => void` | 重置表单回调函数 |

## 返回值详解

### 数据相关

- `data`: 表格数据数组，响应式
- `loading`: 加载状态，响应式
- `error`: 错误信息，响应式
- `pagination`: 分页信息对象，包含 `current`、`size`、`total` 等

### 搜索相关

- `searchParams`: 搜索参数对象，响应式
- `resetSearchParams()`: 重置搜索参数方法

### 分页相关

- `handleSizeChange(size)`: 处理每页条数变化
- `handleCurrentChange(current)`: 处理当前页变化

### 数据操作

- `getData(strategy?)`: 手动获取数据，可指定缓存策略
- `refreshData(strategy?)`: 刷新数据
- `resetAndGetData()`: 重置到第一页并获取数据

### 列配置相关

- `columns`: 表格列配置，响应式
- `columnChecks`: 列显示控制，响应式

### 缓存相关

- `getCacheStats()`: 获取缓存统计信息
- `clearCache(strategy?)`: 清除缓存

## 缓存策略

useTable 支持多种缓存失效策略：

```typescript
enum CacheInvalidationStrategy {
  CLEAR_ALL = 'clear_all',         // 清空所有缓存
  CLEAR_CURRENT = 'clear_current', // 仅清空当前查询条件的缓存
  CLEAR_PAGINATION = 'clear_pagination', // 清空所有分页缓存
  KEEP_ALL = 'keep_all'           // 不清除缓存
}

// 使用示例
refreshData(CacheInvalidationStrategy.CLEAR_ALL)
```

## 完整示例

### 用户管理页面

```vue
<template>
  <div class="user-page">
    <!-- 搜索栏 -->
    <UserSearch 
      v-model="searchForm" 
      @search="handleSearch" 
      @reset="resetSearchParams"
    />

    <!-- 表格 -->
    <ArtTable
      :loading="loading"
      :data="data"
      :columns="columns"
      :pagination="pagination"
      @selection-change="handleSelectionChange"
      @pagination:size-change="handleSizeChange"
      @pagination:current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup lang="ts">
import { useTable } from '@/composables/useTable'
import { fetchGetUserList } from '@/api/system-manage'

const searchForm = ref({
  username: '',
  status: '',
  daterange: []
})

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  getData,
  searchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData
} = useTable({
  core: {
    apiFn: fetchGetUserList,
    apiParams: {
      current: 1,
      size: 20,
      ...searchForm.value
    },
    excludeParams: ['daterange'],
    columnsFactory: () => [
      { type: 'selection' },
      { type: 'index', width: 60, label: '序号' },
      {
        prop: 'username',
        label: '用户名',
        minWidth: 120
      },
      {
        prop: 'email',
        label: '邮箱',
        minWidth: 150
      },
      {
        prop: 'status',
        label: '状态',
        formatter: (row) => {
          return h(ElTag, 
            { type: row.status === 1 ? 'success' : 'danger' },
            () => row.status === 1 ? '启用' : '禁用'
          )
        }
      },
      {
        prop: 'operation',
        label: '操作',
        width: 120,
        fixed: 'right',
        formatter: (row) => h('div', [
          h(ElButton, { 
            size: 'small', 
            onClick: () => editUser(row) 
          }, () => '编辑'),
          h(ElButton, { 
            size: 'small', 
            type: 'danger',
            onClick: () => deleteUser(row) 
          }, () => '删除')
        ])
      }
    ]
  },
  transform: {
    dataTransformer: (records) => {
      return records.map((item, index) => ({
        ...item,
        avatar: DEFAULT_AVATAR_LIST[index % DEFAULT_AVATAR_LIST.length]
      }))
    }
  },
  performance: {
    enableCache: true,
    cacheTime: 5 * 60 * 1000,
    debounceTime: 300
  },
  hooks: {
    onSuccess: (data, response) => {
      console.log('数据加载成功:', data.length, '条记录')
    },
    onError: (error) => {
      ElMessage.error(error.message)
    },
    onCacheHit: (data, response) => {
      console.log('缓存命中，数据来源：缓存')
    }
  }
})

// 搜索处理
const handleSearch = (params) => {
  const { daterange, ...filterParams } = params
  const [startTime, endTime] = Array.isArray(daterange) ? daterange : [null, null]
  
  Object.assign(searchParams, { 
    ...filterParams, 
    startTime, 
    endTime 
  })
  getData()
}

// 选择变化
const handleSelectionChange = (selection) => {
  console.log('选中的行:', selection)
}

// 编辑用户
const editUser = (row) => {
  // 编辑逻辑
}

// 删除用户
const deleteUser = (row) => {
  // 删除逻辑
  // 删除成功后刷新数据
  refreshData()
}
</script>
```

### 部门管理示例（自定义分页字段）

```typescript
const {
  data,
  loading,
  pagination,
  refreshData
} = useTable({
  core: {
    apiFn: fetchDepartmentList,
    apiParams: {
      page: 1,           // 注意：使用 page 而不是 current
      pageSize: 20,      // 注意：使用 pageSize 而不是 size
      status: 1
    },
    paginationKey: {
      current: 'page',   // 映射到 page 字段
      size: 'pageSize'   // 映射到 pageSize 字段
    },
    columnsFactory: () => [
      { prop: 'name', label: '部门名称' },
      { prop: 'principal', label: '负责人' },
      { prop: 'phone', label: '电话' }
    ]
  },
  performance: {
    enableCache: true
  }
})
```

## 最佳实践

### 1. API 响应格式适配

useTable 内置了通用的响应适配器，支持多种常见格式：

```typescript
// 支持的响应格式1: 直接数组
[{id: 1, name: 'test'}]

// 支持的响应格式2: 包装对象
{
  data: [{id: 1, name: 'test'}],
  total: 100
}

// 支持的响应格式3: 标准响应
{
  code: 200,
  msg: 'success',
  success: true,
  data: {
    records: [{id: 1, name: 'test'}],
    total: 100,
    current: 1,
    size: 20
  }
}
```

### 2. 错误处理

```typescript
{
  hooks: {
    onError: (error) => {
      // 统一错误处理
      if (error.code === 'NETWORK_ERROR') {
        ElMessage.error('网络连接失败，请检查网络')
      } else if (error.code === 'AUTH_ERROR') {
        // 处理认证错误
        router.push('/login')
      } else {
        ElMessage.error(error.message || '操作失败')
      }
    }
  }
}
```

### 3. 性能优化

```typescript
{
  performance: {
    enableCache: true,        // 启用缓存
    cacheTime: 10 * 60 * 1000, // 10分钟缓存
    debounceTime: 500,        // 500ms防抖
    maxCacheSize: 100         // 最多100条缓存
  }
}
```

### 4. 列配置最佳实践

```typescript
columnsFactory: () => [
  { type: 'selection' },      // 勾选列
  { type: 'index', width: 60, label: '序号' }, // 序号列
  
  // 普通文本列
  {
    prop: 'name',
    label: '姓名',
    minWidth: 120,            // 使用 minWidth 而不是固定 width
    showOverflowTooltip: true // 超长文本显示 tooltip
  },
  
  // 状态列（使用 formatter）
  {
    prop: 'status',
    label: '状态',
    width: 100,
    formatter: (row) => {
      return h(ElTag, {
        type: row.status === 1 ? 'success' : 'danger'
      }, () => row.status === 1 ? '启用' : '禁用')
    }
  },
  
  // 操作列
  {
    prop: 'operation',
    label: '操作',
    width: 180,
    fixed: 'right',           // 固定在右侧
    formatter: (row) => h('div', { class: 'table-operations' }, [
      h(ElButton, {
        size: 'small',
        onClick: () => editRow(row)
      }, () => '编辑'),
      h(ElButton, {
        size: 'small',
        type: 'danger',
        onClick: () => deleteRow(row)
      }, () => '删除')
    ])
  }
]
```

## 注意事项

1. **分页字段映射**: 确保 `paginationKey` 中的字段名与 `apiParams` 中的字段名一致
2. **API 类型**: 建议为 API 函数定义准确的 TypeScript 类型，以获得更好的类型推导
3. **缓存策略**: 在数据变更后及时清理相关缓存，避免显示过期数据
4. **错误处理**: 建议在 `onError` 回调中进行统一的错误处理
5. **性能**: 对于大量数据的表格，建议启用缓存和适当的防抖时间

## 类型定义

```typescript
// API 响应类型示例
interface DepartmentListResponse {
  code: number
  msg: string
  success: boolean
  data: {
    records: DepartmentInfo[]
    total: number
    current: number
    size: number
  }
}

// 部门信息类型
interface DepartmentInfo {
  id: string
  name: string
  principal: string
  phone: string
  email: string
  status: number
  sort: number
  created_at: string
}
```

这份文档涵盖了 useTable 的所有功能特性和使用方法，可以帮助开发者快速上手并高效使用这个强大的表格管理工具。
