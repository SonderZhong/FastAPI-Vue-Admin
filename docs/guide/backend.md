# 🔧 后端知识库

FastAPI-Vue-Admin 后端基于 **FastAPI + Tortoise-ORM + Casbin** 构建，采用全异步架构，提供高性能的 API 服务。

## 🚀 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步 Web 框架 |
| ORM | Tortoise-ORM | 异步 ORM，支持 MySQL/PostgreSQL/SQLite |
| 数据验证 | Pydantic | 数据验证和序列化 |
| 权限控制 | Casbin | RBAC/ABAC 权限引擎 |
| 缓存 | Redis | 会话存储、数据缓存 |
| 认证 | JWT | JSON Web Token 身份认证 |
| 日志 | Loguru | 结构化日志记录 |

## 📁 目录结构

```
server/
├── main.py                 # 应用入口（自动检测配置）
├── app.py                  # FastAPI 应用实例
├── config.yaml             # 配置文件（初始化后生成）
├── requirements.txt        # Python 依赖
├── uvicorn_config.json     # Uvicorn 日志配置
│
├── apis/                   # API 路由层
├── models/                 # 数据模型层
├── schemas/                # Pydantic 模型
├── annotation/             # 装饰器（认证、日志）
├── middlewares/            # 中间件
├── exceptions/             # 异常处理
├── utils/                  # 工具函数
├── setup/                  # 初始化向导
├── fva_mcp/               # MCP 服务
├── migrations/             # 数据库迁移脚本
├── templates/              # 邮件模板等
├── assets/                 # 静态资源
├── uploads/                # 上传文件存储
└── logs/                   # 日志文件
```

## 🎯 启动流程

### 入口文件 `main.py`

```python
def main():
    if check_config_exists():
        # 配置文件存在，启动主应用
        start_main_app()
    else:
        # 配置文件不存在，启动初始化向导
        start_setup_server()
```

**启动逻辑：**
1. 检测 `config.yaml` 是否存在
2. 不存在 → 启动初始化向导（端口 9090）
3. 存在 → 启动主应用

### 应用实例 `app.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    app.state.redis = await RedisUtil.create_redis_connection()
    await init_db()                          # 初始化数据库
    await CasbinEnforcer.init(app.state.redis)  # 初始化权限引擎
    yield
    # 关闭时执行
    await close_db()
    await RedisUtil.close_redis_connection(app.state.redis)

app = FastAPI(
    title=config.app().name,
    lifespan=lifespan,
)
```

## 📂 核心模块详解

### 1. APIs 路由层 (`apis/`)

API 路由按功能模块组织：

| 文件 | 说明 | 主要接口 |
|------|------|----------|
| `auth.py` | 认证接口 | 登录、登出、刷新Token |
| `user.py` | 用户管理 | 用户CRUD、状态管理 |
| `role.py` | 角色管理 | 角色CRUD、权限分配 |
| `department.py` | 部门管理 | 部门树、组织架构 |
| `permission.py` | 权限管理 | 菜单/按钮/API权限 |
| `config.py` | 配置管理 | 系统参数配置 |
| `cache.py` | 缓存管理 | Redis缓存操作 |
| `file.py` | 文件管理 | 文件上传下载 |
| `notification.py` | 通知管理 | 系统通知 |
| `log.py` | 日志管理 | 操作日志、登录日志 |
| `server.py` | 服务监控 | 服务器状态 |
| `dashboard.py` | 仪表盘 | 统计数据 |

**路由注册示例：**

```python
# apis/__init__.py
from fastapi import FastAPI
from apis import auth, user, role, department, permission

def register_api(app: FastAPI):
    app.include_router(auth.router, prefix="/auth", tags=["认证"])
    app.include_router(user.router, prefix="/user", tags=["用户管理"])
    # ...
```

### 2. Models 数据模型层 (`models/`)

基于 Tortoise-ORM 的数据模型：

| 文件 | 模型 | 说明 |
|------|------|------|
| `user.py` | `SystemUser` | 用户表 |
| `role.py` | `SystemRole` | 角色表 |
| `department.py` | `SystemDepartment` | 部门表 |
| `permission.py` | `SystemPermission` | 权限表 |
| `config.py` | `SystemConfig` | 配置表 |
| `log.py` | `OperationLog`, `LoginLog` | 日志表 |
| `notification.py` | `SystemNotification` | 通知表 |
| `file.py` | `SystemFile` | 文件表 |
| `casbin.py` | `CasbinRule` | Casbin规则表 |
| `common.py` | `BaseModel` | 基础模型类 |

**模型示例：**

```python
# models/user.py
from tortoise import fields
from models.common import BaseModel

