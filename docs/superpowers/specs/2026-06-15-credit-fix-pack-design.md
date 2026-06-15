# 资损与越权急修包 Design

**Date:** 2026-06-15
**Scope:** Agnes Studio 后端
**Trigger:** 阶段二/三审计发现的 5 处资损/越权风险

## 背景

代码审计在 `image_service` / `video_service` 中发现以下问题，均会直接造成资损或越权：

1. **图像生成失败仍扣积分** —— `image_service.generate()` 在调用上游前就执行 `user.credits -= IMAGE_COST`，即使上游返回失败、image_url 为空，积分依然被扣。
2. **视频生成完全免费** —— `video_service.create_video()` 不调用任何扣费逻辑，`VIDEO_COST_PER_SECOND` 配置项形同虚设。
3. **并发超扣** —— `User.credits` 的 `SELECT → 计算 → UPDATE` 没有行锁；同一用户的多个并发请求可越过余额检查。
4. **视频轮询越权** —— `video_service.poll_video_status(db, agnes_video_id, user_id)` 接受 `user_id` 但不使用；只要拿到 Agnes 平台的 `video_id`，任何登录用户都能 poll 任意他人任务的状态。
5. **video_url 字段映射 bug** —— 完成时 `video_gen.video_url = api_response.get("remixed_from_video_id")`，把上游的"被 remix 的源视频 id"误存入 URL 列。

## 目标

- 修复以上 5 项，逐项可独立验证、可独立回滚。
- 引入 **CreditTransaction（积分流水）** 表与 **CreditService** 作为后续退款、对账、运营调整的基础设施。
- 不引入新的运行时依赖（不上 Redis / Celery / Stripe）。

## 非目标

- 视频生成失败的自动退款机制（§3 上线后才具备能力，本急修包仅记录已知限制）。
- API Key 鉴权路径中的限流落地（B 包负责）。
- 充值真实支付通道（C 包负责）。

## 实施分解

按依赖顺序划分为 4 个阶段；每阶段一条 commit，可独立验证。

### 阶段 1：图像失败不扣积分

**修改文件**：`backend/app/services/image_service.py`

- 余额检查继续在调用上游之前。
- `user.credits -= settings.IMAGE_COST` 移到 **上游成功且返回非空 image_url** 之后。
- `status = "failed"` 分支上不修改 credits。
- 单元测试：模拟上游 raise / 返回空 url / 返回正常 url 三种情况，断言 `user.credits` 变化正确。

**验收**：
- 现有 happy-path 测试通过。
- 新增 `test_image_generate_upstream_failure_does_not_charge` 通过。

### 阶段 2：视频积分扣减（无退款）

**修改文件**：
- `backend/app/models/video.py` —— 新增 `credits_charged: Integer = 0`。
- `backend/app/services/video_service.py` —— `create_video()` 中按 `ceil(num_frames / frame_rate * VIDEO_COST_PER_SECOND)` 预扣。
- `backend/app/api/videos.py` —— 余额不足返回 402。
- `backend/app/schemas/video.py` —— `VideoGenerateResponse` 增加 `credits_charged: int` 字段。

**扣费时机**：上游 `create_video_task` 成功返回后；上游失败不扣分。

**已知限制**（写入 commit message + `docs/KNOWN_ISSUES.md`）：
> 视频任务在上游成功创建后、生成阶段失败（poll → status=failed）时，本阶段不退还积分。退款能力随阶段 3 ledger 上线后通过补偿脚本补做。

**数据迁移**：已有 `video_generations` 行 `credits_charged` 默认 0，无需回填。

**验收**：
- 视频生成 happy-path：`user.credits` 减少 = 预期值；响应中 `credits_charged` 正确。
- 余额不足：返回 402，未创建 `VideoGeneration` 记录，无上游调用。
- 上游失败：`user.credits` 不变。

### 阶段 3：积分 ledger + 行锁

#### 3.1 数据模型

新增 `backend/app/models/credit_transaction.py`：

```python
class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    amount        = Column(Integer, nullable=False)        # +入账, -扣费
    balance_after = Column(Integer, nullable=False)        # 此次操作后余额快照
    type          = Column(String(32), nullable=False, index=True)
    ref_type      = Column(String(32), nullable=True)
    ref_id        = Column(Integer, nullable=True)
    note          = Column(String(255), nullable=True)
    created_at    = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           index=True)
```

