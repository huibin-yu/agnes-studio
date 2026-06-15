"""Tests for video_service credit charging behavior."""
import math
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

    # 121 / 24 = 5.0416...s -> 5.0416 * VIDEO_COST_PER_SECOND -> ceil
    expected_cost = math.ceil((121 / 24) * settings.VIDEO_COST_PER_SECOND)
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
