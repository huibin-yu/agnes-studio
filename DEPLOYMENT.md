# Agnes Studio 部署指南

## 项目概述

Agnes Studio 是一个基于 Agnes AI API 构建的生产级 AI 生图生视频平台。完全兼容 Agnes AI 官方文档，支持：
- 文生图（14+ 风格/多尺寸）
- 图生图（风格迁移/编辑）
- 文生视频（前端轮询/进度追踪）
- 图生视频
- 用户系统、积分管理、社区画廊

## 技术栈

### 前端
- Next.js 15 (App Router) + TypeScript
- Tailwind CSS + Shadcn/ui
- Zustand (状态管理)
- Axios (HTTP 客户端)

### 后端
- FastAPI (Python 3.11+)
- SQLAlchemy (ORM) + AIOSQLite
- JWT 认证
- httpx (异步 HTTP)
- **无需 Redis/Celery，简化部署**

## Agnes AI API 配置

### 官方文档
- 总览：https://agnes-ai.com/doc/overview
- 视频文档：https://agnes-ai.com/doc/agnes-video-v20

### 关键配置
- **Base URL**: `https://apihub.agnes-ai.com/v1`
- **认证**: `Authorization: Bearer YOUR_API_KEY`
- **图片模型**: `agnes-image-2.1-flash`（推荐）或 `agnes-image-2.0-flash`
- **视频模型**: `agnes-video-v2.0`
- **当前价格**: 免费（RPM ≤ 20）

### 重要注意事项
1. **图片生成**：`response_format` 必须放在 `extra_body` 中，不能放顶层
2. **图生图**：`image` 参数必须放在 `extra_body.image` 数组中
3. **视频生成**：必须使用 `video_id` 查询结果（不要用 `task_id`）
4. **视频帧数**：必须是 `8n+1` 且 ≤ 441（有效值：81, 121, 161, 241, 441）
5. **轮询间隔**：建议 5 秒

## 本地开发

### 1. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，填入 Agnes AI API Key
```

### 2. 启动后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost:3000

## 生产环境部署

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /generated/ {
        alias /path/to/backend/generated/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 环境变量配置

```bash
# .env.production
AGNES_API_KEY=your_production_key
SECRET_KEY=your_production_secret_key
DATABASE_URL=sqlite+aiosqlite:///./agnes_studio.db
BASE_URL=https://your-domain.com
```

### 使用 Gunicorn + Uvicorn

```bash
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

## 监控和维护

### 清理过期视频记录
```bash
python -c "
from app.services.video_service import video_service
import asyncio
from app.core.database import async_session

async def cleanup():
    async with async_session() as db:
        await video_service.cleanup_expired_videos(db)

asyncio.run(cleanup())
"
```

### 数据库备份
```bash
# SQLite
cp backend/agnes_studio.db backup_$(date +%Y%m%d).db
```

## 安全建议

1. 使用 HTTPS
2. 定期更新 SECRET_KEY
3. 设置合理的 CORS 配置
4. 启用数据库加密
5. 定期备份数据
6. 使用 CDN 加速静态资源