class SystemUser(BaseModel):
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password = fields.CharField(max_length=128, description="密码")
    nickname = fields.CharField(max_length=50, null=True, description="昵称")
    avatar = fields.CharField(max_length=255, null=True, description="头像")
    status = fields.IntField(default=1, description="状态：1启用 0禁用")
    user_type = fields.IntField(default=3, description="用户类型")
    department = fields.ForeignKeyField(
        "system.SystemDepartment", 
        related_name="users",
        null=True
    )

    class Meta:
        table = "system_user"
        app = "system"
```

### 3. Schemas 数据验证层 (`schemas/`)

Pydantic 模型用于请求/响应数据验证：

| 文件 | 说明 |
|------|------|
| `auth.py` | 登录请求/响应模型 |
| `user.py` | 用户CRUD模型 |
| `role.py` | 角色CRUD模型 |
| `department.py` | 部门CRUD模型 |
| `permission.py` | 权限CRUD模型 |
| `common.py` | 通用模型（分页、响应等） |

**Schema 示例：**

```python
# schemas/user.py
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    nickname: str | None = Field(None, max_length=50, description="昵称")
    department_id: str | None = Field(None, description="部门ID")

class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str | None
    status: int
    created_at: datetime
```

### 4. Annotation 装饰器 (`annotation/`)

| 文件 | 装饰器 | 说明 |
|------|--------|------|
| `auth.py` | `@Auth` | 权限验证装饰器 |
| `auth.py` | `@DataPermission` | 数据权限装饰器 |
| `log.py` | `@Log` | 操作日志记录装饰器 |

**权限装饰器使用：**

```python
from annotation.auth import Auth
from annotation.log import Log

@router.get("/list")
@Auth(permission_list=["user:btn:list", "GET:/user/list"])
@Log(title="用户管理", business_type=4)
async def get_user_list(request: Request):
    # 业务逻辑
    pass
```

**权限格式说明：**
- 按钮权限：`模块:btn:操作`，如 `user:btn:add`
- API权限：`METHOD:/path`，如 `GET:/user/list`

### 5. Utils 工具函数 (`utils/`)

| 文件 | 说明 | 主要函数/类 |
|------|------|-------------|
| `config.py` | 配置加载器 | `ConfigLoader`, `config` |
| `database.py` | 数据库连接 | `init_db()`, `close_db()` |
| `get_redis.py` | Redis 连接 | `RedisUtil`, `RedisKeyConfig` |
| `response.py` | 响应封装 | `ResponseUtil` |
| `casbin.py` | 权限引擎 | `CasbinEnforcer` |
| `password.py` | 密码处理 | `hash_password()`, `verify_password()` |
| `captcha.py` | 验证码 | `generate_captcha()` |
| `log.py` | 日志工具 | `logger` |
| `mail.py` | 邮件发送 | `send_email()` |
| `storage.py` | 文件存储 | `StorageService` |
| `geoip.py` | IP定位 | `get_ip_location()` |

**响应工具使用：**

```python
from utils.response import ResponseUtil

# 成功响应
return ResponseUtil.success(data={"id": 1}, msg="创建成功")

# 失败响应
return ResponseUtil.failure(msg="用户名已存在")

# 分页响应
return ResponseUtil.success(data={"list": users, "total": 100})
```

**配置读取：**

```python
from utils.config import config

# 获取应用配置
app_name = config.app().name
port = config.app().port

# 获取数据库配置
db_host = config.database().host

# 获取 JWT 配置
jwt_secret = config.jwt().secret_key
```

### 6. Middlewares 中间件 (`middlewares/`)

| 文件 | 说明 |
|------|------|
| `cors.py` | 跨域处理 |
| `gzip.py` | Gzip 压缩 |
| `casbin.py` | Casbin 权限中间件 |
| `handle.py` | 中间件注册 |

**中间件注册：**

```python
# middlewares/handle.py
def handle_middleware(app: FastAPI):
    # CORS 跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Gzip 压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 7. Exceptions 异常处理 (`exceptions/`)

| 文件 | 说明 |
|------|------|
| `exception.py` | 自定义异常类 |
| `handle.py` | 全局异常处理器 |

**自定义异常：**

```python
# exceptions/exception.py
class AuthException(Exception):
    """认证异常"""
    def __init__(self, message: str = "认证失败", data: Any = None):
        self.message = message
        self.data = data

class PermissionException(Exception):
    """权限异常"""
    def __init__(self, message: str = "无权限访问"):
        self.message = message
```

