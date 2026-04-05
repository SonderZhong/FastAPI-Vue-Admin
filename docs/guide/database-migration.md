# 数据库配置说明

## 默认数据库

FastAPI-Vue-Admin 默认使用 **SQLite** 作为数据库，无需额外安装和配置数据库服务。

SQLite 是一个轻量级的嵌入式数据库，适合：
- 开发和测试环境
- 小型应用和个人项目
- 快速原型开发
- 单用户或低并发场景

## SQLite 配置

默认配置（`config.yaml`）：

```yaml
database:
  engine: "sqlite"
  host: ""
  port: 0
  username: ""
  password: ""
  database: "fva.db"  # 数据库文件路径
  pool_size: 10
  pool_timeout: 30
  echo: false
  timezone: "Asia/Shanghai"
  charset: "utf8mb4"
```

数据库文件 `fva.db` 会自动创建在 `server` 目录下。

**优点：**
- ✅ 无需安装额外软件
- ✅ 零配置，开箱即用
- ✅ 单文件存储，易于备份
- ✅ 资源占用少

**限制：**
- ⚠️ 不支持高并发写入
- ⚠️ 不适合多服务器部署
- ⚠️ 数据库大小建议 < 1GB

## 切换到 MySQL

MySQL 是最流行的开源关系型数据库，适合中大型应用。

### 1. 安装 MySQL

