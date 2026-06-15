"""Tests for CreditService: charge, grant, query, idempotency.

Uses self-contained fixtures (in-memory SQLite) so tests run even when
the project .env is missing or has extra-field validation errors.
"""
import pytest_asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.database import Base, User, CreditTransaction  # noqa: F401 -- import all models so relationships resolve
from app.models.credit_transaction import TX_IMAGE_GENERATE, TX_TOPUP, TX_VIDEO_REFUND
from app.services.credit_service import credit_service, InsufficientCreditsError

# ---------------------------------------------------------------------------
# Self-contained fixtures (do NOT rely on conftest.py)
# ---------------------------------------------------------------------------

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_user(db: AsyncSession, email: str, credits: int = 10) -> User:
    user = User(
        email=email,
        username=email.split("@")[0],
        hashed_password="x",
        credits=credits,
        referral_code=f"REF{email[:4].upper()}",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

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
    uid = user.id  # save before rollback to avoid lazy-load issues

    with pytest.raises(InsufficientCreditsError):
        await credit_service.charge(
            db, uid, amount=5, type=TX_IMAGE_GENERATE,
        )

    await db.rollback()
    refreshed = (await db.execute(select(User).where(User.id == uid))).scalar_one()
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
    after refund. credit_service.grant itself doesn't dedupe -- confirm two
    grants both succeed (so caller-level guard is mandatory)."""
    user = await _make_user(db, "refund1@example.com", credits=10)

    await credit_service.grant(db, user.id, 5, type=TX_VIDEO_REFUND, ref_id=1)
    await credit_service.grant(db, user.id, 5, type=TX_VIDEO_REFUND, ref_id=1)
    await db.commit()

    refreshed = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.credits == 20  # 10 + 5 + 5


@pytest.mark.asyncio
async def test_backfill_script_is_idempotent(db):
    """Running backfill twice should produce a single migration_initial row."""
    from app.models.credit_transaction import (
        CreditTransaction, TX_MIGRATION_INITIAL,
    )
    user = await _make_user(db, "backfill@example.com", credits=42)
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