`type` 枚举：`image_generate` / `video_generate` / `video_refund` / `topup` /
`register_bonus` / `referral_bonus` / `admin_adjust` / `migration_initial`。

#### 3.2 服务层

新增 `backend/app/services/credit_service.py`：

```python
class InsufficientCreditsError(Exception): ...

class CreditService:
    async def charge(self, db, user_id, amount, type, ref_type=None,
                     ref_id=None, note=None) -> CreditTransaction:
        """扣费：amount 传正数。在事务内使用 with_for_update() 锁定 users 行，
        余额不足抛 InsufficientCreditsError，否则原子更新 credits 并写入流水。
        不 commit —— 由调用方控制事务边界。"""

    async def grant(self, db, user_id, amount, type, ...) -> CreditTransaction:
        """入账：充值/奖励/退款。同样不 commit。"""

    async def get_user_transactions(self, db, user_id, page, per_page) \
            -> tuple[list[CreditTransaction], int]:
        """分页查询用户流水。"""
```

**实现要点**：
- 使用 SQLAlchemy `select(User).where(User.id == uid).with_for_update()`。
  - PostgreSQL：`FOR UPDATE`，正确防并发。
  - SQLite (aiosqlite)：`with_for_update()` 在 sqlite 方言下是 no-op；为防并发超扣，事务开启时使用 `BEGIN IMMEDIATE`（通过 `connection.execute(text("BEGIN IMMEDIATE"))`）。生产环境推荐迁移 PG。
- `balance_after` 在同一事务里读 `user.credits` 的更新后值（先 `await db.flush()` 再读）。
- 服务方法 **不 commit**；由 API/外层服务统一 commit，保证业务记录与流水原子写入。

#### 3.3 改造调用点

| 位置 | 调用 |
|---|---|
| `image_service.generate()` 成功分支 | `credit_service.charge(db, user_id, IMAGE_COST, type='image_generate', ref_type='image', ref_id=image.id)` |
| `video_service.create_video()` 成功分支 | `credit_service.charge(db, user_id, cost, type='video_generate', ref_type='video', ref_id=video.id)` |
| `auth_service.register()` | `credit_service.grant(db, new_user.id, FREE_CREDITS_ON_REGISTER, type='register_bonus')` |
| `auth_service.register()` 推荐人奖励 | `credit_service.grant(db, referrer.id, REFERRAL_BONUS, type='referral_bonus', ref_type='user', ref_id=new_user.id)` |
| `video_service.poll_video_status()` failed 分支 | 见阶段 4.3 |

注册赠送 / 推荐奖励原本直接 `user.credits = ...`，统一改走 ledger，保证 `users.credits` 等于 sum(amount)。

#### 3.4 数据回填脚本

`backend/scripts/backfill_credit_ledger.py`：
- 查询所有 `users`。
- 对每个用户：若该用户在 `credit_transactions` 表中尚无记录，插入一条 `type='migration_initial'`，`amount = balance_after = user.credits`，`note = 'initial backfill'`。
- 幂等：脚本可重复运行。

#### 3.5 视频失败退款（补做阶段 2 的尾巴）

在 `video_service.poll_video_status()` 拿到上游 `failed` 状态时：
```python
if video_gen.credits_charged > 0 and video_gen.status != "failed":
    await credit_service.grant(
        db, video_gen.user_id, video_gen.credits_charged,
        type='video_refund', ref_type='video', ref_id=video_gen.id,
        note='generation_failed',
    )
    video_gen.credits_charged = 0   # 防重入
video_gen.status = "failed"
video_gen.error_message = ...
await db.commit()
```

#### 3.6 用户流水 API

`backend/app/api/users.py` 新增：
```python
@router.get("/credits/transactions", response_model=CreditTransactionListResponse)
async def list_credit_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await credit_service.get_user_transactions(
        db, current_user.id, page, per_page
    )
    return {"items": items, "total": total, "page": page, "per_page": per_page}
```

新增 schemas：`CreditTransactionResponse`、`CreditTransactionListResponse`。

#### 3.7 测试

- 并发测试：`asyncio.gather` 起 N 个并发 charge，断言：
  - 总扣分 ≤ 初始余额。
  - 余额永不为负。
  - 流水记录数 == 成功 charge 次数。
- 退款幂等：对同一 video 调两次 grant + 防重入逻辑，第二次应跳过。
- 流水查询分页正确。
- 回填脚本幂等：跑两次，记录数不变。

**验收**：
- 现有所有测试通过。
- 新增并发/退款/查询测试通过。
- 回填脚本在本地 SQLite 可执行成功。

