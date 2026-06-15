<!--
╔══════════════════════════════════════════════════════════════════════╗
║  DreamSeed 种梦计划 — AI创造者大赛  官方 README 模板                ║
║                                                                      ║
║  使用说明：                                                          ║
║  1. 将本模板放在参赛仓库根目录 README.md 的顶部                       ║
║  2. 头图使用 DreamField 官方公开活动图片地址                         ║
║  3. 请保留 DREAMFIELD_README_HEADER_START / END 标识                 ║
║  4. 分割线以下供创作者自由编写项目内容                               ║
╚══════════════════════════════════════════════════════════════════════╝
-->

<!-- DREAMFIELD_README_HEADER_START -->

<p align="center">
  <a href="https://www.dreamfield.top">
      <img src="https://www.dreamfield.top/dream-field/contest-readme/assets/dreamseed-readme-banner.png" alt="DreamSeed 种梦计划参赛作品" width="100%" />
  </a>
</p>

<!-- DREAMFIELD_README_HEADER_END -->


# Agnes Studio - AI 生图生视频平台

基于 Agnes AI API 构建的生产级生图生视频网站。

## 技术栈

### 前端
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn/ui
- Framer Motion (动画)
- Zustand (状态管理)

### 后端
- FastAPI (Python 3.11+)
- SQLAlchemy (ORM)
- SQLite (AIOSQLite)
- JWT 认证
- httpx (异步 HTTP)

## 功能特性

- [x] 用户系统（注册/登录/积分管理）
- [x] 文生图（14+ 风格/多尺寸/参数调节）
- [x] 图生图（风格迁移/编辑）
- [x] 文生视频（前端轮询/进度追踪）
- [x] 图生视频
- [x] 作品画廊（分类/收藏/分享/下载）
- [x] 积分充值系统
- [x] API Key 管理

## 快速开始

### 安装

```bash
# 安装前端依赖
cd frontend
npm install

# 安装后端依赖
cd ../backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env` 并填入 Agnes AI API Key：

```bash
cp .env.example .env
```

### 启动

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# 启动前端（新终端）
cd ../frontend
npm run dev
```

访问 http://localhost:3000

## 项目结构

```
agnes-studio/
├── frontend/           # Next.js 前端
│   ├── app/            # App Router 页面
│   ├── components/     # UI 组件
│   ├── lib/            # 工具函数
│   ├── stores/         # Zustand 状态管理
│   └── public/         # 静态资源
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── api/        # API 路由
│   │   ├── core/       # 核心配置
│   │   ├── models/     # 数据模型
│   │   ├── schemas/    # Pydantic 模型
│   │   └── services/   # 业务逻辑
│   ├── uploads/        # 上传文件
│   └── generated/      # 生成结果存储
└── docker-compose.yml  # Docker 编排
```

## 部署

详见 [DEPLOYMENT.md](DEPLOYMENT.md)

## License

MIT
