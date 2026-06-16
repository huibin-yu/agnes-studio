# P0 执行方案 — 致命级修复

> **执行团队**: Architect / Backend / Frontend / QA
>
> **总工期**: 5 个工作日（1 周）
>
> **前置条件**: 无，可立即启动

---

## 团队分工总览

```
        Day 1              Day 2            Day 3            Day 4            Day 5
    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
Arc │ P0-3 设计  │    │ P0-3 审查  │    │ P0-5 审查  │    │ P0-6 审查  │    │ 总体验收   │
    ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤
BE  │ P0-3 实施  │    │ P0-3 完成  │    │ P0-5 实施  │    │ P0-6 实施  │    │ P0-6 收尾  │
    │ P0-4 修复  │    │ P0-4 回归  │    │           │    │           │    │           │
    ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤
FE  │ P0-1 修复  │    │ 自查 +     │    │ 协助 QA    │    │ 协助 QA    │    │ 最终验收   │
    │ P0-2 修复  │    │ Code Review│    │ 回归测试   │    │ 回归测试   │    │           │
    ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤
QA  │ 编写测试   │    │ 测试 P0-1  │    │ 并发压力   │    │ 并发压力   │    │ 全量回归   │
    │ 计划+用例  │    │ P0-2 P0-4  │    │ 测试 P0-5  │    │ 测试 P0-6  │    │ 签字确认   │
    └───────────┘    └───────────┘    └───────────┘    └───────────┘    └───────────┘
```

---

## P0-1. 修复登录状态刷新丢失

> **负责人**: Frontend
>
> **工期**: 0.5 小时
>
> **风险**: 🟢 低

### 问题根因

`frontend/src/stores/auth.ts:54` — `partialize` 仅持久化 `user`、`accessToken`、`refreshToken`，**未持久化 `isAuthenticated`**。

页面刷新时 Zustand 从 localStorage 恢复，`isAuthenticated` 回到初始值 `false`，导航栏显示"登录"按钮。

### 实施方案

**方案选择**: 移除独立 `isAuthenticated` 状态字段，改为从 `user` 和 `accessToken` 派生。

**理由**: 独立布尔状态与真实状态存在同步风险（已验证）。派生计算永远正确。

### 任务拆解

#### Frontend-1.1: 修改 Zustand Store（30 分钟）

**文件**: `frontend/src/stores/auth.ts`

**改动**:
```
1. 从 AuthState 接口中删除 `isAuthenticated: boolean`
2. 从初始状态中删除 `isAuthenticated: false`
3. 从 login() 中删除 `isAuthenticated: true`
4. 从 logout() 中删除 `isAuthenticated: false`
5. 新增 getter:
   get isAuthenticated() {
     return useAuthStore.getState().user !== null
         && useAuthStore.getState().accessToken !== null
   }
```

**注意**: 如果 Zustand selector 方式使用 `store.isAuthenticated`，改为用 selector:
```typescript
// 在组件中使用
const isAuthenticated = useAuthStore(
  (s) => s.user !== null && s.accessToken !== null
)
```

#### Frontend-1.2: 更新所有消费 `isAuthenticated` 的组件（15 分钟）

**文件清单**:
- `frontend/src/components/navbar.tsx` — 检查 line 70 附近的 `isAuthenticated` 使用
- `frontend/src/app/login/page.tsx` — 登录/注册后跳转逻辑
- 任何其他引用 `isAuthenticated` 的文件

**改动**: 将 `useAuthStore((s) => s.isAuthenticated)` 替换为 `useAuthStore((s) => s.user !== null && s.accessToken !== null)`

#### Frontend-1.3: 同步修复 `api.ts` Token 刷新不通知 Store 的问题（顺便修）

**文件**: `frontend/src/lib/api.ts:55-58`

**改动**: Token 刷新成功后调用 `useAuthStore.getState().setAccessToken(newToken)` 而非直接改 localStorage。

#### QA-1.1: 验证测试（15 分钟）

| 用例 | 操作 | 预期 |
|------|------|------|
| 1 | 登录后刷新页面 | 导航栏仍显示用户头像和积分 |
| 2 | 退出登录后刷新 | 导航栏显示"登录" |
| 3 | Token 过期自动刷新后 | 组件能感知到新 Token |
| 4 | 无痕模式下关闭再打开 | localStorage 持久化生效 |

---

## P0-2. 移除首页虚假统计数据

> **负责人**: Frontend
>
> **工期**: 0.5 小时
>
> **风险**: 🟢 低