**使用异常：**

```python
from exceptions.exception import AuthException, PermissionException

# 抛出认证异常
raise AuthException(message="用户token已失效")

# 抛出权限异常
raise PermissionException(message="该用户无此接口权限")
```

## ⚙️ 配置文件

### config.yaml 结构

```yaml
# 应用配置
app:
  env: dev                    # 环境：dev/prod
  name: FastAPI-Vue-Admin     # 应用名称
  host: 0.0.0.0              # 监听地址
  port: 9090                  # 监听端口
  reload: true                # 热重载（开发环境）
  api_prefix: /dev-api        # API前缀

# JWT 配置
jwt:
  secret_key: your-secret-key # JWT密钥
  algorithm: HS256            # 签名算法
  expire_minutes: 1440        # 过期时间（分钟）

# 数据库配置
database:
  engine: mysql               # 数据库类型
  host: 127.0.0.1
  port: 3306
  username: root
  password: your-password
  database: fva
  charset: utf8mb4
  timezone: Asia/Shanghai

# Redis 配置
redis:
  host: 127.0.0.1
  port: 6379
  password: ""
  database: 1

# 文件上传配置
upload:
  storage_type: local         # 存储类型：local/aliyun_oss/tencent_cos
  max_file_size: 100          # 最大文件大小（MB）
  local_upload_path: data/local_uploads

# 邮件配置
email:
  host: smtp.qq.com
  port: 465
  username: your-email@qq.com
  password: your-smtp-password
```

## 🔐 权限系统

### Casbin RBAC 模型

系统使用 Casbin 实现 RBAC 权限控制：

```
用户 (User) → 角色 (Role) → 权限 (Permission)
```

**权限类型：**
- **菜单权限** (menu_type=0)：控制页面访问
- **按钮权限** (menu_type=1)：控制操作按钮
- **API权限** (menu_type=2)：控制接口访问

**数据权限范围：**

| 值 | 说明 |
|----|------|
| 1 | 全部数据 |
| 2 | 本部门及下属部门 |
| 3 | 仅本部门 |
| 4 | 仅本人 |

### 权限使用示例

```python
from annotation.auth import Auth, DataPermission
from utils.casbin import CasbinEnforcer

# 接口权限控制
@router.post("/add")
@Auth(permission_list=["user:btn:add"])
async def add_user(request: Request):
    pass

# 数据权限控制
@router.get("/list")
@DataPermission()
async def get_list(request: Request):
    # 获取可访问的部门ID列表
    dept_ids = request.state.accessible_dept_ids
    # 根据部门过滤数据
    users = await SystemUser.filter(department_id__in=dept_ids)
```

## 📝 日志系统

### 日志装饰器

```python
from annotation.log import Log

@router.post("/add")
@Log(title="用户管理", business_type=1)  # 1=新增
async def add_user():
    pass

@router.put("/{id}")
@Log(title="用户管理", business_type=2)  # 2=修改
async def update_user():
    pass

@router.delete("/{id}")
@Log(title="用户管理", business_type=3)  # 3=删除
async def delete_user():
    pass
```

**业务类型：**
- 1：新增
- 2：修改
- 3：删除
- 4：查询
- 5：导出
- 6：导入

## 🛠️ 开发指南

### 新增 API 接口

1. **创建路由文件** `apis/example.py`

```python
from fastapi import APIRouter, Request
from annotation.auth import Auth
from annotation.log import Log
from utils.response import ResponseUtil

router = APIRouter()

@router.get("/list")
@Auth(permission_list=["example:btn:list"])
@Log(title="示例管理", business_type=4)
async def get_list(request: Request):
    return ResponseUtil.success(data=[])
```

2. **注册路由** `apis/__init__.py`

```python
from apis import example

def register_api(app: FastAPI):
    # ...
    app.include_router(example.router, prefix="/example", tags=["示例"])
```

### 新增数据模型

1. **创建模型** `models/example.py`

```python
from tortoise import fields
from models.common import BaseModel

class Example(BaseModel):
    name = fields.CharField(max_length=100)
    status = fields.IntField(default=1)

    class Meta:
        table = "example"
        app = "system"
```

2. **注册模型** `models/__init__.py`

```python
from models.example import Example
```

## 📚 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Tortoise-ORM 文档](https://tortoise.github.io/)
- [Casbin 文档](https://casbin.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)
