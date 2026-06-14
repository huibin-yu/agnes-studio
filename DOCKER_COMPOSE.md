# Agnes Studio - Docker Compose 部署指南

## 概述

Agnes Studio 支持通过 `docker compose` 一键启动整个项目，包括后端（FastAPI）和前端（Next.js）。

## 前置要求

- Docker Engine 20.10+
- Docker Compose V2 (v2.0+)
- Agnes AI API Key（从 https://platform.agnes-ai.com 获取）

## 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd agnes-studio

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 Agnes AI API Key

# 3. 一键启动
docker compose up -d

# 4. 查看日志
docker compose logs -f

# 5. 访问
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 方式二：使用自动安装脚本

```bash
# 自动检测 Docker 并启动项目
chmod +x setup.sh
bash setup.sh
```

## 常用命令

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 停止并删除数据卷（会清除所有数据！）
docker compose down -v

# 查看日志
docker compose logs -f backend    # 后端日志
docker compose logs -f frontend   # 前端日志
docker compose logs -f            # 所有日志

# 查看运行状态
docker compose ps

# 重启某个服务
docker compose restart backend
docker compose restart frontend

# 重新构建镜像
docker compose up -d --build

# 查看资源使用
docker stats

# 进入后端容器
docker compose exec backend bash

# 进入前端容器
docker compose exec frontend sh

# 备份数据库
docker compose exec backend cp /app/data/agnes_studio.db /tmp/backup.db
docker cp agnes-studio-backend:/tmp/backup.db ./backup.db

# 查看数据库状态
docker compose exec backend python -c "
from app.core.database import engine
import sqlalchemy
print(sqlalchemy.inspect(engine).get_table_names())
"
```

## 环境变量说明

| 变量 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `AGNES_API_KEY` | ✅ | Agnes AI API Key | - |
| `AGNES_API_BASE` | ❌ | API 地址 | `https://apihub.agnes-ai.com/v1` |
| `SECRET_KEY` | ❌ | JWT 密钥 | `change-me-in-production` |
| `DATABASE_URL` | ❌ | 数据库连接 | `sqlite+aiosqlite:///./agnes_studio.db` |
| `BASE_URL` | ❌ | 前端 URL（用于 CORS） | `http://localhost:3000` |

## 数据持久化

Docker Compose 使用以下命名卷来持久化数据：

| 卷名 | 用途 | 说明 |
|------|------|------|
| `db_data` | SQLite 数据库 | 用户数据、生成记录 |
| `upload_data` | 上传文件 | 用户上传的图片 |
| `generated_data` | 生成内容 | 生成的图片和视频 |

数据存储在 Docker 管理的位置，不是宿主机文件系统。

### 数据备份

```bash
# 备份数据库
docker compose exec backend cp /app/data/agnes_studio.db /tmp/backup.db
docker cp agnes-studio-backend:/tmp/backup.db ./backup.db

# 备份所有数据卷
docker run --rm -v agnes-studio_db_data:/source -v $(pwd):/backup alpine tar czf /backup/db_backup.tar.gz -C /source .
docker run --rm -v agnes-studio_upload_data:/source -v $(pwd):/backup alpine tar czf /backup/upload_backup.tar.gz -C /source .
docker run --rm -v agnes-studio_generated_data:/source -v $(pwd):/backup alpine tar czf /backup/generated_backup.tar.gz -C /source .
```

### 数据恢复

```bash
# 恢复数据库
docker compose down
docker run --rm -v agnes-studio_db_data:/target -v $(pwd):/backup alpine tar xzf /backup/db_backup.tar.gz -C /target
docker compose up -d
```

## 生产环境部署

### Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Generated content (static files)
    location /generated/ {
        alias /path/to/generated/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 生产环境 docker-compose.yml

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - AGNES_API_KEY=${AGNES_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - BASE_URL=https://your-domain.com
    volumes:
      - db_data:/app/data
      - upload_data:/app/uploads
      - generated_data:/app/generated
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    depends_on:
      backend:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

volumes:
  db_data:
  upload_data:
  generated_data:
```

使用时指定生产配置：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 使用 Docker Secret 管理密钥

```bash
# 将密钥写入文件
echo -n "your-agnes-api-key" > .agnes_api_key
echo -n "your-secret-key" > .secret_key

# 添加密钥到 docker-compose.yml
# backend 服务中添加:
# secrets:
#   - agnes_api_key
#   - secret_key
# environment:
#   AGNES_API_KEY: file:/run/secrets/agnes_api_key
#   SECRET_KEY: file:/run/secrets/secret_key

# 启动
docker compose up -d

# 清理密钥文件
rm .agnes_api_key .secret_key
```

## 故障排查

### 后端无法启动

```bash
# 查看日志
docker compose logs backend

# 常见问题：
# 1. AGNES_API_KEY 未配置 - 检查 .env 文件
# 2. 端口被占用 - 修改 docker-compose.yml 中的端口映射
# 3. 依赖安装失败 - 检查 requirements.txt 中的包是否可用
```

### 前端无法访问后端

```bash
# 确认后端健康检查通过
docker compose ps

# 测试后端 API
curl http://localhost:8000/api/health

# 查看前端日志
docker compose logs frontend

# 常见问题：
# 1. NEXT_PUBLIC_API_URL 配置错误
# 2. 后端服务未就绪（depends_on + healthcheck 已处理）
# 3. CORS 配置问题
```

### 数据丢失

```bash
# 检查数据卷是否存在
docker volume ls | grep agnes-studio

# 重新挂载数据卷
docker compose down
docker compose up -d
```

### 重新构建镜像

```bash
# 清除所有缓存并重新构建
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 监控

```bash
# 实时监控资源使用
docker stats

# 查看容器详细信息
docker inspect agnes-studio-backend
docker inspect agnes-studio-frontend

# 检查端口占用
docker compose port backend 8000
docker compose port frontend 3000
```

## 更新

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose down
docker compose build
docker compose up -d

# 数据库迁移（如果需要）
docker compose exec backend alembic upgrade head
```

## 卸载

```bash
# 停止并删除容器
docker compose down

# 停止并删除容器和数据卷（彻底删除所有数据！）
docker compose down -v

# 删除镜像
docker rmi $(docker images -q agnes-studio*)
```