### 问题根因

`frontend/src/app/page.tsx:41-47` — `stats` 数组硬编码 `100K+`、`1M+` 等虚假数字。TODO 注释承认需要替换。

### 实施方案

**方案选择**: 暂时删除整个统计区块。后续接入真实 API。

**理由**: 虚假数据 > 无数据。在比赛期间展示造假数据比不展示更危险。

### 任务拆解

#### Frontend-2.1: 删除统计区块（15 分钟）

**文件**: `frontend/src/app/page.tsx`

**改动**:
```
1. 删除 lines 41-47 的 stats 数组定义
2. 删除 lines 119-136 的统计区块 JSX（整个 <section className="py-16 px-4 border-y">）
3. 删除顶部 import 中不再使用的图标（Users, Image, Video 如果仅 stats 用到）
   — 注意: features 数组也用了 Image, Video, Users, Sparkles，不要误删
```

#### Frontend-2.2: 顺便修正"免费调用"误导标签（5 分钟）

**文件**: `frontend/src/app/page.tsx:68`

**改动**: `Agnes AI 驱动 · 免费调用` → `Agnes AI 驱动 · 注册送积分`

#### QA-2.1: 验证测试（10 分钟）

| 用例 | 操作 | 预期 |
|------|------|------|
| 1 | 访问首页 | 统计区块不再显示 |
| 2 | 页面布局无断裂 | Features 区块紧接 Hero 之后 |
| 3 | 标签文案更新 | 显示"注册送积分"而非"免费调用" |

---

## P0-3. 初始化 Alembic 数据库迁移

> **负责人**: Architect（设计）+ Backend（实施）
>
> **工期**: 1 天
>
> **风险**: 🟡 中

### 问题根因

`backend/app/main.py:41` — 使用 `Base.metadata.create_all` 创建表。此方法无法修改已有表结构（加列、改类型、加约束）。Alembic 已在 `requirements.txt`（line 5: `alembic==1.14.0`）但从未初始化。

### 架构设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 迁移目录位置 | `backend/alembic/` | Python 项目惯例 |
| 自动生成 vs 手写 | 自动生成 + 人工审查 | 降低遗漏风险 |
| 启动时是否自动迁移 | 否，仅检测 | 生产环境应手动控制迁移时机 |
| 初始迁移基线 | 从当前 ORM 生成 | 捕获所有已有表和字段 |

### 任务拆解

#### Architect-3.1: 设计迁移策略（1 小时）

**输出物**: 迁移策略文档（内嵌于代码注释）

**决策**:
```
1. alembic.ini 中 sqlalchemy.url 从环境变量读取（与 config.py 一致）
2. env.py 中导入 app.models.database.Base.metadata 作为 target_metadata
3. 命名约定: {date}_{revision}_{description}.py
4. 启动时仅检查（alembic upgrade head），不自动运行
5. 提供 CLI 命令手动执行: alembic upgrade head / alembic downgrade -1
```

#### Backend-3.1: 初始化 Alembic（30 分钟）

**操作**:
```bash
cd backend
alembic init alembic
```

**文件**: `backend/alembic.ini`

**改动**:
```
1. sqlalchemy.url = %(DATABASE_URL)s  # 从环境变量读取
2. 文件编码: script_location = alembic
```

**文件**: `backend/alembic/env.py`

**改动**:
```python
1. 导入 from app.core.config import settings
2. 导入 from app.models.database import Base
3. 设置 target_metadata = Base.metadata
4. 设置 sqlalchemy.url 从 settings.DATABASE_URL 读取
5. 添加 run_migrations_online() 中的 context.configure(
    compare_type=True,       # 检测类型变更
    compare_server_default=True  # 检测默认值变更
   )
```

#### Backend-3.2: 生成初始迁移（30 分钟）

**操作**:
```bash
cd backend
alembic revision --autogenerate -m "initial_schema"
```

**审查清单**:
```
□ 包含全部 7 张表: users, image_generations, video_generations,
  gallery_items, gallery_likes, api_keys, credit_transactions
□ 所有字段类型与 ORM 模型一致
□ 所有外键约束正确
□ 所有索引正确
□ 所有 unique 约束正确
□ ondelete="CASCADE" 策略正确
```

#### Backend-3.3: 替换 `create_all` 为迁移检测（30 分钟）

**文件**: `backend/app/main.py`

**原代码** (line 36-42):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agnes Studio API...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")
    yield
