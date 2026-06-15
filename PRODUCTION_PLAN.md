# Agnes Studio 生产级商业化改造计划

## 阶段一：致命 Bug 修复与安全加固（P0）
> 阻塞一切：不修复则平台无法正常运行

### 1.1 前端 Token 存储 Key 不匹配
- `stores/auth.ts` 写入 `access_token`，`lib/api.ts` 读取 `auth_token`
- 修复：统一为 Zustand store 直接提供 token，移除 localStorage 直接读写

### 1.2 安全漏洞修复
- 添加 `.dockerignore` 防止密钥泄露到 Docker 镜像
- 启动时强制校验 SECRET_KEY 不能为默认值
- 修复头像上传路径遍历（调用 sanitize_filename）
- 修复删除图片端点的 async/sync 不兼容
- API Key 列表接口不返回明文 key
- CORS 限制具体 methods 和 headers
- 错误响应不再暴露内部异常详情

### 1.3 前端致命 Bug
- 修复图片生成默认模型 ID 不匹配 IMAGE_MODELS
- 修复 profile 页面运算符优先级 bug
- 修复 Download/Share/Like 按钮无 onClick

## 阶段二：核心基础设施（P1）
> 没有这些，平台无法承载真实用户

### 2.1 后端日志框架
- 引入 structlog，结构化 JSON 日志
- 认证事件、生成请求、积分变动、错误全量记录

### 2.2 速率限制
- 引入 slowapi
- 登录/注册：5次/分钟
- 生成接口：按用户积分和 API Key 限制

### 2.3 数据库优化
- 关键字段添加索引（user_id, video_id, is_public）
- count 查询改用 func.count()
- 修复浏览/点赞计数竞态条件
- 访问令牌过期时间从 7 天缩短到 15 分钟

### 2.4 前端错误处理
- 添加全局 Error Boundary (error.tsx)
- 添加路由级 loading.tsx
- 修复静默吞错（gallery, profile）
- API 请求添加 timeout 和重试逻辑
- 视频轮询添加最大重试次数

### 2.5 前端性能优化
- 搜索防抖
- 图片使用 Next.js Image 组件
- 替换 framer-motion 为 CSS 动画（loading 组件）

## 阶段三：商业化核心功能（P2）
> 没有这些，平台无法产生收入

### 3.1 支付系统
- 后端：Transaction 模型、积分充值 API、Stripe/支付宝集成
- 前端：TopUp 页面接入真实支付
- Webhook 回调处理支付确认

### 3.2 邮件系统
- 注册邮箱验证
- 密码重置（忘记密码）
- 生成完成通知

### 3.3 内容审核
- Prompt 安全过滤（敏感词/NSFW）
- 生成结果审核机制
- 用户举报功能

### 3.4 法律合规
- 服务条款页面
- 隐私政策页面
- Cookie 同意横幅
- 用户数据导出/删除（GDPR）

## 阶段四：运营能力（P3）
> 没有这些，团队无法管理平台

### 4.1 管理后台
- 用户管理（查看/封禁/删除）
- 内容审核队列
- 积分手动调整
- 系统配置

### 4.2 监控与可观测性
- Sentry 错误追踪
- 请求链路追踪
- 性能指标收集
- 告警配置

### 4.3 CI/CD
- GitHub Actions 流水线
- 自动化 lint + test + build
- Docker 镜像自动构建推送

### 4.4 测试体系
- 后端：API 端点集成测试、服务层单元测试
- 前端：关键路径 E2E 测试

## 阶段五：体验优化（P4）
> 提升留存和转化

### 5.1 SEO 优化
- Open Graph / Twitter Card 元标签
- 结构化数据 (JSON-LD)
- 每个页面独立 metadata

### 5.2 无障碍优化
- aria-label、表单关联、键盘导航
- 色彩对比度修正

### 5.3 画廊增强
- 分页 UI
- 搜索空状态提示
- 无限滚动

### 5.4 i18n 国际化
- 引入 next-intl
- 中英文双语支持

---

## 执行顺序

**当前开始：阶段一**（预计 2-3 小时）
按 1.1 → 1.2 → 1.3 顺序逐项修复，每项完成后验证。

---

## 执行记录

### 阶段一完成 ✅ (2026-06-12)

#### 1.1 前端 Token 存储 Key 不匹配 ✅
- `stores/auth.ts`: 移除手动 localStorage 操作，Zustand persist 自动管理
- `lib/api.ts`: 从 Zustand persist 的 localStorage key `auth-storage` 读取 token
- 添加了自动 refresh token 逻辑（401 时自动刷新重试）

#### 1.2 安全漏洞修复 ✅
- 添加 `.dockerignore` 防止密钥泄露到 Docker 镜像
- `config.py`: SECRET_KEY 启动时强制校验不能为默认值
- `.env`: 生成了 64 字节安全随机 SECRET_KEY
- `users.py`: 头像上传调用 `sanitize_filename()`，验证 magic bytes，限制 5MB
- `images.py`: 修复删除端点 async/sync 不兼容（改用 `delete()` 语句）
- `api_keys.py`: 列表接口返回 `key_prefix` 而非明文 key
- `main.py`: CORS 限制具体 methods 和 headers
- 所有 API 错误响应不再暴露内部异常详情（日志记录，返回通用消息）
- 全局异常处理兜底

