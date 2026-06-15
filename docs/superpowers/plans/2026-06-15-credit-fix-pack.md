# 资损与越权急修包 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 5 处资损 / 越权 bug：图像失败仍扣分、视频不扣分、并发超扣、视频轮询越权、video_url 字段映射 bug。

**Architecture:** 4 个独立可回滚阶段。新增 `CreditTransaction` 模型 + `CreditService` 作为统一扣费/退款入口；用 `with_for_update()` 加行锁防并发；URL 抽取改为可单测的纯函数；轮询补充 user_id 校验。

**Tech Stack:** FastAPI 0.115 / SQLAlchemy 2.0 / Pydantic v2 / aiosqlite / pytest-asyncio。无新增运行时依赖。

**Spec:** [`docs/superpowers/specs/2026-06-15-credit-fix-pack-design.md`](../specs/2026-06-15-credit-fix-pack-design.md)

---

## File Structure

每个阶段对应的文件清单（已存在 = M = modify，新建 = C = create）：

| 阶段 | 文件 | 改动类型 | 职责 |
|---|---|---|---|
| 1 | `backend/app/services/image_service.py` | M | 调整扣费时机 |
| 1 | `backend/tests/test_image_service.py` | C | 图像失败不扣分单测 |
| 2 | `backend/app/models/video.py` | M | 加 `credits_charged` 列 |
| 2 | `backend/app/services/video_service.py` | M | `create_video` 预扣积分 |
| 2 | `backend/app/schemas/video.py` | M | 响应中暴露 `credits_charged` |
| 2 | `backend/tests/test_video_charge.py` | C | 视频扣分单测 |
| 2 | `docs/KNOWN_ISSUES.md` | C | 记录已知限制 |
| 3 | `backend/app/models/credit_transaction.py` | C | CreditTransaction 模型 |
| 3 | `backend/app/models/__init__.py` | M | 导出 CreditTransaction |
| 3 | `backend/app/models/database.py` | M | 注册新模型到 metadata |
| 3 | `backend/app/services/credit_service.py` | C | charge/grant/查询，行锁 |
| 3 | `backend/app/services/image_service.py` | M | 改走 credit_service |
| 3 | `backend/app/services/video_service.py` | M | 改走 credit_service |
| 3 | `backend/app/services/auth_service.py` | M | 注册赠送/推荐奖励改走 grant |
| 3 | `backend/app/schemas/credit.py` | C | 流水响应 schema |
| 3 | `backend/app/api/users.py` | M | 加流水查询端点 |
| 3 | `backend/scripts/__init__.py` | C | 空文件 |
| 3 | `backend/scripts/backfill_credit_ledger.py` | C | 历史用户回填 |
| 3 | `backend/tests/test_credit_service.py` | C | 行锁/并发/退款幂等 |
| 3 | `backend/tests/test_credit_api.py` | C | 流水端点测试 |
| 4 | `backend/app/services/video_service.py` | M | 越权校验 + URL 抽取 |
| 4 | `backend/tests/test_video_service.py` | C | URL 抽取 + 越权单测 |

---

## Conventions

- 工作目录始终是仓库根 `/Users/yuhuibin/code/tool/agnes-studio`。
- 所有 `pytest` 命令都从 `backend/` 子目录执行：`cd backend && pytest ...`。
- 所有 commit 在 `feat/credit-fix-pack` 分支上。每个 step 5 后立即 commit，commit message 末尾追加：
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```
- 测试文件统一放 `backend/tests/`，遵循现有命名 `test_*.py`。
- 时间戳一律 `datetime.now(timezone.utc)`，禁用 `datetime.utcnow()`。

---

## Stage 1: 图像失败不扣积分

### Task 1.1: 写测试 — 上游失败不扣分

**Files:**
- Create: `backend/tests/test_image_service.py`

- [ ] **Step 1: Write the failing tests**

写入 `backend/tests/test_image_service.py`：

```python
"""Tests for image_service credit charging behavior."""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.models.user import User
from app.services.image_service import image_service