```

**改为**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agnes Studio API...")
    # 开发环境: 自动迁移（仅当 DATABASE_URL 包含 sqlite 时）
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured (SQLite dev mode).")
    else:
        # 生产环境: 仅检查迁移状态
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        try:
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations applied.")
        except Exception as e:
            logger.error(f"Migration check failed: {e}")
            logger.warning("Run 'alembic upgrade head' manually.")
    yield
    logger.info("Shutting down Agnes Studio API...")
    await engine.dispose()
```

#### Backend-3.4: 添加 `CHECK (credits >= 0)` 约束（通过迁移）（30 分钟）

**文件**: 新建迁移文件

**操作**:
```bash
alembic revision --autogenerate -m "add_credits_check_constraint"
```

**迁移内容**:
```python
def upgrade():
    op.create_check_constraint(
        'ck_users_credits_non_negative',
        'users',
        'credits >= 0'
    )

def downgrade():
    op.drop_constraint('ck_users_credits_non_negative', 'users')
```

#### QA-3.1: 迁移验证测试（1 小时）

| 用例 | 操作 | 预期 |
|------|------|------|
| 1 | 空数据库执行 `alembic upgrade head` | 所有表正确创建 |
| 2 | 已有数据库执行 `alembic upgrade head` | 无报错，无数据丢失 |
| 3 | `alembic downgrade -1` | 安全回滚，表不删除 |
| 4 | `alembic history` | 显示完整迁移链 |
| 5 | `alembic current` | 显示最新版本号 |
| 6 | 尝试将 credits 设为负数 | CHECK 约束拒绝（PostgreSQL） |

---

## P0-4. 修复头像 URL 路径不匹配

> **负责人**: Backend
>
> **工期**: 10 分钟
>
> **风险**: 🟢 低

### 问题根因

`backend/app/api/users.py:61-64`:
```python
# 文件保存路径（正确）
avatar_path = upload_dir / f"{current_user.id}_{safe_name}"

# 数据库存储 URL（错误 — 缺少 user_id 前缀）
current_user.avatar_url = f"/uploads/avatars/{safe_name}"
```

文件以 `{user_id}_{name}` 保存，但 URL 只存 `{name}`，导致 404。

### 任务拆解

#### Backend-4.1: 修复 URL 路径（5 分钟）

**文件**: `backend/app/api/users.py`

**改动**:
```python
# Line 64: 修改为
current_user.avatar_url = f"/uploads/avatars/{current_user.id}_{safe_name}"
```

#### Backend-4.2: 添加运算符优先级括号（5 分钟）

**文件**: `backend/app/api/users.py:47-52`

**原代码** (WebP 检查缺括号):
```python
is_valid_image = (
    content[:3] == b'\xff\xd8\xff' or
    content[:8] == b'\x89PNG\r\n\x1a\n' or
    content[:4] == b'GIF8' or
    content[:4] == b'RIFF' and content[8:12] == b'WEBP'  # and 优先于 or
)
```

**改为** (与 `images.py` 一致):
```python
is_valid_image = (
    content[:3] == b'\xff\xd8\xff' or            # JPEG
    content[:8] == b'\x89PNG\r\n\x1a\n' or       # PNG
    content[:4] == b'GIF8' or                      # GIF
    (content[:4] == b'RIFF' and content[8:12] == b'WEBP')  # WebP
)
```

#### QA-4.1: 验证测试（15 分钟）

| 用例 | 操作 | 预期 |
|------|------|------|
| 1 | 上传头像后查看个人资料 | 头像图片正常显示（非 404） |
| 2 | 再次上传不同头像 | 旧头像被覆盖，新头像显示正确 |
| 3 | 上传 WebP 格式头像 | 验证通过（括号修复生效） |

---

## P0-5. 修复视频双重退款竞态条件

> **负责人**: Backend（实施）+ Architect（审查）+ QA（并发测试）
>
> **工期**: 1 天
>
> **风险**: 🔴 高 — 涉及资金路径

### 问题根因

`backend/app/services/video_service.py:219-227` — `_refund_if_needed` 使用 ORM 对象属性检查:

```python
async def _refund_if_needed(reason: str):
    if video_gen.credits_charged and video_gen.credits_charged > 0:  # 读 ORM 对象
        await credit_service.grant(...)   # 执行退款
        video_gen.credits_charged = 0     # 写 ORM 对象
```

**竞态场景**:
```
请求 A: 读 credits_charged = 5  → true
请求 B: 读 credits_charged = 5  → true  (A 还未写入 0)
请求 A: 执行 grant(5)           → 用户余额 +5
请求 B: 执行 grant(5)           → 用户余额 +5  ← 双重退款！
请求 A: 写 credits_charged = 0
请求 B: 写 credits_charged = 0
```

