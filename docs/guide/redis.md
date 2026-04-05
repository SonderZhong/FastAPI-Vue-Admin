# Redis 配置指南

## 概述

FastAPI-Vue-Admin 支持两种 Redis 运行模式：

- **内存模式（Memory Mode）**：使用内存模拟 Redis，无需安装 Redis 服务器
- **服务器模式（Server Mode）**：连接真实的 Redis 服务器

## 运行模式对比

| 特性 | 内存模式 | 服务器模式 |
|------|---------|-----------|
| 安装要求 | 无需安装 Redis | 需要安装 Redis 服务器 |
| 适用场景 | 开发、测试、小规模部署 | 生产环境、高并发场景 |
| 数据持久化 | 不支持（重启丢失） | 支持（RDB/AOF） |
| 分布式支持 | 不支持 | 支持（集群/哨兵） |
| 性能 | 适中 | 高性能 |
| 配置复杂度 | 简单 | 需要配置连接参数 |

## 内存模式

### 特点

- 无需安装和配置 Redis 服务器
- 数据存储在应用内存中
- 应用重启后数据丢失
- 适合开发环境和小规模部署

### 配置方式

在 `server/config.yaml` 中配置：

```yaml
redis:
  mode: "memory"  # 使用内存模式
  host: "127.0.0.1"  # 内存模式下此参数无效
  port: 6379
  password: ""
  database: 1
```

### 使用限制

1. **数据不持久化**：应用重启后所有缓存数据丢失
2. **单机运行**：不支持分布式部署
3. **内存限制**：受应用进程内存限制
4. **功能限制**：
   - 不支持 Redis 集群
   - 不支持发布/订阅（Pub/Sub）
   - 不支持 Lua 脚本
   - 不支持事务（MULTI/EXEC）

### 适用场景

- 本地开发和调试
- 单元测试和集成测试
- 小规模个人项目
- 快速原型验证
- 无需数据持久化的场景

## 服务器模式

### 特点

- 连接真实的 Redis 服务器
- 支持数据持久化
- 支持分布式部署
- 高性能、高可用

### 安装 Redis

#### Windows

1. 下载 Redis for Windows：
   - 官方版本：https://github.com/microsoftarchive/redis/releases
   - 或使用 WSL2 安装 Linux 版本

2. 解压并运行：
   ```bash
   redis-server.exe
   ```

3. 测试连接：
   ```bash
   redis-cli.exe ping
   # 返回 PONG 表示成功
   ```

#### macOS

使用 Homebrew 安装：

```bash
# 安装 Redis
brew install redis

# 启动 Redis 服务
brew services start redis

# 测试连接
redis-cli ping
```

#### Linux (Ubuntu/Debian)

```bash
# 更新包索引
sudo apt update

# 安装 Redis
sudo apt install redis-server

# 启动 Redis 服务
sudo systemctl start redis-server

# 设置开机自启
sudo systemctl enable redis-server

# 测试连接
redis-cli ping
```

#### Docker

```bash
# 运行 Redis 容器
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest

# 测试连接
docker exec -it redis redis-cli ping
```

### 配置方式

在 `server/config.yaml` 中配置：

```yaml
redis:
  mode: "server"  # 使用服务器模式
  host: "127.0.0.1"  # Redis 服务器地址
  port: 6379  # Redis 端口
  password: ""  # Redis 密码（如果设置了）
  database: 1  # 数据库编号（0-15）
  max_connections: 10  # 连接池大小
  socket_timeout: 5  # 连接超时时间（秒）
  retry_on_timeout: true  # 超时是否重试
```

### 远程连接配置

如果 Redis 运行在远程服务器上，需要修改 Redis 配置文件 `redis.conf`：

```bash
# 1. 绑定所有网络接口（默认只绑定 127.0.0.1）
bind 0.0.0.0

# 2. 设置密码（强烈推荐）
requirepass your_strong_password

# 3. 关闭保护模式（或设置密码）
protected-mode no

# 4. 重启 Redis 服务
sudo systemctl restart redis-server
```

应用配置：

```yaml
redis:
  mode: "server"
  host: "192.168.1.100"  # 远程服务器 IP
  port: 6379
  password: "your_strong_password"  # 设置的密码
  database: 1
```

