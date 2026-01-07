## Release {{RELEASE_TAG}}

🎯 **在线演示**: [https://fva.hygc.site](https://fva.hygc.site) - 账号: `admin` 密码: `admin123@*`

📚 **文档地址**: [https://sonderzhong.github.io/FastAPI-Vue-Admin/](https://sonderzhong.github.io/FastAPI-Vue-Admin/)

### 📦 下载地址
| 类型 | 文件 | 说明 |
|------|------|------|
{{DIST_ROW}}
{{SERVER_ROW}}

---

### 🖥️ 后端部署

```bash
# 1. 解压文件
unzip server-x.x.x.zip -d /path/to/server

# 2. 创建虚拟环境
cd /path/to/server
python -m venv venv

# 3. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置 config.yaml（数据库、Redis等）

# 6. 启动服务
python main.py
```

首次启动会自动进入初始化向导页面 http://localhost:9090

---

### 🌐 Nginx 代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api {
        rewrite ^.+api/?(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $http_connection;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
    }
    
    # 文件代理
    location /files {
        proxy_pass http://127.0.0.1:9090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }
}
```