**Windows:**
1. 下载 [MySQL Installer](https://dev.mysql.com/downloads/installer/)
2. 运行安装程序，选择 "MySQL Server"
3. 设置 root 密码
4. 完成安装

**macOS:**
```bash
# 使用 Homebrew
brew install mysql

# 启动 MySQL 服务
brew services start mysql

# 设置 root 密码
mysql_secure_installation
```

**Linux (Ubuntu/Debian):**
```bash
# 安装 MySQL
sudo apt update
sudo apt install mysql-server

# 启动 MySQL 服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置 root 密码
sudo mysql_secure_installation
```

**验证安装：**
```bash
mysql --version
# 输出示例：mysql  Ver 8.0.35 for Linux on x86_64
```

### 2. 创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE fva CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建专用用户（可选，推荐）
CREATE USER 'fva_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON fva.* TO 'fva_user'@'localhost';
FLUSH PRIVILEGES;

# 退出
EXIT;
```

### 3. 修改配置

编辑 `server/config.yaml`：

```yaml
database:
  engine: "mysql"
  host: "127.0.0.1"
  port: 3306
  username: "root"  # 或 fva_user
  password: "your_password"
  database: "fva"
  pool_size: 10
  pool_timeout: 30
  echo: false
  timezone: "Asia/Shanghai"
  charset: "utf8mb4"
```

### 4. 重启服务

```bash
cd server
python main.py
```

系统会自动创建所有必要的数据表。

**MySQL 优点：**
- ✅ 成熟稳定，生态丰富
- ✅ 支持高并发读写
- ✅ 丰富的管理工具
- ✅ 广泛的社区支持

**适用场景：**
- 中大型 Web 应用
- 需要主从复制的场景
- 需要分库分表的场景
- 日访问量 10 万 - 1000 万

## 切换到 PostgreSQL

PostgreSQL 是功能最强大的开源关系型数据库，适合企业级应用。

### 1. 安装 PostgreSQL

**Windows:**
1. 下载 [PostgreSQL Installer](https://www.postgresql.org/download/windows/)
2. 运行安装程序
3. 设置 postgres 用户密码
4. 记住端口号（默认 5432）
5. 完成安装

**macOS:**
```bash
# 使用 Homebrew
brew install postgresql@14

# 启动 PostgreSQL 服务
brew services start postgresql@14

# 初始化数据库（如果需要）
initdb /usr/local/var/postgres
```

**Linux (Ubuntu/Debian):**
```bash
# 安装 PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动 PostgreSQL 服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到 postgres 用户
sudo -i -u postgres
```

**验证安装：**
```bash
psql --version
# 输出示例：psql (PostgreSQL) 14.10
```

### 2. 创建数据库

```bash
# 登录 PostgreSQL（Linux/macOS）
sudo -u postgres psql

# 或直接使用 psql（Windows，已配置环境变量）
psql -U postgres

# 创建数据库
CREATE DATABASE fva WITH ENCODING 'UTF8';

# 创建专用用户（可选，推荐）
CREATE USER fva_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fva TO fva_user;

# 退出
\q
```

### 3. 配置远程访问（如需要）

编辑 PostgreSQL 配置文件：

**postgresql.conf:**
```bash
# 找到配置文件
# Linux: /etc/postgresql/14/main/postgresql.conf
# macOS: /usr/local/var/postgres/postgresql.conf
# Windows: C:\Program Files\PostgreSQL\14\data\postgresql.conf

# 修改监听地址
listen_addresses = '*'  # 或 'localhost'
```

**pg_hba.conf:**
```bash
# 添加允许的连接
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# 如果需要远程访问
host    all             all             0.0.0.0/0               md5
```

重启 PostgreSQL 服务：
```bash
# Linux
sudo systemctl restart postgresql

# macOS
brew services restart postgresql@14

# Windows
# 在服务管理器中重启 PostgreSQL 服务
```

### 4. 修改配置

编辑 `server/config.yaml`：

```yaml
database:
  engine: "postgresql"
  host: "127.0.0.1"
  port: 5432
  username: "postgres"  # 或 fva_user
  password: "your_password"
  database: "fva"
  pool_size: 10
  pool_timeout: 30
  echo: false
  timezone: "Asia/Shanghai"
  charset: "utf8mb4"
```

### 5. 重启服务

```bash
cd server
python main.py
```

系统会自动创建所有必要的数据表。

**PostgreSQL 优点：**
- ✅ 功能最强大，支持高级特性
- ✅ 优秀的并发性能
- ✅ 强大的 JSON 支持
- ✅ 严格的数据完整性
- ✅ 支持全文搜索、地理信息等

**适用场景：**
- 企业级应用
- 需要复杂查询的场景
- 需要 JSON 数据类型的场景
- 需要地理信息系统（GIS）
- 日访问量 > 1000 万

## 数据迁移

如果需要从一个数据库迁移到另一个数据库，可以使用以下方法：

### 方法一：重新初始化（推荐用于开发环境）

适用于开发环境或数据不重要的情况。

1. 备份重要数据（如有）
2. 删除配置文件和数据库：
   ```bash
   cd server
   rm config.yaml
   rm fva.db  # SQLite
   # 或删除 MySQL/PostgreSQL 中的数据库
   ```
3. 重新运行 `python main.py`，在初始化向导中选择新的数据库类型
4. 系统会自动创建新的表结构
5. 手动导入必要的数据

### 方法二：使用数据导出工具（推荐用于生产环境）

#### SQLite 到 MySQL

使用 [sqlite3-to-mysql](https://github.com/techouse/sqlite3-to-mysql) 工具：

```bash
# 安装工具
pip install sqlite3-to-mysql

# 执行迁移
sqlite3mysql -f fva.db -d fva -u root -p
```

#### SQLite 到 PostgreSQL

使用 [pgloader](https://github.com/dimitri/pgloader) 工具：

```bash
# 安装 pgloader（Ubuntu/Debian）
sudo apt install pgloader

# 执行迁移
pgloader fva.db postgresql://postgres:password@localhost/fva
```

#### MySQL 到 PostgreSQL

使用 [pgloader](https://github.com/dimitri/pgloader)：

```bash
pgloader mysql://root:password@localhost/fva postgresql://postgres:password@localhost/fva
```

### 方法三：自定义 Python 脚本

适用于需要数据转换或清洗的场景。

```python
import asyncio
from tortoise import Tortoise

async def migrate_data():
    # 连接源数据库
    await Tortoise.init(
        db_url="sqlite://fva.db",
        modules={"models": ["models"]}
    )
    
    # 导出数据
    from models import SystemUser
    users = await SystemUser.all()
    
    # 关闭源数据库
    await Tortoise.close_connections()
    
    # 连接目标数据库
    await Tortoise.init(
        db_url="mysql://root:password@localhost/fva",
        modules={"models": ["models"]}
    )
    
    # 导入数据
    for user in users:
        await SystemUser.create(**user.__dict__)
    
    await Tortoise.close_connections()

asyncio.run(migrate_data())
```

## 性能对比

| 特性 | SQLite | MySQL | PostgreSQL |
|------|--------|-------|------------|
| 安装配置 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 并发读取 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 并发写入 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 功能丰富度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 资源占用 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 数据完整性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| JSON 支持 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 全文搜索 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 地理信息 | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 社区支持 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 使用场景建议

### SQLite 适合

✅ **开发和测试**
- 快速搭建开发环境
- 单元测试和集成测试
- 原型开发和演示

✅ **小型应用**
- 个人博客、笔记应用
- 内部工具和脚本
- 桌面应用的本地存储
- 日访问量 < 10 万

✅ **嵌入式场景**
- 移动应用后端
- IoT 设备数据存储
- 边缘计算场景

❌ **不适合**
- 高并发写入（> 100 写入/秒）
- 多服务器集群部署
- 需要复杂事务的场景
- 数据库大小 > 10GB

### MySQL 适合

✅ **中大型 Web 应用**
- 电商网站
- 社交平台
- 内容管理系统
- 日访问量 10 万 - 1000 万

✅ **需要主从复制**
- 读写分离架构
- 数据备份和容灾
- 负载均衡

✅ **成熟生态**
- 丰富的管理工具（phpMyAdmin、MySQL Workbench）
- 大量的教程和文档
- 广泛的云服务支持

❌ **不适合**
- 需要复杂 JSON 查询
- 需要地理信息系统
- 需要高级数据类型

### PostgreSQL 适合

✅ **企业级应用**
- 金融系统
- ERP/CRM 系统
- 数据仓库
- 日访问量 > 1000 万

✅ **复杂查询**
- 需要窗口函数
- 需要递归查询
- 需要复杂的 JOIN 操作

✅ **高级特性**
- JSON/JSONB 数据类型
- 数组和范围类型
- 全文搜索
- 地理信息系统（PostGIS）
- 时序数据（TimescaleDB）

✅ **数据完整性要求高**
- 严格的外键约束
- 事务隔离级别
- ACID 完全支持

❌ **不适合**
- 简单的 CRUD 应用（过于复杂）
- 资源受限的环境
- 需要极简配置的场景

## 常见问题

### Q: SQLite 是否适合生产环境？

SQLite 适合以下生产场景：
- 单用户或低并发应用
- 嵌入式系统
- 移动应用后端
- 小型网站（日访问量 < 10万）

不适合：
- 高并发写入场景
- 多服务器部署
- 需要复杂查询优化的场景

### Q: 切换数据库后需要修改代码吗？

不需要。Tortoise-ORM 会自动处理不同数据库的差异，只需修改配置文件即可。

### Q: 如何备份 SQLite 数据库？

```bash
# 简单备份
cp server/fva.db server/fva.db.backup

# 使用 SQLite 命令
sqlite3 server/fva.db ".backup server/fva.db.backup"
```

### Q: 数据库文件在哪里？

默认位置：`server/fva.db`

可以在 `config.yaml` 中修改路径：

```yaml
database:
  database: "/path/to/your/database.db"  # 绝对路径
  # 或
  database: "data/fva.db"  # 相对于 server 目录
```