#### 1.3 前端致命 Bug ✅
- 修复默认模型 ID `'agnes-image-2.1-flash'` → `'agnes-image-v20'`
- 修复 profile 页面运算符优先级：`?? 0 +` → `(?? 0) +`
- 修复 Download 按钮：添加文件下载逻辑
- 修复 Share 按钮：添加 Web Share API / 剪贴板回退
- 移除了 Like 按钮（需要后端 API 支持）
- Profile 页面 API Key 和充值卡片添加 Link 跳转
- ESLint 配置修复

#### 额外修复
- `video_service.py`: `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `video_service.py`: 改用 SQLAlchemy select 语法
- `image_service.py`: count 查询改用 `func.count()`
- `users.py`: stats 查询改用 `func.count()`
- 数据库模型添加索引：`user_id`, `video_id`, `is_public`
- 外键添加 `ondelete="CASCADE"`
- 画廊服务：浏览/点赞计数改用原子 UPDATE 防竞态
- 画廊搜索：LIKE 模式转义防注入
- API 请求添加 30 秒 timeout
- `auth.py`: refresh token 过期时间从硬编码 30 天改为配置项
- 密码最小长度 6 → 8
- 所有后端模块添加结构化日志
- 数据库连接池配置（PostgreSQL 优化）

#### 构建验证 ✅
- 前端 `next build` 通过，无类型错误
- ESLint 通过（仅 `<img>` 警告，阶段二修复）

### 阶段二部分完成 ✅ (2026-06-12)

#### 2.4 前端错误处理 ✅
- `error.tsx`: 全局 Error Boundary（中文提示 + 重试按钮）
- `not-found.tsx`: 自定义 404 页面
- `loading.tsx`: 全局路由级 loading 状态
- 画廊页面：错误状态展示 + 重试按钮
- 视频页面：轮询最大次数限制（120 次 = 10 分钟超时）

#### 2.5 前端性能优化 ✅
- 画廊搜索：300ms 防抖，避免每次按键请求
- `loading.tsx` 组件：framer-motion 替换为 CSS `animate-pulse`
- ESLint 配置修复

#### 前端可访问性修复 ✅
- 视频页面：表单输入添加 `id` + `label` 关联
- 视频模板卡片：`<div onClick>` 改为 `<button type="button">`
- 错误处理：`catch (err: any)` 替换为类型安全写法
- 视频页面 UI 文本中文化

### 资损与越权急修包完成 ✅ (2026-06-15)

#### 阶段 1：图像失败不扣积分 ✅
- `image_service.generate` 仅在 `image_url` 非空且上游未异常时扣 `IMAGE_COST`
- 上游异常：积分不变，抛 503
- 上游返回空 url：记录 `status=failed`，积分不变

#### 阶段 2：视频积分扣减 ✅
- `video_generations` 新增 `credits_charged` 列
- `create_video` 上游成功后按 `ceil(duration * VIDEO_COST_PER_SECOND)` 扣分
- 余额不足返 402；上游失败不扣分
- `VideoGenerateResponse` 暴露 `credits_charged`
- 已知限制见 `docs/KNOWN_ISSUES.md`

#### 阶段 3：积分 ledger + 行锁 ✅
- 新增 `credit_transactions` 表 + `CreditService`（charge / grant / get_user_transactions）
- `with_for_update()` 行锁防并发超扣（PG 生效，SQLite no-op）
- `image_service` / `video_service` / `auth_service.register` 全部改走 ledger
- 新增 `GET /api/users/credits/transactions` 流水分页查询
- 历史用户回填脚本：`backend/scripts/backfill_credit_ledger.py`

#### 阶段 4：视频越权 + URL bug ✅
- `poll_video_status` 强制 `user_id` 校验，越权返 404
- `_extract_video_url` 纯函数按 fallback 顺序取 URL，拒绝非 http 字符串
- 无 URL 时判失败并退款（`credits_charged` 置 0 防重入）
- `failed` 状态首次见到时退款，幂等

#### Commits
- `f2204ab` fix(image): 仅在生成成功时扣减积分
- `78c75ac` feat(video): 添加 credits_charged 列
- `17f72d4` feat(video): 视频生成预扣积分
- `5afde95` docs: 已知限制
- `932990f` feat(credit): CreditTransaction 模型
- `8c5f287` feat(credit): CreditService
- `b9edd39` refactor(image): 扣分改走 ledger
- `7a9b870` refactor(video): 扣分改走 ledger
- `c71d2d8` refactor(auth): 注册赠送改走 grant
- `d1208c9` feat(api): 流水查询 API
- `b301993` feat(credit): 回填脚本
- `5234ad3` fix(video): 越权校验 + URL bug + 退款
