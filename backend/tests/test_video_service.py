"""Tests for video_service URL extraction and authorization."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator

from app.core.database import Base
from app.models.user import User
from app.models.video import VideoGeneration
from app.models.image import ImageGeneration  # noqa: F401
from app.models.gallery import GalleryItem  # noqa: F401
from app.models.api_key import ApiKey  # noqa: F401
from app.services.video_service import _extract_video_url, video_service


# --- Self-contained fixtures ---
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session


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


# --- URL extraction tests (no db needed) ---

def test_extract_top_level_video_url():
    assert _extract_video_url({"video_url": "https://cdn.example.com/v.mp4"}) == "https://cdn.example.com/v.mp4"


def test_extract_top_level_url_alias():
    assert _extract_video_url({"url": "https://cdn.example.com/v.mp4"}) == "https://cdn.example.com/v.mp4"


def test_extract_output_list_dict():
    assert _extract_video_url({"output": [{"video_url": "https://cdn.example.com/v.mp4"}]}) == "https://cdn.example.com/v.mp4"


def test_extract_output_list_string():
    assert _extract_video_url({"output": ["https://cdn.example.com/v.mp4"]}) == "https://cdn.example.com/v.mp4"


def test_extract_output_dict():
    assert _extract_video_url({"output": {"download_url": "https://cdn.example.com/v.mp4"}}) == "https://cdn.example.com/v.mp4"


def test_extract_data_nested():
    assert _extract_video_url({"data": {"video_url": "https://cdn.example.com/v.mp4"}}) == "https://cdn.example.com/v.mp4"


def test_extract_rejects_non_http_string():
    assert _extract_video_url({"remixed_from_video_id": "vid_abc123", "video_url": None}) is None


def test_extract_returns_none_for_empty():
    assert _extract_video_url({}) is None


def test_extract_returns_none_when_only_id_present():
    assert _extract_video_url({"id": "x", "task_id": "y"}) is None


# --- Authorization tests ---

@pytest.mark.asyncio
async def test_poll_rejects_other_user(db):
    from fastapi import HTTPException
    alice, video = await _make_user_and_video(db, "alice@example.com")
    bob = User(
        email="bob@example.com", username="bob", hashed_password="x",
        credits=10, referral_code="REFBOB",
    )
    db.add(bob)
    await db.commit()
    await db.refresh(bob)

    with pytest.raises(HTTPException) as exc:
        await video_service.poll_video_status(db, video.video_id, user_id=bob.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_poll_completed_with_url_updates_record(db, monkeypatch):
    user, video = await _make_user_and_video(db, "polluser@example.com")
    video.credits_charged = 5
    await db.commit()

    async def fake_poll(vid):
        return {"status": "completed", "progress": 100, "video_url": "https://cdn.example.com/done.mp4"}
    monkeypatch.setattr("app.services.video_service.agnes_service.poll_video_status", fake_poll)

    result = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result["status"] == "completed"
    assert result["video_url"] == "https://cdn.example.com/done.mp4"

    refreshed = (await db.execute(select(VideoGeneration).where(VideoGeneration.id == video.id))).scalar_one()
    assert refreshed.video_url == "https://cdn.example.com/done.mp4"


@pytest.mark.asyncio
async def test_poll_completed_without_url_marks_failed_and_refunds(db, monkeypatch):
    from app.models.credit_transaction import CreditTransaction, TX_VIDEO_REFUND
    user, video = await _make_user_and_video(db, "norefund@example.com")
    video.credits_charged = 6
    await db.commit()
    initial_credits = user.credits

    async def fake_poll(vid):
        return {"status": "completed", "remixed_from_video_id": "vid_xyz"}
    monkeypatch.setattr("app.services.video_service.agnes_service.poll_video_status", fake_poll)

    result = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result["status"] == "failed"

    refreshed_video = (await db.execute(select(VideoGeneration).where(VideoGeneration.id == video.id))).scalar_one()
    assert refreshed_video.status == "failed"
    assert refreshed_video.credits_charged == 0

    refreshed_user = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed_user.credits == initial_credits + 6

    txs = (await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .where(CreditTransaction.type == TX_VIDEO_REFUND)
    )).scalars().all()
    assert len(txs) == 1


@pytest.mark.asyncio
async def test_poll_failed_status_refunds_once(db, monkeypatch):
    from app.models.credit_transaction import CreditTransaction, TX_VIDEO_REFUND
    user, video = await _make_user_and_video(db, "failpoll@example.com")
    video.credits_charged = 4
    await db.commit()

    async def fake_poll(vid):
        return {"status": "failed", "error": {"message": "boom"}}
    monkeypatch.setattr("app.services.video_service.agnes_service.poll_video_status", fake_poll)

    result1 = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result1["status"] == "failed"
    result2 = await video_service.poll_video_status(db, video.video_id, user_id=user.id)
    assert result2["status"] == "failed"

    txs = (await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .where(CreditTransaction.type == TX_VIDEO_REFUND)
    )).scalars().all()
    assert len(txs) == 1  # idempotent
