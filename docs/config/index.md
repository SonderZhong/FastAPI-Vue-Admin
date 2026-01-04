# ⚙️ 后端配置

后端配置文件为 `server/config.yaml`，首次启动时通过初始化向导自动生成。

## 📄 完整配置示例

```yaml
# 应用核心配置
app:
  env: dev                      # 环境：dev/prod
  name: FastAPI-Vue-Admin       # 应用名称
  api_prefix: /dev-api          # API 前缀
  api_status_enabled: true      # 是否启用 API 文档
  host: 0.0.0.0                 # 监听地址
  port: 9090                    # 监听端口
  version: 1.0.0                # 版本号
  reload: true                  # 热重载（开发环境）
  ip_location_enabled: true     # IP 定位功能
  multi_login_allowed: true     # 允许多端登录
  init_database: true           # 初始化数据库

# JWT 认证配置
jwt:
  secret_key: your-secret-key   # JWT 密钥（必须修改！）
  algorithm: HS256              # 签名算法
  salt: your-salt               # 加盐值
  expire_minutes: 1440          # Token 过期时间（分钟）
  redis_expire_minutes: 30      # Redis 缓存时间

# 数据库配置
database:
  engine: mysql                 # 数据库类型：mysql/postgresql/sqlite
  host: 127.0.0.1
  port: 3306
  username: root
  password: your-password
  database: fva
  pool_size: 10                 # 连接池大小
  pool_timeout: 30              # 连接超时
  echo: false                   # SQL 日志
  charset: utf8mb4
  timezone: Asia/Shanghai

# Redis 配置
redis:
  host: 127.0.0.1
  port: 6379
  password: ""
  database: 1
  max_connections: 10
  socket_timeout: 5
  retry_on_timeout: true

# 文件上传配置
upload:
  storage_type: local           # 存储类型：local/aliyun_oss/tencent_cos
  max_file_size: 100            # 最大文件大小（MB）
  local_upload_path: data/local_uploads
  local_download_path: data/local_downloads
  local_url_prefix: /uploads
  allowed_extensions:
    - jpg
    - jpeg
    - png
    - gif
    - pdf
    - doc
    - docx

# 邮件配置
email:
  host: smtp.qq.com
  port: 465
  username: your-email@qq.com
  password: your-smtp-password
  from_addr: your-email@qq.com

# 地图服务配置
map:
  provider: baidu               # 服务商：baidu/amap
  ak: your-map-ak
  sk: your-map-sk
```

## 📋 配置项详解

### app - 应用配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `env` | string | dev | 运行环境：`dev` 开发 / `prod` 生产 |
| `name` | string | FastAPI-Vue-Admin | 应用名称，用于文档标题等 |
| `api_prefix` | string | /dev-api | API 路径前缀 |
| `api_status_enabled` | bool | true | 是否启用 Swagger 文档 |
| `host` | string | 0.0.0.0 | 监听地址 |
| `port` | int | 9090 | 监听端口 |
| `version` | string | 1.0.0 | 应用版本号 |
| `reload` | bool | true | 代码热重载（仅开发环境） |
| `ip_location_enabled` | bool | true | 是否启用 IP 地理定位 |
| `multi_login_allowed` | bool | true | 是否允许多端同时登录 |
| `init_database` | bool | true | 是否自动初始化数据库表 |

::: warning 生产环境注意
- `env` 设置为 `prod`
- `reload` 设置为 `false`
- `api_status_enabled` 建议设置为 `false`
:::

### jwt - JWT 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `secret_key` | string | - | JWT 签名密钥（**必须修改**） |
| `algorithm` | string | HS256 | 签名算法：HS256/HS384/HS512 |
| `salt` | string | - | 密码加盐值 |
| `expire_minutes` | int | 1440 | Token 有效期（分钟），1440=24小时 |
| `redis_expire_minutes` | int | 30 | Token 在 Redis 中的缓存时间 |

::: danger 安全提示
`secret_key` 必须使用强随机字符串，可通过以下命令生成：
```bash
openssl rand -hex 32
```
:::

### database - 数据库配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `engine` | string | mysql | 数据库类型：mysql/postgresql/sqlite |
| `host` | string | 127.0.0.1 | 数据库主机地址 |
| `port` | int | 3306 | 数据库端口 |
| `username` | string | root | 数据库用户名 |
| `password` | string | - | 数据库密码 |
| `database` | string | fva | 数据库名称 |
| `pool_size` | int | 10 | 连接池大小 |
| `pool_timeout` | int | 30 | 连接超时时间（秒） |
| `echo` | bool | false | 是否打印 SQL 日志 |
| `charset` | string | utf8mb4 | 字符集 |
| `timezone` | string | Asia/Shanghai | 时区 |

### redis - Redis 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `host` | string | 127.0.0.1 | Redis 主机地址 |
| `port` | int | 6379 | Redis 端口 |
| `password` | string | - | Redis 密码（无密码留空） |
| `database` | int | 1 | Redis 数据库索引（0-15） |
| `max_connections` | int | 10 | 最大连接数 |
| `socket_timeout` | int | 5 | 连接超时时间（秒） |
| `retry_on_timeout` | bool | true | 超时是否自动重试 |

### upload - 文件上传配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `storage_type` | string | local | 存储类型：local/aliyun_oss/tencent_cos |
| `max_file_size` | int | 100 | 最大文件大小（MB） |
| `local_upload_path` | string | data/local_uploads | 本地上传目录 |
| `local_url_prefix` | string | /uploads | 文件访问 URL 前缀 |
| `allowed_extensions` | list | [...] | 允许的文件扩展名 |

**云存储配置（storage_type 非 local 时）：**

| 配置项 | 说明 |
|--------|------|
| `cloud_access_key` | 云存储 Access Key |
| `cloud_secret_key` | 云存储 Secret Key |
| `cloud_endpoint` | 云存储 Endpoint |
| `cloud_bucket` | 存储桶名称 |
| `cloud_domain` | CDN 域名（可选） |

### email - 邮件配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `host` | string | smtp.qq.com | SMTP 服务器地址 |
| `port` | int | 465 | SMTP 端口（SSL: 465, TLS: 587） |
| `username` | string | - | 邮箱账号 |
| `password` | string | - | SMTP 授权码（非登录密码） |
| `from_addr` | string | - | 发件人地址 |

::: tip 常用 SMTP 服务器
- QQ 邮箱：smtp.qq.com:465
- 163 邮箱：smtp.163.com:465
- Gmail：smtp.gmail.com:587
:::

### map - 地图服务配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `provider` | string | baidu | 服务商：baidu/amap |
| `ak` | string | - | Access Key |
| `sk` | string | - | Secret Key |

## 🔧 配置读取

在代码中读取配置：

```python
from utils.config import config

# 获取应用配置
app_name = config.app().name
port = config.app().port

# 获取数据库配置
db_host = config.database().host
db_password = config.database().password.get_secret_value()

# 获取 JWT 配置
jwt_secret = config.jwt().secret_key
expire = config.jwt().expire_minutes
```

## 📝 动态修改配置

```python
from utils.config import config

# 修改配置值
config.set_config_value("app.port", 8080)
config.set_config_value("database.host", "192.168.1.100")

# 导出配置到文件
config.export_to_yaml("config_backup.yaml")
```
