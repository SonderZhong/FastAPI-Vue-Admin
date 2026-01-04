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

### Cursor

在 `.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "fva-helper": {
      "command": "python",
      "args": ["-m", "fva_mcp.server"],
      "cwd": "/path/to/project/server"
    }
  }
}
```

### Kiro

在 `.kiro/settings/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "fva-helper": {
      "command": "python",
      "args": ["-m", "fva_mcp.server"],
      "cwd": "/path/to/project/server"
    }
  }
}
```

## 使用示例

配置完成后，可以在 AI 对话中使用 MCP 工具：

- "查询所有用户列表"
- "创建一个文章模型，包含标题、内容、作者字段"
- "根据 Article 模型生成 CRUD API"