@pytest.mark.asyncio
async def test_image_generate_success_charges_credits(db, monkeypatch):
    """Happy path: upstream returns valid url, credits decrement by IMAGE_COST."""
    user = User(
        email="img-ok@example.com",
        username="imgok",
        hashed_password="x",
        credits=10,
        referral_code="REFOK01",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake_generate_image(**kwargs):
        return {"image_url": "https://example.com/ok.png"}

    monkeypatch.setattr(
        "app.services.image_service.agnes_service.generate_image",
        fake_generate_image,
    )

    image = await image_service.generate(db, user.id, {
        "prompt": "p", "model": "agnes-image-2.1-flash",
        "size": "1024x768", "style": "none",
    })

    assert image.status == "completed"
    assert image.image_url == "https://example.com/ok.png"

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 9  # IMAGE_COST = 1


@pytest.mark.asyncio
async def test_image_generate_upstream_raises_does_not_charge(db, monkeypatch):
    """Upstream raises -> credits unchanged, no DB row created."""
    user = User(
        email="img-raise@example.com",
        username="imgraise",
        hashed_password="x",
        credits=10,
        referral_code="REFRAISE",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake_generate_image(**kwargs):
        raise RuntimeError("upstream down")

    monkeypatch.setattr(
        "app.services.image_service.agnes_service.generate_image",
        fake_generate_image,
    )

    with pytest.raises(Exception):
        await image_service.generate(db, user.id, {
            "prompt": "p", "model": "agnes-image-2.1-flash",
            "size": "1024x768", "style": "none",
        })

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 10  # unchanged


@pytest.mark.asyncio
async def test_image_generate_empty_url_does_not_charge(db, monkeypatch):
    """Upstream returns empty url -> status=failed, credits unchanged."""
    user = User(
        email="img-empty@example.com",
        username="imgempty",
        hashed_password="x",
        credits=10,
        referral_code="REFEMPTY",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake_generate_image(**kwargs):
        return {"image_url": ""}

    monkeypatch.setattr(
        "app.services.image_service.agnes_service.generate_image",
        fake_generate_image,
    )

    image = await image_service.generate(db, user.id, {
        "prompt": "p", "model": "agnes-image-2.1-flash",
        "size": "1024x768", "style": "none",
    })

    assert image.status == "failed"
    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 10  # not charged
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_image_service.py -v
```

Expected: `test_image_generate_upstream_raises_does_not_charge` and `test_image_generate_empty_url_does_not_charge` FAIL (current code charges unconditionally). The success test may pass.

- [ ] **Step 3: Implement minimal fix**

Modify `backend/app/services/image_service.py`. Replace the existing `generate` method body with:

```python
    async def generate(self, db: AsyncSession, user_id: int, data: Dict) -> ImageGeneration:
        # Check credits
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.credits < settings.IMAGE_COST:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits. Please recharge."
            )

        # Call Agnes AI (do NOT charge yet)
        try:
            agnes_response = await agnes_service.generate_image(
                prompt=data["prompt"],
                model=data.get("model", "agnes-image-2.1-flash"),
                size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
                negative_prompt=data.get("negative_prompt", ""),
                style=data.get("style", "none"),
            )
        except Exception as e:
            logger.error(f"Image generation service error for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image generation service is temporarily unavailable. Please try again later."
            )

        image_url = agnes_response.get("image_url", "")
        succeeded = bool(image_url)

        image_gen = ImageGeneration(
            user_id=user_id,
            prompt=data["prompt"],
            negative_prompt=data.get("negative_prompt", ""),
            model=data.get("model", "agnes-image-2.1-flash"),
            size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
            style=data.get("style", "none"),
            image_url=image_url,
            status="completed" if succeeded else "failed",
            parameters=data,
        )
        if not succeeded:
            image_gen.error_message = "Image generation returned no result"

        db.add(image_gen)

        # Only charge on success
        if succeeded:
            user.credits -= settings.IMAGE_COST

        await db.commit()
        await db.refresh(image_gen)
        logger.info(
            f"Image {image_gen.id} generated for user {user_id}, "
            f"status={image_gen.status}, credits remaining: {user.credits}"
        )
        return image_gen
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && pytest tests/test_image_service.py -v
```

Expected: 3 passed. Then run full suite to ensure no regression:

```bash
cd backend && pytest -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/image_service.py backend/tests/test_image_service.py
git commit -m "fix(image): 仅在生成成功时扣减积分

- 上游异常：积分不变，向上抛 503
- 上游返回空 url：记录 status=failed，积分不变
- 上游返回有效 url：保存 status=completed 并扣 IMAGE_COST

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Stage 2: 视频积分扣减（无退款）

### Task 2.1: 给 VideoGeneration 加 credits_charged 列

**Files:**
- Modify: `backend/app/models/video.py`

- [ ] **Step 1: Add the column**

Edit `backend/app/models/video.py`. After line 33 (the `expires_at` line) and before the `# Metadata` comment, add:

```python
    credits_charged = Column(Integer, default=0, nullable=False)
```

完整插入位置示意（diff 上下文）：

```python
    error_message = Column(Text, default=None)
    expires_at = Column(SqlAlchemyDateTime(timezone=True), default=None)
    credits_charged = Column(Integer, default=0, nullable=False)  # ← 新增

    # Metadata
    parameters = Column(JSON, default=dict)
```

注：项目用 `Base.metadata.create_all`，**对已存在的表新增列不会自动迁移**。本地 SQLite 测试库每次重建无影响；生产 SQLite/PG 需手工 ALTER。把 ALTER SQL 写入 `docs/KNOWN_ISSUES.md`（Task 2.4 处理）。

- [ ] **Step 2: Run regression**

```bash
cd backend && pytest -v
```

Expected: all existing tests still pass (column has default=0, won't break inserts).

- [ ] **Step 3: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/models/video.py
git commit -m "feat(video): 添加 credits_charged 列记录视频扣分

为后续退款 / ledger 回填做准备。default=0 兼容历史行。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 2.2: 写测试 — 视频生成扣分

**Files:**
- Create: `backend/tests/test_video_charge.py`

- [ ] **Step 1: Write failing tests**

写入 `backend/tests/test_video_charge.py`：

```python
"""Tests for video_service credit charging behavior."""
import pytest
from sqlalchemy import select
from fastapi import HTTPException

from app.models.user import User
from app.services.video_service import video_service
from app.core.config import settings


@pytest.mark.asyncio
async def test_video_create_charges_credits_on_upstream_success(db, monkeypatch):
    """Happy path: upstream returns task -> credits decrement, credits_charged set."""
    user = User(
        email="vid-ok@example.com",
        username="vidok",
        hashed_password="x",
        credits=100,
        referral_code="REFVIDOK",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake_create_task(**kwargs):
        return {
            "id": "task-1", "task_id": "task-1",
            "video_id": "vid-1", "status": "queued", "progress": 0,
        }

    monkeypatch.setattr(
        "app.services.video_service.agnes_service.create_video_task",
        fake_create_task,
    )

    result = await video_service.create_video(
        db=db, user_id=user.id, prompt="p",
        num_frames=121, frame_rate=24,
    )

    # 121 / 24 = 5.04s -> ceil = 6 -> 6 * VIDEO_COST_PER_SECOND
    expected_cost = 6 * settings.VIDEO_COST_PER_SECOND
    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 100 - expected_cost
    assert result["credits_charged"] == expected_cost


@pytest.mark.asyncio
async def test_video_create_insufficient_credits_returns_402(db, monkeypatch):
    """Balance < cost -> HTTPException 402, no upstream call."""
    user = User(
        email="vid-poor@example.com",
        username="vidpoor",
        hashed_password="x",
        credits=1,  # very low
        referral_code="REFPOOR",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    called = {"count": 0}

    async def fake_create_task(**kwargs):
        called["count"] += 1
        return {}

    monkeypatch.setattr(
        "app.services.video_service.agnes_service.create_video_task",
        fake_create_task,
    )

    with pytest.raises(HTTPException) as exc:
        await video_service.create_video(
            db=db, user_id=user.id, prompt="p",
            num_frames=121, frame_rate=24,
        )
    assert exc.value.status_code == 402
    assert called["count"] == 0

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 1


@pytest.mark.asyncio
async def test_video_create_upstream_failure_does_not_charge(db, monkeypatch):
    """Upstream raises -> credits unchanged."""
    user = User(
        email="vid-fail@example.com",
        username="vidfail",
        hashed_password="x",
        credits=100,
        referral_code="REFVFAIL",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake_create_task(**kwargs):
        raise RuntimeError("upstream down")

    monkeypatch.setattr(
        "app.services.video_service.agnes_service.create_video_task",
        fake_create_task,
    )

    with pytest.raises(Exception):
        await video_service.create_video(
            db=db, user_id=user.id, prompt="p",
            num_frames=121, frame_rate=24,
        )

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 100  # unchanged
```

- [ ] **Step 2: Run tests to verify fail**

```bash
cd backend && pytest tests/test_video_charge.py -v
```

Expected: all 3 fail (current `create_video` does not charge).

### Task 2.3: 实现视频扣分

**Files:**
- Modify: `backend/app/services/video_service.py`
- Modify: `backend/app/schemas/video.py`

- [ ] **Step 1: Update schema response to expose credits_charged**

Edit `backend/app/schemas/video.py`. In `VideoGenerateResponse` (currently lines 46-62), add `credits_charged` field:

```python
class VideoGenerateResponse(BaseModel):
    id: int
    task_id: str
    video_id: str
    status: str
    progress: int
    prompt: str
    estimated_time: int = 300
    video_url: Optional[str] = None
    num_frames: Optional[int] = None
    frame_rate: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    credits_charged: int = 0  # ← 新增
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Update `videos.py` `_video_generate_response` helper**

Edit `backend/app/api/videos.py`. In the `_video_generate_response` function (the dict it returns), add the `credits_charged` key:

Locate this block:
```python
def _video_generate_response(video: Any) -> dict:
    return {
        "id": _video_value(video, "id"),
        ...
        "created_at": _video_value(video, "created_at"),
    }
```

Add `"credits_charged": _video_value(video, "credits_charged", 0),` before the `"created_at"` line:

```python
def _video_generate_response(video: Any) -> dict:
    return {
        "id": _video_value(video, "id"),
        "task_id": _video_value(video, "task_id"),
        "video_id": _video_value(video, "video_id"),
        "status": _video_value(video, "status"),
        "progress": _video_value(video, "progress", 0),
        "prompt": _video_value(video, "prompt"),
        "estimated_time": _video_value(video, "estimated_time", 300),
        "video_url": _video_value(video, "video_url"),
        "num_frames": _video_value(video, "num_frames"),
        "frame_rate": _video_value(video, "frame_rate"),
        "width": _video_value(video, "width"),
        "height": _video_value(video, "height"),
        "credits_charged": _video_value(video, "credits_charged", 0),
        "created_at": _video_value(video, "created_at"),
    }
```

- [ ] **Step 3: Implement charging logic in video_service**

Edit `backend/app/services/video_service.py`. Add at top of file (with other imports):

```python
import math
from fastapi import HTTPException, status as http_status
from app.models.user import User
from app.core.config import settings
```

Replace the `create_video` method body. Find the line `# Validate frame rate ... raise ValueError` and after the validation, before `# Create database record`, insert credit check:

```python
    async def create_video(self, db: AsyncSession, user_id: int,
                          prompt: str, num_frames: int = 121,
                          frame_rate: int = 24, mode: str = "ti2vid",
                          image: str = None, extra_images: list = None,
                          width: int = 1152, height: int = 768,
                          negative_prompt: str = None) -> Dict:
        # Validate frame count
        if num_frames not in VALID_FRAME_COUNTS:
            raise ValueError(f"Invalid num_frames: {num_frames}. Must be one of {VALID_FRAME_COUNTS}")

        # Validate frame rate
        if frame_rate not in VALID_FRAME_RATES:
            raise ValueError(f"Invalid frame_rate: {frame_rate}. Must be one of {VALID_FRAME_RATES}")

        # Calculate cost (ceil duration * per-second rate)
        duration = num_frames / frame_rate
        cost = math.ceil(duration * settings.VIDEO_COST_PER_SECOND)

        # Load user and check balance
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.credits < cost:
            raise HTTPException(
                status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits. Please recharge.",
            )

        # Create database record (queued)
        video_gen = VideoGeneration(
            user_id=user_id,
            prompt=prompt,
            num_frames=num_frames,
            frame_rate=frame_rate,
            width=width,
            height=height,
            status="queued",
            progress=0,
        )
        db.add(video_gen)
        await db.commit()
        await db.refresh(video_gen)

        # Prepare extra_body for multi-image/keyframes mode
        extra_body = {}
        if extra_images and len(extra_images) > 0:
            extra_body["image"] = extra_images
            if mode == "keyframes":
                extra_body["mode"] = "keyframes"

        # Call Agnes AI API to create video task
        try:
            api_response = await agnes_service.create_video_task(
                prompt=prompt,
                mode=mode,
                image=image,
                extra_body=extra_body if extra_body else None,
                num_frames=num_frames,
                frame_rate=frame_rate,
                height=height,
                width=width,
                negative_prompt=negative_prompt,
            )
        except Exception as e:
            video_gen.status = "failed"
            video_gen.error_message = "Video task creation failed"
            await db.commit()
            logger.error(f"Failed to create video task for user {user_id}: {e}")
            raise Exception("Failed to create video task. Please try again later.")

        # Upstream succeeded -> charge credits
        video_gen.task_id = api_response.get("id") or api_response.get("task_id")
        video_gen.video_id = api_response.get("video_id")
        video_gen.status = api_response.get("status", "queued")
        video_gen.progress = api_response.get("progress", 0)
        video_gen.credits_charged = cost
        user.credits -= cost
        await db.commit()
        await db.refresh(video_gen)

        logger.info(
            f"Video task created for user {user_id}, video_id={video_gen.video_id}, "
            f"charged {cost} credits, balance: {user.credits}"
        )

        return {
            "id": video_gen.id,
            "task_id": video_gen.task_id,
            "video_id": video_gen.video_id,
            "status": video_gen.status,
            "progress": video_gen.progress,
            "prompt": prompt,
            "estimated_time": 300,
            "video_url": video_gen.video_url,
            "num_frames": video_gen.num_frames,
            "frame_rate": video_gen.frame_rate,
            "width": video_gen.width,
            "height": video_gen.height,
            "credits_charged": video_gen.credits_charged,
            "created_at": video_gen.created_at,
        }
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && pytest tests/test_video_charge.py -v
cd backend && pytest -v
```

Expected: new tests pass; existing `test_generate_video` (which mocks the whole `create_video`) still passes.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/video_service.py backend/app/schemas/video.py backend/app/api/videos.py backend/tests/test_video_charge.py
git commit -m "feat(video): 视频生成预扣积分

- 创建任务前校验余额，不足返回 402
- 上游创建任务成功后按 ceil(duration * VIDEO_COST_PER_SECOND) 扣分
- 上游失败不扣分
- 响应中暴露 credits_charged 供前端展示

已知限制：上游成功后生成阶段失败不退款，待 ledger 阶段补做。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 2.4: 记录已知限制

**Files:**
- Create: `docs/KNOWN_ISSUES.md`

- [ ] **Step 1: Write the doc**

Create `docs/KNOWN_ISSUES.md`:

```markdown
# Known Issues

## 视频生成阶段失败不自动退款（截至 Stage 2）

**现象**：用户调用 `/api/videos/generate` 后，若 Agnes 上游已成功创建任务（已扣积分），
但后续 poll 拿到 `status=failed`，当前积分**不会自动退还**。

**临时缓解**：用户可联系运营手工调账。

**根治计划**：Stage 3（积分 ledger）上线后通过补偿脚本统一退款，并在 `poll_video_status`
看到 `status=failed` 时实时退款。

## 新增列后需手工 ALTER（生产 SQLite/PG）

`Base.metadata.create_all` 不会为已存在的表新增列。Stage 2 / Stage 3 引入新列时：

```sql
-- Stage 2
ALTER TABLE video_generations ADD COLUMN credits_charged INTEGER DEFAULT 0 NOT NULL;

-- Stage 3 创建新表（create_all 会自动建，无需手工）
```

测试用 SQLite in-memory，每次重建，不受影响。
```

- [ ] **Step 2: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add docs/KNOWN_ISSUES.md
git commit -m "docs: 记录已知限制（视频不自动退款 / ALTER TABLE 手工迁移）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Stage 3: 积分 ledger + 行锁

### Task 3.1: CreditTransaction 模型

**Files:**
- Create: `backend/app/models/credit_transaction.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/database.py`

- [ ] **Step 1: Create the model**

Write `backend/app/models/credit_transaction.py`:

```python
"""Credit Transaction (Ledger) Model."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime as SqlAlchemyDateTime,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# Allowed `type` values
TX_IMAGE_GENERATE = "image_generate"
TX_VIDEO_GENERATE = "video_generate"
TX_VIDEO_REFUND = "video_refund"
TX_TOPUP = "topup"
TX_REGISTER_BONUS = "register_bonus"
TX_REFERRAL_BONUS = "referral_bonus"
TX_ADMIN_ADJUST = "admin_adjust"
TX_MIGRATION_INITIAL = "migration_initial"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount = Column(Integer, nullable=False)         # +入账, -扣费
    balance_after = Column(Integer, nullable=False)  # 操作后余额快照
    type = Column(String(32), nullable=False, index=True)
    ref_type = Column(String(32), nullable=True)
    ref_id = Column(Integer, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(
        SqlAlchemyDateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user = relationship("User")

    def __repr__(self):
        return (
            f"<CreditTransaction(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, type={self.type})>"
        )
```

- [ ] **Step 2: Register in models package**

Edit `backend/app/models/__init__.py`. Currently 1 line; ensure it's empty or compatible — since `__init__.py` is currently empty per our reads, leave it empty (the model is registered via `models/database.py`).

- [ ] **Step 3: Register in database aggregator**

Edit `backend/app/models/database.py`. Replace contents with:

```python
"""Database Base & Models"""
from app.core.database import Base, engine
from app.models.user import User
from app.models.image import ImageGeneration
from app.models.video import VideoGeneration
from app.models.gallery import GalleryItem
from app.models.api_key import ApiKey
from app.models.credit_transaction import CreditTransaction

__all__ = [
    "Base", "engine",
    "User", "ImageGeneration", "VideoGeneration",
    "GalleryItem", "ApiKey", "CreditTransaction",
]
```

- [ ] **Step 4: Smoke test — table creates**

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected: existing tests pass (table now exists in test DB; nothing else changed).

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/models/credit_transaction.py backend/app/models/database.py
git commit -m "feat(credit): 新增 CreditTransaction ledger 模型

定义 type 常量；表结构：amount / balance_after / ref_type / ref_id / note。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 3.2: CreditService（charge / grant / 查询）

**Files:**
- Create: `backend/app/services/credit_service.py`
- Create: `backend/tests/test_credit_service.py`

- [ ] **Step 1: Write failing tests first (TDD)**

Write `backend/tests/test_credit_service.py`:

```python
"""Tests for CreditService: charge, grant, query, idempotency."""
import asyncio
import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.credit_transaction import (
    CreditTransaction, TX_IMAGE_GENERATE, TX_TOPUP, TX_VIDEO_REFUND,
)
from app.services.credit_service import (
    credit_service, InsufficientCreditsError,
)


async def _make_user(db, email, credits=10):
    user = User(
        email=email, username=email.split("@")[0],
        hashed_password="x", credits=credits,
        referral_code=f"REF{email[:4].upper()}",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_charge_decrements_credits_and_writes_ledger(db):
    user = await _make_user(db, "charge1@example.com", credits=10)

    tx = await credit_service.charge(
        db, user.id, amount=3, type=TX_IMAGE_GENERATE,
        ref_type="image", ref_id=42,
    )
    await db.commit()

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 7
    assert tx.amount == -3
    assert tx.balance_after == 7
    assert tx.ref_id == 42


@pytest.mark.asyncio
async def test_charge_insufficient_raises(db):
    user = await _make_user(db, "charge2@example.com", credits=2)

    with pytest.raises(InsufficientCreditsError):
        await credit_service.charge(
            db, user.id, amount=5, type=TX_IMAGE_GENERATE,
        )

    # rollback so the session doesn't leak; re-fetch
    await db.rollback()
    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 2  # unchanged


@pytest.mark.asyncio
async def test_grant_increments_credits(db):
    user = await _make_user(db, "grant1@example.com", credits=10)

    tx = await credit_service.grant(
        db, user.id, amount=20, type=TX_TOPUP, note="test topup",
    )
    await db.commit()

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 30
    assert tx.amount == 20
    assert tx.balance_after == 30


@pytest.mark.asyncio
async def test_get_user_transactions_paginated(db):
    user = await _make_user(db, "list1@example.com", credits=100)
    for i in range(5):
        await credit_service.grant(db, user.id, 1, type=TX_TOPUP, note=f"tx{i}")
    await db.commit()

    items, total = await credit_service.get_user_transactions(
        db, user.id, page=1, per_page=3,
    )
    assert total == 5
    assert len(items) == 3


@pytest.mark.asyncio
async def test_video_refund_idempotent_via_caller(db):
    """Caller (video poll handler) is responsible for setting credits_charged=0
    after refund. credit_service.grant itself doesn't dedupe — confirm two
    grants both succeed (so caller-level guard is mandatory)."""
    user = await _make_user(db, "refund1@example.com", credits=10)

    await credit_service.grant(db, user.id, 5, type=TX_VIDEO_REFUND, ref_id=1)
    await credit_service.grant(db, user.id, 5, type=TX_VIDEO_REFUND, ref_id=1)
    await db.commit()

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 20  # 10 + 5 + 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_credit_service.py -v
```

Expected: ImportError (credit_service doesn't exist yet) — counts as failure.

- [ ] **Step 3: Implement CreditService**

Write `backend/app/services/credit_service.py`:

```python
"""Credit ledger service: charges, grants, queries.

Methods do NOT commit — caller controls transaction boundary so the
ledger row and any business rows commit atomically.
"""
import logging
from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.credit_transaction import CreditTransaction

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Raised when a charge would drive balance below zero."""


class CreditService:
    async def charge(
        self,
        db: AsyncSession,
        user_id: int,
        amount: int,
        type: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> CreditTransaction:
        """Deduct `amount` credits from user. amount must be positive.

        Locks the users row with SELECT ... FOR UPDATE (no-op on SQLite).
        Raises InsufficientCreditsError if balance < amount.
        Does NOT commit.
        """
        if amount <= 0:
            raise ValueError("charge amount must be positive")

        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} not found")

        if user.credits < amount:
            raise InsufficientCreditsError(
                f"User {user_id} has {user.credits} credits, needs {amount}"
            )

        user.credits -= amount
        await db.flush()

        tx = CreditTransaction(
            user_id=user_id,
            amount=-amount,
            balance_after=user.credits,
            type=type,
            ref_type=ref_type,
            ref_id=ref_id,
            note=note,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def grant(
        self,
        db: AsyncSession,
        user_id: int,
        amount: int,
        type: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> CreditTransaction:
        """Credit `amount` to user. amount must be positive. Does NOT commit."""
        if amount <= 0:
            raise ValueError("grant amount must be positive")

        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} not found")

        user.credits += amount
        await db.flush()

        tx = CreditTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=user.credits,
            type=type,
            ref_type=ref_type,
            ref_id=ref_id,
            note=note,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def get_user_transactions(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[CreditTransaction], int]:
        """List user's credit transactions, newest first."""
        offset = (page - 1) * per_page

        count_result = await db.execute(
            select(func.count(CreditTransaction.id))
            .where(CreditTransaction.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc(), CreditTransaction.id.desc())
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        return items, total


credit_service = CreditService()
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && pytest tests/test_credit_service.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/credit_service.py backend/tests/test_credit_service.py
git commit -m "feat(credit): CreditService 提供 charge/grant/查询

- with_for_update() 行锁防并发超扣（PG 生效，SQLite no-op）
- 不 commit；调用方控事务边界
- balance_after 快照便于审计

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 3.3: image_service 改走 credit_service

**Files:**
- Modify: `backend/app/services/image_service.py`

- [ ] **Step 1: Update image_service.generate**

Edit `backend/app/services/image_service.py`. Replace the entire `generate` method (currently the version from Stage 1) with:

```python
    async def generate(self, db: AsyncSession, user_id: int, data: Dict) -> ImageGeneration:
        # Pre-check (cheap UX-only check; authoritative check is in credit_service)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.credits < settings.IMAGE_COST:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits. Please recharge.",
            )

        # Call Agnes AI (do NOT charge yet)
        try:
            agnes_response = await agnes_service.generate_image(
                prompt=data["prompt"],
                model=data.get("model", "agnes-image-2.1-flash"),
                size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
                negative_prompt=data.get("negative_prompt", ""),
                style=data.get("style", "none"),
            )
        except Exception as e:
            logger.error(f"Image generation service error for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image generation service is temporarily unavailable. Please try again later.",
            )

        image_url = agnes_response.get("image_url", "")
        succeeded = bool(image_url)

        image_gen = ImageGeneration(
            user_id=user_id,
            prompt=data["prompt"],
            negative_prompt=data.get("negative_prompt", ""),
            model=data.get("model", "agnes-image-2.1-flash"),
            size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
            style=data.get("style", "none"),
            image_url=image_url,
            status="completed" if succeeded else "failed",
            parameters=data,
        )
        if not succeeded:
            image_gen.error_message = "Image generation returned no result"

        db.add(image_gen)
        await db.flush()  # so image_gen.id is populated

        if succeeded:
            from app.services.credit_service import (
                credit_service, InsufficientCreditsError,
            )
            from app.models.credit_transaction import TX_IMAGE_GENERATE
            try:
                await credit_service.charge(
                    db, user_id, settings.IMAGE_COST,
                    type=TX_IMAGE_GENERATE,
                    ref_type="image", ref_id=image_gen.id,
                )
            except InsufficientCreditsError:
                # Race lost: balance dropped between pre-check and charge.
                # Roll back: mark as failed and don't charge.
                await db.rollback()
                logger.warning(
                    f"Concurrency race: insufficient credits for user {user_id} after upstream success"
                )
                # Re-add a failed record after rollback so user sees the attempt
                image_gen = ImageGeneration(
                    user_id=user_id,
                    prompt=data["prompt"],
                    negative_prompt=data.get("negative_prompt", ""),
                    model=data.get("model", "agnes-image-2.1-flash"),
                    size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
                    style=data.get("style", "none"),
                    image_url=image_url,
                    status="failed",
                    error_message="Insufficient credits at charge time",
                    parameters=data,
                )
                db.add(image_gen)
                await db.commit()
                await db.refresh(image_gen)
                return image_gen

        await db.commit()
        await db.refresh(image_gen)
        logger.info(
            f"Image {image_gen.id} generated for user {user_id}, "
            f"status={image_gen.status}"
        )
        return image_gen
```

- [ ] **Step 2: Run regression**

```bash
cd backend && pytest tests/test_image_service.py tests/test_generation.py -v
```

Expected: all pass. The Stage 1 tests still hold (the success path now charges via ledger; the result on the User row is the same).

- [ ] **Step 3: Add a ledger-presence test**

Append to `backend/tests/test_image_service.py`:

```python
@pytest.mark.asyncio
async def test_image_success_writes_ledger_entry(db, monkeypatch):
    from app.models.credit_transaction import CreditTransaction, TX_IMAGE_GENERATE

    user = User(
        email="img-led@example.com",
        username="imgled",
        hashed_password="x",
        credits=10,
        referral_code="REFLED01",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake(**kwargs):
        return {"image_url": "https://example.com/x.png"}

    monkeypatch.setattr(
        "app.services.image_service.agnes_service.generate_image", fake
    )

    image = await image_service.generate(db, user.id, {
        "prompt": "p", "model": "agnes-image-2.1-flash",
        "size": "1024x768", "style": "none",
    })

    txs = (await db.execute(
        select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    )).scalars().all()
    assert len(txs) == 1
    assert txs[0].type == TX_IMAGE_GENERATE
    assert txs[0].amount == -1
    assert txs[0].ref_id == image.id
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_image_service.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/image_service.py backend/tests/test_image_service.py
git commit -m "refactor(image): 扣分改走 credit_service ledger

- 成功后调 credit_service.charge 写入流水
- 并发争用导致 InsufficientCreditsError 时回滚并标记失败
- 新增 ledger 写入测试

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 3.4: video_service 改走 credit_service

**Files:**
- Modify: `backend/app/services/video_service.py`

- [ ] **Step 1: Update video create_video to use credit_service**

In `backend/app/services/video_service.py`, replace the segment that does `user.credits -= cost` (Task 2.3) with `credit_service.charge`.

Locate this block (added in Task 2.3):
```python
        video_gen.credits_charged = cost
        user.credits -= cost
        await db.commit()
```

Replace with:
```python
        from app.services.credit_service import credit_service, InsufficientCreditsError
        from app.models.credit_transaction import TX_VIDEO_GENERATE

        try:
            await credit_service.charge(
                db, user_id, cost,
                type=TX_VIDEO_GENERATE,
                ref_type="video", ref_id=video_gen.id,
            )
        except InsufficientCreditsError:
            # Concurrency race: balance dropped after pre-check.
            # Mark task failed locally; upstream task is created but we won't
            # surface it — admin can clean up via logs.
            await db.rollback()
            logger.error(
                f"Race: insufficient credits for user {user_id} after upstream "
                f"created video task. video_id={video_gen.video_id}"
            )
            raise HTTPException(
                status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits at charge time. Please retry.",
            )
        video_gen.credits_charged = cost
        await db.commit()
```

(`user.credits -= cost` removed — credit_service.charge does it under the row lock.)

- [ ] **Step 2: Run regression**

```bash
cd backend && pytest tests/test_video_charge.py tests/test_generation.py -v
```

Expected: all pass.

- [ ] **Step 3: Add ledger entry assertion**

Append to `backend/tests/test_video_charge.py`:

```python
@pytest.mark.asyncio
async def test_video_create_writes_ledger_entry(db, monkeypatch):
    from app.models.credit_transaction import CreditTransaction, TX_VIDEO_GENERATE

    user = User(
        email="vid-led@example.com",
        username="vidled",
        hashed_password="x",
        credits=100,
        referral_code="REFVLED",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def fake_create_task(**kwargs):
        return {
            "id": "task-led", "task_id": "task-led",
            "video_id": "vid-led", "status": "queued", "progress": 0,
        }
    monkeypatch.setattr(
        "app.services.video_service.agnes_service.create_video_task",
        fake_create_task,
    )

    result = await video_service.create_video(
        db=db, user_id=user.id, prompt="p",
        num_frames=121, frame_rate=24,
    )

    txs = (await db.execute(
        select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    )).scalars().all()
    assert len(txs) == 1
    assert txs[0].type == TX_VIDEO_GENERATE
    assert txs[0].amount == -result["credits_charged"]
    assert txs[0].ref_id == result["id"]
```

(Note: `from app.models.user import User` and `from sqlalchemy import select` already imported in this test file.)

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_video_charge.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/video_service.py backend/tests/test_video_charge.py
git commit -m "refactor(video): 扣分改走 credit_service ledger

- create_video 成功路径调 credit_service.charge 写流水
- 并发争用走 402 异常，避免无单据扣分
- 新增 ledger 写入测试

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 3.5: auth_service 注册 / 推荐改走 grant

**Files:**
- Modify: `backend/app/services/auth_service.py`

- [ ] **Step 1: Update register**

Edit `backend/app/services/auth_service.py`. Replace the `register` method body:

```python
    async def register(self, db: AsyncSession, data: UserRegister) -> User:
        # Check duplicate
        existing = await db.execute(
            select(User).where(
                (User.email == data.email) | (User.username == data.username)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )

        referral_code = f"REF{secrets.token_hex(4).upper()}"

        # Create user with 0 credits; grant via ledger so totals stay consistent
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
            referral_code=referral_code,
            credits=0,
        )
        db.add(user)
        await db.flush()  # populate user.id

        # Local import to avoid circular: credit_service -> models -> user
        from app.services.credit_service import credit_service
        from app.models.credit_transaction import (
            TX_REGISTER_BONUS, TX_REFERRAL_BONUS,
        )

        await credit_service.grant(
            db, user.id, settings.FREE_CREDITS_ON_REGISTER,
            type=TX_REGISTER_BONUS, note="register bonus",
        )

        # Handle referral
        if data.referral_code:
            result = await db.execute(
                select(User).where(User.referral_code == data.referral_code)
            )
            referrer = result.scalar_one_or_none()
            if referrer and referrer.id != user.id:
                user.referred_by = referrer.id
                await credit_service.grant(
                    db, referrer.id, settings.REFERRAL_BONUS,
                    type=TX_REFERRAL_BONUS,
                    ref_type="user", ref_id=user.id,
                    note=f"referred {user.email}",
                )

        await db.commit()
        await db.refresh(user)
        logger.info(f"User registered: {user.email} (id={user.id})")
        return user
```

- [ ] **Step 2: Run auth regression**

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected: all pass. The `data["credits"] == 10` assertion in `test_register` still holds because `FREE_CREDITS_ON_REGISTER = 10`.

- [ ] **Step 3: Add ledger assertion test**

Append to `backend/tests/test_auth.py`:

```python
@pytest.mark.asyncio
async def test_register_writes_register_bonus_ledger(client):
    from app.models.credit_transaction import (
        CreditTransaction, TX_REGISTER_BONUS,
    )
    from app.models.user import User
    from sqlalchemy import select
    from tests.conftest import TestSessionLocal

    resp = await client.post("/api/auth/register", json={
        "email": "ledger@example.com",
        "username": "ledgeruser",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 201

    async with TestSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.email == "ledger@example.com")
        )).scalar_one()
        txs = (await session.execute(
            select(CreditTransaction).where(CreditTransaction.user_id == user.id)
        )).scalars().all()
        assert len(txs) == 1
        assert txs[0].type == TX_REGISTER_BONUS
        assert txs[0].amount == 10
        assert txs[0].balance_after == 10
```

- [ ] **Step 4: Run**

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected: all pass (existing + 1 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/auth_service.py backend/tests/test_auth.py
git commit -m "refactor(auth): 注册赠送 / 推荐奖励改走 credit_service.grant

- credits 字段统一通过 ledger 维护
- 防止用户用自己的 referral_code 自循环（id 比对）
- 新增 register_bonus ledger 单测

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 3.6: 用户流水 API

**Files:**
- Create: `backend/app/schemas/credit.py`
- Modify: `backend/app/api/users.py`
- Create: `backend/tests/test_credit_api.py`

- [ ] **Step 1: Create response schemas**

Write `backend/app/schemas/credit.py`:

```python
"""Schemas for credit ledger API."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CreditTransactionResponse(BaseModel):
    id: int
    amount: int
    balance_after: int
    type: str
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreditTransactionListResponse(BaseModel):
    items: List[CreditTransactionResponse]
    total: int
    page: int
    per_page: int
```

- [ ] **Step 2: Add endpoint to users.py**

Edit `backend/app/api/users.py`. Add at the bottom:

```python
from fastapi import Query
from app.schemas.credit import CreditTransactionListResponse
from app.services.credit_service import credit_service


@router.get("/credits/transactions", response_model=CreditTransactionListResponse)
async def list_credit_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of the current user's credit transactions."""
    items, total = await credit_service.get_user_transactions(
        db, current_user.id, page, per_page,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }
```

(`Query` may already be imported — if so, skip duplicate.)

- [ ] **Step 3: Write API tests**

Write `backend/tests/test_credit_api.py`:

```python
"""Tests for /api/users/credits/transactions."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_credit_transactions_returns_register_bonus(
    authenticated_client: AsyncClient,
):
    resp = await authenticated_client.get("/api/users/credits/transactions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    types = [tx["type"] for tx in data["items"]]
    assert "register_bonus" in types


@pytest.mark.asyncio
async def test_credit_transactions_pagination(authenticated_client: AsyncClient):
    resp = await authenticated_client.get(
        "/api/users/credits/transactions",
        params={"page": 1, "per_page": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["per_page"] == 1
    assert len(data["items"]) <= 1


@pytest.mark.asyncio
async def test_credit_transactions_requires_auth(client: AsyncClient):
    resp = await client.get("/api/users/credits/transactions")
    assert resp.status_code == 401
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_credit_api.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/schemas/credit.py backend/app/api/users.py backend/tests/test_credit_api.py
git commit -m "feat(api): GET /api/users/credits/transactions 流水分页查询

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 3.7: 历史用户回填脚本

**Files:**
- Create: `backend/scripts/__init__.py`
- Create: `backend/scripts/backfill_credit_ledger.py`

- [ ] **Step 1: Create scripts package**

Write `backend/scripts/__init__.py` as an empty file:

```python
```

- [ ] **Step 2: Implement the script**

Write `backend/scripts/backfill_credit_ledger.py`:

```python
"""Backfill `credit_transactions` for users who pre-date the ledger.

Idempotent: safe to re-run. For each user that has 0 transaction rows,
inserts a single `migration_initial` row with amount=balance_after=user.credits.

Usage:
    cd backend
    python -m scripts.backfill_credit_ledger
"""
import asyncio
import logging

from sqlalchemy import select, func

from app.core.database import async_session
from app.models.user import User
from app.models.credit_transaction import (
    CreditTransaction, TX_MIGRATION_INITIAL,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("backfill_credit_ledger")


async def backfill():
    inserted = 0
    skipped = 0
    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()
        for user in users:
            count = (await session.execute(
                select(func.count(CreditTransaction.id))
                .where(CreditTransaction.user_id == user.id)
            )).scalar() or 0
            if count > 0:
                skipped += 1
                continue
            tx = CreditTransaction(
                user_id=user.id,
                amount=user.credits,
                balance_after=user.credits,
                type=TX_MIGRATION_INITIAL,
                note="initial backfill",
            )
            session.add(tx)
            inserted += 1
        await session.commit()
    logger.info(f"Backfill complete: inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(backfill())
```

- [ ] **Step 3: Test idempotency**

Add to `backend/tests/test_credit_service.py`:

```python
@pytest.mark.asyncio
async def test_backfill_script_is_idempotent(db):
    """Running backfill twice should produce a single migration_initial row."""
    from app.models.credit_transaction import (
        CreditTransaction, TX_MIGRATION_INITIAL,
    )
    user = await _make_user(db, "backfill@example.com", credits=42)
    # Direct call to logic (not the asyncio.run shim) to share the test session
    from sqlalchemy import select as _select, func as _func

    async def _do_backfill(session):
        count = (await session.execute(
            _select(_func.count(CreditTransaction.id))
            .where(CreditTransaction.user_id == user.id)
        )).scalar() or 0
        if count > 0:
            return 0
        session.add(CreditTransaction(
            user_id=user.id, amount=user.credits,
            balance_after=user.credits,
            type=TX_MIGRATION_INITIAL,
            note="initial backfill",
        ))
        return 1

    inserted_first = await _do_backfill(db)
    await db.commit()
    inserted_second = await _do_backfill(db)
    await db.commit()

    assert inserted_first == 1
    assert inserted_second == 0

    txs = (await db.execute(
        _select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    )).scalars().all()
    assert len(txs) == 1
    assert txs[0].type == TX_MIGRATION_INITIAL
    assert txs[0].amount == 42
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_credit_service.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/scripts/__init__.py backend/scripts/backfill_credit_ledger.py backend/tests/test_credit_service.py
git commit -m "feat(credit): 历史用户 ledger 回填脚本

幂等：每个用户只插入一条 migration_initial 记录。
运行：cd backend && python -m scripts.backfill_credit_ledger

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Stage 4: 视频越权 + URL bug

### Task 4.1: URL 抽取纯函数 + 单测

**Files:**
- Modify: `backend/app/services/video_service.py`
- Create: `backend/tests/test_video_service.py`

- [ ] **Step 1: Write failing tests**

Write `backend/tests/test_video_service.py`:

```python
"""Tests for video_service URL extraction and authorization."""
import pytest

from app.services.video_service import _extract_video_url


def test_extract_top_level_video_url():
    assert _extract_video_url({
        "video_url": "https://cdn.example.com/v.mp4"
    }) == "https://cdn.example.com/v.mp4"


def test_extract_top_level_url_alias():
    assert _extract_video_url({
        "url": "https://cdn.example.com/v.mp4"
    }) == "https://cdn.example.com/v.mp4"


def test_extract_output_list_dict():
    assert _extract_video_url({
        "output": [{"video_url": "https://cdn.example.com/v.mp4"}]
    }) == "https://cdn.example.com/v.mp4"


def test_extract_output_list_string():
    assert _extract_video_url({
        "output": ["https://cdn.example.com/v.mp4"]
    }) == "https://cdn.example.com/v.mp4"


def test_extract_output_dict():
    assert _extract_video_url({
        "output": {"download_url": "https://cdn.example.com/v.mp4"}
    }) == "https://cdn.example.com/v.mp4"


def test_extract_data_nested():
    assert _extract_video_url({
        "data": {"video_url": "https://cdn.example.com/v.mp4"}
    }) == "https://cdn.example.com/v.mp4"


def test_extract_rejects_non_http_string():
    """Old bug: remixed_from_video_id (an ID) used to land in video_url."""
    assert _extract_video_url({
        "remixed_from_video_id": "vid_abc123",
        "video_url": None,
    }) is None


def test_extract_returns_none_for_empty():
    assert _extract_video_url({}) is None


def test_extract_returns_none_when_only_id_present():
    assert _extract_video_url({"id": "x", "task_id": "y"}) is None
```

- [ ] **Step 2: Run tests to verify fail**

```bash
cd backend && pytest tests/test_video_service.py -v
```

Expected: ImportError (`_extract_video_url` not defined).

- [ ] **Step 3: Implement the function**

Edit `backend/app/services/video_service.py`. Add at module level (after imports, before `class VideoService`):

```python
def _extract_video_url(payload: dict) -> Optional[str]:
    """Extract a video URL from upstream payload across known shapes.

    Returns None if no plausible URL is found. Pure function, no IO.
    """
    def _is_url(v):
        return isinstance(v, str) and v.startswith(("http://", "https://"))

    if not isinstance(payload, dict):
        return None

    for key in ("video_url", "url", "download_url", "output_url"):
        v = payload.get(key)
        if _is_url(v):
            return v

    output = payload.get("output")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            for key in ("video_url", "url", "download_url"):
                v = first.get(key)
                if _is_url(v):
                    return v
        elif _is_url(first):
            return first
    elif isinstance(output, dict):
        for key in ("video_url", "url", "download_url"):
            v = output.get(key)
            if _is_url(v):
                return v

    data = payload.get("data")
    if isinstance(data, dict):
        return _extract_video_url(data)

    return None
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_video_service.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/video_service.py backend/tests/test_video_service.py
git commit -m "feat(video): _extract_video_url 纯函数兼容多种上游响应

按 fallback 顺序搜索 video_url / url / download_url / output_url，
支持 output 为列表 / 对象 / data 嵌套，拒绝非 http 字符串。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 4.2: 修 poll_video_status 越权 + URL bug + 失败退款

**Files:**
- Modify: `backend/app/services/video_service.py`

- [ ] **Step 1: Write authorization test**

Append to `backend/tests/test_video_service.py`:

```python
import pytest as _pytest
from sqlalchemy import select
from app.models.user import User
from app.models.video import VideoGeneration
from app.services.video_service import video_service


async def _make_user_and_video(db, email):
    user = User(
        email=email, username=email.split("@")[0], hashed_password="x",
        credits=100, referral_code=f"REF{email[:4].upper()}",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    video = VideoGeneration(
        user_id=user.id, prompt="p",
        task_id="t-" + email, video_id="v-" + email,
        status="queued", num_frames=121, frame_rate=24,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return user, video


@_pytest.mark.asyncio
async def test_poll_rejects_other_user(db):
    """User B polling user A's video_id must get 404."""
    from fastapi import HTTPException
    alice, video = await _make_user_and_video(db, "alice@example.com")
    bob = User(
        email="bob@example.com", username="bob", hashed_password="x",
        credits=10, referral_code="REFBOB",
    )
    db.add(bob)
    await db.commit()
    await db.refresh(bob)

    with _pytest.raises(HTTPException) as exc:
        await video_service.poll_video_status(db, video.video_id, user_id=bob.id)
    assert exc.value.status_code == 404


@_pytest.mark.asyncio
async def test_poll_completed_with_url_updates_record(db, monkeypatch):
    user, video = await _make_user_and_video(db, "polluser@example.com")
    video.credits_charged = 5
    await db.commit()

    async def fake_poll(vid):
        return {
            "status": "completed",
            "progress": 100,
            "video_url": "https://cdn.example.com/done.mp4",
        }
    monkeypatch.setattr(
        "app.services.video_service.agnes_service.poll_video_status",
        fake_poll,
    )

    result = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result["status"] == "completed"
    assert result["video_url"] == "https://cdn.example.com/done.mp4"

    refreshed = (await db.execute(
        select(VideoGeneration).where(VideoGeneration.id == video.id)
    )).scalar_one()
    assert refreshed.video_url == "https://cdn.example.com/done.mp4"


@_pytest.mark.asyncio
async def test_poll_completed_without_url_marks_failed_and_refunds(db, monkeypatch):
    from app.models.credit_transaction import CreditTransaction, TX_VIDEO_REFUND
    user, video = await _make_user_and_video(db, "norefund@example.com")
    video.credits_charged = 6
    await db.commit()
    initial_credits = user.credits

    async def fake_poll(vid):
        # Upstream says completed but no URL anywhere
        return {"status": "completed", "remixed_from_video_id": "vid_xyz"}
    monkeypatch.setattr(
        "app.services.video_service.agnes_service.poll_video_status",
        fake_poll,
    )

    result = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result["status"] == "failed"

    refreshed_video = (await db.execute(
        select(VideoGeneration).where(VideoGeneration.id == video.id)
    )).scalar_one()
    assert refreshed_video.status == "failed"
    assert refreshed_video.credits_charged == 0  # refunded marker

    refreshed_user = (await db.execute(
        select(User).where(User.id == user.id)
    )).scalar_one()
    assert refreshed_user.credits == initial_credits + 6

    txs = (await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .where(CreditTransaction.type == TX_VIDEO_REFUND)
    )).scalars().all()
    assert len(txs) == 1


@_pytest.mark.asyncio
async def test_poll_failed_status_refunds_once(db, monkeypatch):
    from app.models.credit_transaction import CreditTransaction, TX_VIDEO_REFUND
    user, video = await _make_user_and_video(db, "failpoll@example.com")
    video.credits_charged = 4
    await db.commit()

    async def fake_poll(vid):
        return {"status": "failed", "error": {"message": "boom"}}
    monkeypatch.setattr(
        "app.services.video_service.agnes_service.poll_video_status",
        fake_poll,
    )

    # First poll: refund
    result1 = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result1["status"] == "failed"
    # Second poll: must NOT refund again
    result2 = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result2["status"] == "failed"

    txs = (await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .where(CreditTransaction.type == TX_VIDEO_REFUND)
    )).scalars().all()
    assert len(txs) == 1  # idempotent
```

- [ ] **Step 2: Run tests to verify fail**

```bash
cd backend && pytest tests/test_video_service.py -v
```

Expected: the 4 new tests fail (越权未校验 / URL 写错 / 失败不退款).

- [ ] **Step 3: Replace poll_video_status**

Edit `backend/app/services/video_service.py`. Replace the entire `poll_video_status` method:

```python
    async def poll_video_status(
        self, db: AsyncSession, video_id: str, user_id: int = None,
    ) -> Dict:
        """Poll video generation status.

        - 强制 user_id 校验：找不到记录或不属于该用户都返回 404。
        - 成功时按 fallback 顺序提取 video URL；提取失败按"完成但无 URL"处理并退款。
        - 失败时退款一次（防重入：credits_charged > 0 才退）。
        """
        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id is required")

        result = await db.execute(
            select(VideoGeneration).where(
                VideoGeneration.video_id == video_id,
                VideoGeneration.user_id == user_id,
            )
        )
        video_gen = result.scalar_one_or_none()
        if not video_gen:
            raise HTTPException(status_code=404, detail="Video not found")

        try:
            api_response = await agnes_service.poll_video_status(video_id)
        except Exception as e:
            logger.error(f"Failed to poll video status for {video_id}: {e}")
            raise Exception("Failed to poll video status. Please try again later.")

        upstream_status = api_response.get("status")
        progress = api_response.get("progress", 0)

        # Defer the refund import to here to avoid circulars at module load
        from app.services.credit_service import credit_service
        from app.models.credit_transaction import TX_VIDEO_REFUND

        async def _refund_if_needed(reason: str):
            if video_gen.credits_charged and video_gen.credits_charged > 0:
                await credit_service.grant(
                    db, video_gen.user_id, video_gen.credits_charged,
                    type=TX_VIDEO_REFUND,
                    ref_type="video", ref_id=video_gen.id,
                    note=reason,
                )
                video_gen.credits_charged = 0

        video_gen.progress = progress

        error_message = None
        if upstream_status == "completed":
            url = _extract_video_url(api_response)
            if url:
                video_gen.video_url = url
                video_gen.status = "completed"
                video_gen.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            else:
                logger.error(
                    f"Video {video_gen.id} marked completed but URL missing. "
                    f"Response: {str(api_response)[:500]}"
                )
                video_gen.status = "failed"
                video_gen.error_message = "Upstream completed but no video URL"
                error_message = video_gen.error_message
                await _refund_if_needed("completed_no_url")
                upstream_status = "failed"  # surface to caller
        elif upstream_status == "failed":
            err = api_response.get("error") or {}
            video_gen.status = "failed"
            video_gen.error_message = err.get("message", "Unknown error") if isinstance(err, dict) else str(err)
            error_message = video_gen.error_message
            await _refund_if_needed("generation_failed")
        else:
            # queued / generating: just record progress
            video_gen.status = upstream_status or video_gen.status

        await db.commit()

        return {
            "status": upstream_status,
            "progress": progress,
            "video_url": video_gen.video_url if upstream_status == "completed" else None,
            "error_message": error_message,
            "seconds": api_response.get("seconds"),
            "size": api_response.get("size"),
        }
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_video_service.py -v
cd backend && pytest -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add backend/app/services/video_service.py backend/tests/test_video_service.py
git commit -m "fix(video): 轮询越权校验 + 修 video_url 字段映射 + 失败退款

- poll_video_status 强制按 (video_id, user_id) 鉴权，越权返 404
- 完成时调 _extract_video_url 取真实 URL，找不到判失败并退款
- failed 状态首次见到时退款，credits_charged 置 0 防重入

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Final Verification

### Task FV.1: 全量回归 + 流水一致性手动验证

- [ ] **Step 1: Full test run**

```bash
cd backend && pytest -v
```

Expected: all tests pass, no warnings about un-awaited coroutines.

- [ ] **Step 2: Manual smoke (optional, only if backend is runnable locally)**

如果有可用的本地 backend：

```bash
# 启动 backend
cd backend && uvicorn app.main:app --reload --port 8000

# 在另一个终端
# 1. 注册用户 -> 检查 GET /api/users/credits/transactions 出现 register_bonus
# 2. 调 POST /api/images/generate -> 检查流水中出现 image_generate
# 3. 调 GET /api/users/credits/transactions 验证总额 = users.credits
```

- [ ] **Step 3: Update PRODUCTION_PLAN.md**

Edit `PRODUCTION_PLAN.md`. Append at end of execution log section:

```markdown
### 资损与越权急修包完成 ✅ (2026-06-15)

#### 阶段 1：图像失败不扣积分 ✅
- image_service.generate 仅在 image_url 非空且上游未异常时扣 IMAGE_COST

#### 阶段 2：视频积分扣减 ✅
- video.credits_charged 列
- create_video 上游成功后按 ceil(duration * VIDEO_COST_PER_SECOND) 扣分
- 余额不足返 402

#### 阶段 3：积分 ledger + 行锁 ✅
- 新增 credit_transactions 表 + CreditService（charge / grant / 查询）
- with_for_update 行锁防并发超扣（PG 生效，SQLite 退化）
- image / video / register / referral 全部改走 ledger
- 新增 GET /api/users/credits/transactions 流水查询
- 历史用户回填脚本 backend/scripts/backfill_credit_ledger.py

#### 阶段 4：视频越权 + URL bug ✅
- poll_video_status 强制 user_id 校验
- _extract_video_url 纯函数按 fallback 取 URL
- 失败 / 无 URL 自动退款（credits_charged 置 0 防重入）
```

- [ ] **Step 4: Commit final docs update**

```bash
cd /Users/yuhuibin/code/tool/agnes-studio
git add PRODUCTION_PLAN.md
git commit -m "docs: 资损与越权急修包完成记录

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Push branch**

```bash
git push -u origin feat/credit-fix-pack
```

---

## Self-Review Notes

- **Spec coverage**：每个 spec 阶段（1/2/3/4）均有对应 Task。Task 3.5 覆盖 spec §3.3 中 register/referral 改造；Task 3.7 覆盖 §3.4 回填；Task 4.2 覆盖 §3.5 视频失败退款（合并到此处与 §4.3 一并实现）。
- **类型一致性**：`TX_*` 常量在所有 Task 中使用同一组名字；`InsufficientCreditsError` 仅在 Task 3.2 定义并在 3.3/3.4 import；`_extract_video_url` 在 4.1 定义在 4.2 使用，签名一致。
- **No placeholder**：每个步骤都给出完整代码或确切命令；commit 模板含 Co-Authored-By；测试代码完整。
- **Frequent commits**：每个 Task 末尾 commit；阶段 1 一个 commit，阶段 2 三个，阶段 3 七个，阶段 4 两个，最终一个 = 14 个 commits。