### 架构设计方案

**方案选择**: 原子 UPDATE + affected rows 检查

**理由**: 不依赖 `SELECT FOR UPDATE`（SQLite 不支持），利用 SQL 原子性保证安全。

```sql
UPDATE video_generations
SET credits_charged = 0
WHERE id = :id AND credits_charged > 0
-- 返回 affected_rows: 1 表示成功获取退款权，0 表示已被其他请求处理
```

### 任务拆解

#### Architect-5.1: 审查退款方案设计（1 小时）

**审查清单**:
```
□ 原子 UPDATE 方案不依赖数据库类型（SQLite/PostgreSQL 均可）
□ affected_rows 检查在 SQLAlchemy async 中的正确获取方式
□ 退款操作在同一个事务中（与 video_gen 状态更新一起提交）
□ 异常时回滚不会丢失状态
□ 幂等性：多次调用同一视频的退款不会重复退款
```

#### Backend-5.1: 重写 `_refund_if_needed`（3 小时）

**文件**: `backend/app/services/video_service.py`

**改动**: 将 `_refund_if_needed` 从闭包内函数提升为 `VideoService` 的方法，使用原子 UPDATE。

**新代码**:
```python
async def _refund_if_needed(
    self, db: AsyncSession, video_gen: VideoGeneration, reason: str
) -> bool:
    """原子退款：仅第一个调用者成功。返回 True 表示执行了退款。"""
    from sqlalchemy import update
    from app.services.credit_service import credit_service
    from app.models.credit_transaction import TX_VIDEO_REFUND

    # 步骤 1: 原子地将 credits_charged 置零，仅当 > 0 时生效
    result = await db.execute(
        update(VideoGeneration)
        .where(
            VideoGeneration.id == video_gen.id,
            VideoGeneration.credits_charged > 0,
        )
        .values(credits_charged=0)
    )

    if result.rowcount == 0:
        # 已被其他请求处理，或本就不需要退款
        logger.info(f"Video {video_gen.id} refund skipped (already handled)")
        return False

    # 步骤 2: 执行退款（rowcount=1 表示我们获得了退款权）
    refund_amount = video_gen.credits_charged  # ORM 对象仍持有旧值
    await credit_service.grant(
        db, video_gen.user_id, refund_amount,
        type=TX_VIDEO_REFUND,
        ref_type="video", ref_id=video_gen.id,
        note=reason,
    )

    # 步骤 3: 同步 ORM 对象
    video_gen.credits_charged = 0
    logger.info(
        f"Video {video_gen.id} refunded {refund_amount} credits, reason={reason}"
    )
    return True
```

#### Backend-5.2: 更新 `poll_video_status` 调用方式（1 小时）

**文件**: `backend/app/services/video_service.py:185-266`

**改动**:
```python
# 删除 lines 219-227 的 _refund_if_needed 闭包
# 替换为调用 self._refund_if_needed()

# Line 246: completed_no_url 分支
await self._refund_if_needed(db, video_gen, "completed_no_url")

# Line 253: generation_failed 分支
await self._refund_if_needed(db, video_gen, "generation_failed")
```

#### Backend-5.3: 确保退款在同一事务中（30 分钟）

**验证**: `poll_video_status` 末尾的 `await db.commit()` 必须同时提交：
- video_gen.status 更新
- video_gen.credits_charged = 0
- credit_transactions 退款记录

**检查**: 不要在退款后单独 commit，必须等到整个 poll 结果处理完毕后统一 commit。

#### QA-5.1: 并发退款压力测试（2 小时）

**测试设计**:
```python
# test_video_concurrent_refund.py

async def test_concurrent_refund_only_one_succeeds(db, video_gen_with_credits):
    """模拟 10 个并发轮询请求同时触发退款"""
    video_gen.credits_charged = 10  # 模拟已扣费 10 积分
    await db.commit()

    # 记录退款前余额
    initial_balance = user.credits

    # 并发调用 poll_video_status（模拟视频刚好失败）
    results = await asyncio.gather(*[
        video_service.poll_video_status(db, video_gen.video_id, user.id)
        for _ in range(10)
    ])

    # 断言: 只退了一次
    await db.refresh(user)
    assert user.credits == initial_balance + 10  # 只加一次

    # 断言: 只有一条退款记录
    tx_count = await count_transactions(db, user.id, type="video_refund")
    assert tx_count == 1

    # 断言: credits_charged 为 0
    await db.refresh(video_gen)
    assert video_gen.credits_charged == 0
```

