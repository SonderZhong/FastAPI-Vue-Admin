# 部署指南

## 后端部署

### 使用 Uvicorn

```bash
cd server
uvicorn app:app --host 0.0.0.0 --port 9090 --workers 4
```

### 使用 Gunicorn + Uvicorn

```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:9090
```

### 使用 Supervisor

创建配置文件 `/etc/supervisor/conf.d/fva.conf`：

```ini
[program:fva-backend]
command=/path/to/venv/bin/uvicorn app:app --host 0.0.0.0 --port 9090
directory=/path/to/server
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/fva/backend.log
stderr_logfile=/var/log/fva/backend-error.log
```

## 前端部署

### 构建

```bash
cd web
pnpm build
```

构建产物位于 `web/dist` 目录。

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/web/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 文件代理
    location /files/ {
        proxy_pass http://127.0.0.1:9090/files/;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://127.0.0.1:9090/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Docker 部署

### Dockerfile (后端)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9090

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9090"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./server
    ports:
      - "9090:9090"
    depends_on:
      - mysql
      - redis
    environment:
      - DATABASE_HOST=mysql
      - REDIS_HOST=redis

  frontend:
    build: ./web
    ports:
      - "80:80"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: fva
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

## 环境变量

生产环境建议通过环境变量配置敏感信息：

| 变量 | 说明 |
|------|------|
| DATABASE_HOST | 数据库主机 |
| DATABASE_PORT | 数据库端口 |
| DATABASE_USER | 数据库用户 |
| DATABASE_PASSWORD | 数据库密码 |
| DATABASE_NAME | 数据库名称 |
| REDIS_HOST | Redis 主机 |
| REDIS_PORT | Redis 端口 |
| REDIS_PASSWORD | Redis 密码 |
| JWT_SECRET | JWT 密钥 |