### 阶段 4：视频越权 + URL bug

#### 4.1 越权修复

`backend/app/services/video_service.py` 中 `poll_video_status` 入口加：

```python
result = await db.execute(
    select(VideoGeneration).where(
        VideoGeneration.video_id == agnes_video_id,
        VideoGeneration.user_id == user_id,
    )
)
video_gen = result.scalar_one_or_none()
if not video_gen:
    raise HTTPException(status_code=404, detail="Video not found")
```

API 层（`api/videos.py`）已按 `(id, user_id)` 查过一次，但 service 自身不应假设调用方做过权限校验，双层保险。

#### 4.2 URL 抽取纯函数

新增 `backend/app/services/video_service.py` 模块级函数：

```python
def _extract_video_url(payload: dict) -> Optional[str]:
    """按 fallback 顺序从上游响应中提取 video URL。"""
    def _is_url(v): return isinstance(v, str) and v.startswith(("http://", "https://"))

    for key in ("video_url", "url", "download_url", "output_url"):
        v = payload.get(key)
        if _is_url(v): return v

    output = payload.get("output")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            for key in ("video_url", "url", "download_url"):
                v = first.get(key)
                if _is_url(v): return v
        elif _is_url(first):
            return first
    if isinstance(output, dict):
        for key in ("video_url", "url", "download_url"):
            v = output.get(key)
            if _is_url(v): return v

    data = payload.get("data")
    if isinstance(data, dict):
        return _extract_video_url(data)
    return None
```

#### 4.3 完成处理

```python
if status == "completed":
    url = _extract_video_url(api_response)
    if url:
        video_gen.video_url = url
        video_gen.status = "completed"
    else:
        logger.error(
            f"Video {video_gen.id} marked completed but URL missing. "
            f"Response: {str(api_response)[:500]}"
        )
        video_gen.status = "failed"
        video_gen.error_message = "Upstream completed but no video URL"
        # 触发退款（依赖阶段 3 已上线）
        if video_gen.credits_charged > 0:
            await credit_service.grant(
                db, video_gen.user_id, video_gen.credits_charged,
                type='video_refund', ref_type='video', ref_id=video_gen.id,
                note='completed_no_url',
            )
            video_gen.credits_charged = 0
```

#### 4.4 测试

- `_extract_video_url` 表驱动单测：覆盖顶层 video_url / output 列表 / output 对象 / data 嵌套 / 非 http 字段 / 空 dict。
- 越权测试：用户 A 创建视频 → 用户 B 用 A 的 `agnes_video_id` poll → 期望 404。

**验收**：
- 单测全部通过。
- 越权用例返回 404。

## 数据迁移与上线顺序

```
阶段 1 (image 失败不扣)  ── 单 commit ── 部署
        ↓
阶段 2 (video 预扣)      ── 单 commit + alembic 迁移（credits_charged 列） ── 部署
        ↓
阶段 3 (ledger + 行锁)   ── 单 commit + alembic 迁移 + 回填脚本 ── 部署
                          上线后立刻跑回填脚本
        ↓
阶段 4 (越权 + URL)      ── 单 commit ── 部署
```

每阶段独立验证；阶段 3 部署后必须立即执行回填脚本，否则历史用户的"账面余额"与"流水累计"对不上。

## 风险与回滚

| 阶段 | 风险 | 回滚 |
|---|---|---|
| 1 | 极低（单文件、纯逻辑顺序调整） | 直接 revert commit |
| 2 | 低（新增列默认值兼容旧行） | revert commit + alembic downgrade |
| 3 | 中（核心扣费路径重构 + 新表） | revert commit + alembic downgrade；ledger 表保留无害 |
| 4 | 低（局部修复） | revert commit |

## 验证清单

- [ ] 阶段 1：上游失败不扣分（单测 + 手动）
- [ ] 阶段 2：视频生成扣分正确，余额不足 402
- [ ] 阶段 3：并发 charge 不超扣；流水累计 == users.credits；回填脚本幂等
- [ ] 阶段 4：他人 video_id poll 返回 404；URL fallback 单测全过
- [ ] 全量回归：原有 `tests/test_auth.py` `tests/test_generation.py` 不退化

## 参考

- PRODUCTION_PLAN.md 阶段一/二
- memory/agnes-studio-production-status.md
- 审计依据：本次会话内对 `image_service` / `video_service` / `auth_service` / `api_key_service` 的全面 read-through