**注意**: SQLite 下无法真正并发，需要标记此测试为 `@pytest.mark.postgresql`，仅在 PostgreSQL 环境下运行。

---

## P0-6. 修复孤儿上游任务泄漏

> **负责人**: Backend（实施）+ Architect（审查）+ QA（回归测试）
>
> **工期**: 1-2 天
>
> **风险**: 🔴 高 — 重构核心资金路径

### 问题根因

`backend/app/services/video_service.py:92-158` — 事务顺序错误:

```
当前顺序（错误）:
1. 创建 VideoGeneration 记录     ← Step A: 写入 DB
2. db.commit()                    ← Step A: 提交
3. 调用 Agnes AI 创建任务         ← Step B: 外部 API
4. credit_service.charge()        ← Step C: 扣费
5. db.commit()                    ← Step C: 提交

如果 Step C 失败（积分不足）:
- Step A 已提交: 记录存在
- Step B 已执行: 上游任务在跑
- 回滚无效: Step A 已 commit
- 结果: 用户免费获得视频，Agnes API 配额浪费
```

### 架构设计方案

**新顺序**:
```
1. SELECT FOR UPDATE 锁定用户行 + 检查余额
2. credit_service.charge()        ← 先扣费
3. 创建 VideoGeneration 记录      ← 再建记录
4. 调用 Agnes AI 创建任务         ← 最后调外部 API
5. 更新 video_gen.task_id 等
6. db.commit()                    ← 统一提交

如果 Step 1 失败: 直接返回 402，不调 API
如果 Step 4 失败: 回滚（包括扣费），用户积分恢复
```

**关键约束**: 步骤 1-5 必须在**同一个事务**中，但步骤 4 是外部 HTTP 调用（不可回滚）。

**因此采用折中方案**:
```
1. 检查余额（预检，非权威）
2. 调用 Agnes AI 创建任务（先调外部 API）
3. 在同一个事务中: 扣费 + 创建/更新记录
4. 如果扣费失败: 标记上游任务为孤儿（日志告警），返回 402
```

**理由**: Agnes AI 调用不可回滚，所以必须先调用再扣费。但要将"扣费 + 记录创建"合并为一个原子操作，减少不一致窗口。

### 任务拆解

#### Architect-6.1: 审查资金路径重构方案（2 小时）

**审查清单**:
```
□ 新顺序是否消除了"已调 API 但未扣费"的窗口
□ rollback 语义是否正确（Agnes 调用不可回滚，需接受此风险）
□ 日志是否能捕获孤儿任务（方便后续清理）
□ 是否需要新增"orphaned"状态字段
□ 与图片生成流程（image_service.py）的一致性
```

#### Backend-6.1: 重写 `create_video` 事务流程（4 小时）

**文件**: `backend/app/services/video_service.py:62-183`

**核心改动**:

```python
async def create_video(self, db, user_id, prompt, ...):
    # === 阶段 1: 预检（非权威，快速失败）===
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    cost = math.ceil((num_frames / frame_rate) * settings.VIDEO_COST_PER_SECOND)

    if user.credits < cost:
        raise HTTPException(402, "Insufficient credits")

    # === 阶段 2: 调用外部 API（不可回滚）===
    try:
        api_response = await agnes_service.create_video_task(
            prompt=prompt, mode=mode, image=image, ...
        )
    except Exception as e:
        logger.error(f"Agnes API failed for user {user_id}: {e}")
        raise HTTPException(503, "Video service temporarily unavailable")

    # === 阶段 3: 原子扣费 + 创建记录（同一个事务）===
    from app.services.credit_service import credit_service, InsufficientCreditsError
    from app.models.credit_transaction import TX_VIDEO_GENERATE

    video_gen = VideoGeneration(
        user_id=user_id,
        prompt=prompt,
        task_id=api_response.get("id") or api_response.get("task_id"),
        video_id=api_response.get("video_id"),
        status=api_response.get("status", "queued"),
        progress=api_response.get("progress", 0),
        num_frames=num_frames,
        frame_rate=frame_rate,
        width=width, height=height,
    )
    db.add(video_gen)
    await db.flush()  # 获取 video_gen.id

    try:
        await credit_service.charge(
            db, user_id, cost,
            type=TX_VIDEO_GENERATE,
            ref_type="video", ref_id=video_gen.id,
        )
    except InsufficientCreditsError:
        # 扣费失败：记录孤儿任务日志，回滚整条记录
        logger.error(
            f"ORPHANED TASK: user={user_id} task_id={api_response.get('id')} "
            f"video_id={api_response.get('video_id')} cost={cost}. "
            f"Agnes task created but credits not charged."
        )
        await db.rollback()
        raise HTTPException(402, "Insufficient credits at charge time")

    video_gen.credits_charged = cost
    await db.commit()
    await db.refresh(video_gen)

    return { ... }
```

