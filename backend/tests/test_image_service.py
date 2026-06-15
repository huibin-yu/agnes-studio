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
    """Upstream raises -> credits unchanged."""
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