### Docker 部署注意事项

如果应用运行在 Docker 容器中，需要连接宿主机上的 Redis：

```yaml
redis:
  mode: "server"
  host: "host.docker.internal"  # Docker 特殊域名，指向宿主机
  port: 6379
  password: ""
  database: 1
```

或者使用 Docker Compose 网络：

```yaml
# docker-compose.yml
services:
  app:
    # ...
    depends_on:
      - redis
  
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
```

应用配置：

```yaml
redis:
  mode: "server"
  host: "redis"  # 使用服务名称
  port: 6379
```

## 模式切换

### 从内存模式切换到服务器模式

1. 安装并启动 Redis 服务器
2. 修改 `server/config.yaml`：
   ```yaml
   redis:
     mode: "server"  # 改为 server
     host: "127.0.0.1"
     port: 6379
     password: ""
     database: 1
   ```
3. 重启应用

### 从服务器模式切换到内存模式

1. 修改 `server/config.yaml`：
   ```yaml
   redis:
     mode: "memory"  # 改为 memory
   ```
2. 重启应用
3. 注意：切换后原有缓存数据将丢失

## 性能优化

### 内存模式优化

1. **控制缓存大小**：避免存储过大的数据
2. **设置过期时间**：及时清理过期数据
3. **监控内存使用**：防止内存溢出

### 服务器模式优化

1. **连接池配置**：
   ```yaml
   redis:
     max_connections: 50  # 根据并发量调整
     socket_timeout: 10  # 增加超时时间
   ```

2. **Redis 服务器优化**：
   ```bash
   # redis.conf
   maxmemory 2gb  # 设置最大内存
   maxmemory-policy allkeys-lru  # 内存淘汰策略
   ```

3. **使用连接池**：应用已自动使用连接池

4. **数据持久化配置**：
   ```bash
   # RDB 快照
   save 900 1
   save 300 10
   save 60 10000
   
   # AOF 持久化
   appendonly yes
   appendfsync everysec
   ```

## 监控和维护

### 内存模式监控

内存模式无需特殊监控，关注应用内存使用即可。

### 服务器模式监控

1. **查看 Redis 信息**：
   ```bash
   redis-cli info
   ```

2. **监控内存使用**：
   ```bash
   redis-cli info memory
   ```

3. **查看连接数**：
   ```bash
   redis-cli info clients
   ```

4. **监控慢查询**：
   ```bash
   redis-cli slowlog get 10
   ```

## 故障排查

### 内存模式常见问题

1. **应用重启后数据丢失**
   - 原因：内存模式不持久化数据
   - 解决：切换到服务器模式

2. **内存占用过高**
   - 原因：缓存数据过多
   - 解决：设置合理的过期时间，清理无用数据

### 服务器模式常见问题

1. **连接失败**
   ```
   Redis连接被拒绝（地址: 127.0.0.1:6379）
   ```
   - 检查 Redis 服务是否启动
   - 检查防火墙设置
   - 检查 Redis 配置的 bind 地址

2. **认证失败**
   ```
   Redis认证失败
   ```
   - 检查密码是否正确
   - 检查 Redis 是否设置了 requirepass

3. **连接超时**
   ```
   Redis连接超时
   ```
   - 增加 socket_timeout 配置
   - 检查网络连接
   - 检查 Redis 服务器负载

4. **内存不足**
   ```
   OOM command not allowed when used memory > 'maxmemory'
   ```
   - 增加 Redis maxmemory 配置
   - 设置合理的内存淘汰策略
   - 清理无用数据

## 最佳实践

1. **开发环境**：使用内存模式，快速启动，无需配置
2. **测试环境**：使用服务器模式，模拟生产环境
3. **生产环境**：必须使用服务器模式，配置持久化和高可用
4. **设置密码**：生产环境必须设置 Redis 密码
5. **数据备份**：定期备份 Redis 数据（RDB/AOF）
6. **监控告警**：监控 Redis 内存、连接数、慢查询等指标
7. **合理过期**：为缓存数据设置合理的过期时间
8. **避免大 key**：避免存储过大的单个键值

## 相关文档

- [快速开始](./getting-started.md)
- [后端开发指南](./backend.md)
- [部署指南](./deploy.md)