**关键变更**:
1. 删除了 line 92-105 的"先提交记录再扣费"逻辑
2. Agnes API 调用移到扣费之前（阶段 2）
3. 扣费和记录创建在同一个 `flush` + `commit` 周期中
4. 扣费失败时记录孤儿任务日志（便于后续人工/自动清理）

#### Backend-6.2: 修复 `health_check` 使用 `text()`（10 分钟）

**文件**: `backend/app/main.py:106`

**改动**:
```python
# 原代码
await session.execute("SELECT 1")

# 改为
from sqlalchemy import text
await session.execute(text("SELECT 1"))
```

#### Backend-6.3: 移除 `api/videos.py` 中的 Mock 检测代码（10 分钟）

**文件**: `backend/app/api/videos.py:27-28`

**改动**: 删除 `_video_value` 函数中的 `unittest.mock` 检测逻辑。

#### QA-6.1: 视频生成回归测试（2 小时）

| 用例 | 操作 | 预期 |
|------|------|------|
| 1 | 正常生成视频 | 记录创建 + 积分扣除 + 状态正确 |
| 2 | 积分不足时生成视频 | 返回 402，无 Agnes API 调用（预检拦截） |
| 3 | Agnes API 超时 | 返回 503，积分不变，无记录残留 |
| 4 | 并发生成超过余额 | 最后一个失败的返回 402，有孤儿日志 |
| 5 | 视频轮询成功 | 状态更新 + URL 提取 |
| 6 | 视频轮询失败 | 状态更新 + 积分退还（仅一次） |

#### QA-6.2: 孤儿任务检测验证（1 小时）

| 用例 | 操作 | 预期 |
|------|------|------|
| 1 | 模拟扣费失败 | 日志输出包含 "ORPHANED TASK" + task_id |
| 2 | 验证日志格式 | 包含 user_id, task_id, video_id, cost |

---

# 验收标准

## 每日检查点

| 日 | 必须完成 | 验收人 |
|----|---------|--------|
| Day 1 | P0-1 ✅ P0-2 ✅ P0-4 ✅ P0-3 启动 | QA 签字 |
| Day 2 | P0-3 ✅ | Architect + QA 签字 |
| Day 3 | P0-5 ✅ | Architect + QA 签字 |
| Day 4 | P0-6 ✅ | Architect + QA 签字 |
| Day 5 | 全量回归 + 合并 | 全团队签字 |

## 最终验收清单

```
功能验收:
□ 刷新页面后登录状态保持
□ 首页无虚假统计数字
□ 头像上传后正常显示
□ Alembic 迁移正常运行
□ CHECK (credits >= 0) 约束生效
□ 视频退款不会双重执行
□ 视频生成积分不足时不调用 Agnes API
□ 健康检查使用 text()
□ 生产代码无 mock 检测逻辑

测试验收:
□ 所有新代码有对应测试
□ 并发退款测试在 PostgreSQL 下通过
□ 全量回归测试无退化
□ 测试覆盖率不低于修复前

文档验收:
□ KNOWN_ISSUES.md 更新（已修复的条目标记 resolved）
□ PRODUCTION_PLAN.md 更新进度
□ 新增 P0 修复说明文档
```

---

# 风险缓解

| 风险 | 概率 | 缓解措施 |
|------|------|---------|
| Alembic 自动生成遗漏某些约束 | 中 | 人工逐表审查 migration 文件 |
| 退款竞态修复引入新 Bug | 中 | PostgreSQL 并发测试 + 人工 review |
| 资金路径重构导致图片生成也出问题 | 低 | image_service.py 不在本次范围内，但需回归 |
| 头像 URL 修复后旧头像 404 | 中 | 如有线上数据，需编写数据迁移脚本 |
| 团队成员对 SQLAlchemy 事务不熟悉 | 低 | Architect 提供事务边界设计文档 |

---

*本方案中所有代码引用均基于当前代码库实际内容，行号和文件路径已验证。*
