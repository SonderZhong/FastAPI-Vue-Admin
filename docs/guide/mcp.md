# MCP 服务

项目内置 FVA Helper MCP 服务，提供 AI 辅助开发能力。

## 什么是 MCP

MCP（Model Context Protocol）是一种让 AI 模型与外部工具交互的协议。通过 MCP，AI 可以直接操作数据库、生成代码等。

## 启动 MCP 服务

```bash
cd server

# stdio 模式（用于 IDE 集成）
python -m fva_mcp.server

# SSE 模式（用于 Web 调试）
python -m fva_mcp.server --mode sse --port 9091
```

## 工具列表

### 数据库工具 (db_tools)

- `list_users` - 查询用户列表
- `get_user` - 获取用户详情
- `list_roles` - 查询角色列表
- `list_departments` - 查询部门列表
- `list_permissions` - 查询权限列表
- `execute_sql` - 执行只读 SQL 查询

### Redis 工具 (redis_tools)

- `redis_get` - 获取键值
- `redis_set` - 设置键值
- `redis_delete` - 删除键
- `redis_keys` - 查找匹配的键
- `redis_info` - 获取 Redis 信息

### 模型工具 (model_tools)

- `create_database_model` - 创建数据库模型
- `list_database_models` - 列出所有模型
- `analyze_model_structure` - 分析模型结构

### Schema 工具 (schema_tools)

- `create_schema_from_model` - 根据模型生成 Schema
- `list_existing_schema_files` - 列出现有 Schema 文件

### API 工具 (api_tools)

- `create_api_from_model` - 根据模型生成 API
- `list_existing_api_files` - 列出现有 API 文件

## IDE 配置

::: warning 重要说明
MCP 配置必须使用**绝对路径**，包括：
1. Python 解释器路径 - 如果使用虚拟环境，必须指向虚拟环境中的 Python
2. MCP 服务脚本路径 - 必须是 `server.py` 的完整绝对路径

相对路径或 `cwd` 配置在某些 IDE 中可能不生效！
:::

### Cursor

在 `.cursor/mcp.json` 中添加：

::: code-group

```json [Windows]
{
  "mcpServers": {
    "fva-helper": {
      "command": "E:/projects/fastapi-vue-admin/server/venv/Scripts/python.exe",
      "args": ["E:/projects/fastapi-vue-admin/server/fva_mcp/server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": [
        "list_permissions",
        "list_users",
        "list_roles",
        "list_departments",
        "get_statistics",
        "redis_keys",
        "redis_get",
        "redis_dbsize",
        "redis_info"
      ]
    }
  }
}
```

```json [Linux/Mac]
{
  "mcpServers": {
    "fva-helper": {
      "command": "/home/user/projects/fastapi-vue-admin/server/venv/bin/python",
      "args": ["/home/user/projects/fastapi-vue-admin/server/fva_mcp/server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": [
        "list_permissions",
        "list_users",
        "list_roles",
        "list_departments",
        "get_statistics",
        "redis_keys",
        "redis_get",
        "redis_dbsize",
        "redis_info"
      ]
    }
  }
}
```

:::

### Kiro

在 `.kiro/settings/mcp.json` 中添加：

::: code-group

```json [Windows]
{
  "mcpServers": {
    "fva-helper": {
      "command": "E:/projects/fastapi-vue-admin/server/venv/Scripts/python.exe",
      "args": ["E:/projects/fastapi-vue-admin/server/fva_mcp/server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": [
        "list_permissions",
        "list_users",
        "list_roles",
        "list_departments",
        "get_statistics",
        "redis_keys",
        "redis_get",
        "redis_dbsize",
        "redis_info"
      ]
    }
  }
}
```

```json [Linux/Mac]
{
  "mcpServers": {
    "fva-helper": {
      "command": "/home/user/projects/fastapi-vue-admin/server/venv/bin/python",
      "args": ["/home/user/projects/fastapi-vue-admin/server/fva_mcp/server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": [
        "list_permissions",
        "list_users",
        "list_roles",
        "list_departments",
        "get_statistics",
        "redis_keys",
        "redis_get",
        "redis_dbsize",
        "redis_info"
      ]
    }
  }
}
```

:::

### 路径说明

| 操作系统 | Python 路径示例 |
|---------|----------------|
| Windows (venv) | `E:/projects/fastapi-vue-admin/server/venv/Scripts/python.exe` |
| Windows (系统) | `C:/Python311/python.exe` |
| Linux/Mac (venv) | `/home/user/projects/fastapi-vue-admin/server/venv/bin/python` |
| Linux/Mac (系统) | `/usr/bin/python3` |

::: tip 如何获取路径

::: code-group

```bash [Windows]
# 在项目 server 目录下激活虚拟环境后执行
where python
```

```bash [Linux/Mac]
# 在项目 server 目录下激活虚拟环境后执行
which python
```

:::

:::

### autoApprove 配置

`autoApprove` 数组中的工具会自动执行，无需每次确认。建议只添加只读查询类工具：

- `list_*` - 列表查询类
- `get_*` - 详情查询类
- `redis_get`, `redis_keys`, `redis_info` - Redis 只读操作

::: danger 安全提示
不建议将 `execute_sql`、`redis_set`、`redis_delete` 等写操作工具加入 autoApprove！
:::

## 使用示例

配置完成后，可以在 AI 对话中使用 MCP 工具：

- "查询所有用户列表"
- "创建一个文章模型，包含标题、内容、作者字段"
- "根据 Article 模型生成 CRUD API"
