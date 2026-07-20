"""Test Auth Service"""
import pytest
from httpx import AsyncClient

from app.schemas.auth import UserRegister, UserLogin
from app.services.auth_service import auth_service
from app.core.config import settings


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """Test successful registration."""
    resp = await client.post("/api/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert data["credits"] == settings.FREE_CREDITS_ON_REGISTER


@pytest.mark.asyncio
async def test_duplicate_register(client: AsyncClient):
    """Test duplicate registration fails."""
    await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "username": "dupuser",
        "password": "SecurePass123!",
    })
    resp = await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "username": "dupuser",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "SecurePass123!",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password fails."""
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com",
        "username": "wronguser",
        "password": "SecurePass123!",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user fails."""
    resp = await client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(authenticated_client: AsyncClient):
    """Test get current user info."""
    resp = await authenticated_client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test get me without auth fails."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password(authenticated_client: AsyncClient):
    """Test password change."""
    resp = await authenticated_client.post("/api/auth/change-password", json={
        "old_password": "TestPass123!",
        "new_password": "NewSecurePass456!",
    })
    assert resp.status_code == 200

    # Old token should be invalidated (token_version incremented)
    resp = await authenticated_client.get("/api/auth/me")
    assert resp.status_code == 401

    # Login with new password should work
    resp = await authenticated_client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "NewSecurePass456!",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(authenticated_client: AsyncClient):
    """Test password change with wrong old password fails."""
    resp = await authenticated_client.post("/api/auth/change-password", json={
        "old_password": "WrongOldPassword!",
        "new_password": "NewSecurePass456!",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test token refresh."""
    await client.post("/api/auth/register", json={
        "email": "refresh@example.com",
        "username": "refreshuser",
        "password": "SecurePass123!",
    })
    login_resp = await client.post("/api/auth/login", json={
        "email": "refresh@example.com",
        "password": "SecurePass123!",
    })
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_rate_limit_login(client: AsyncClient):
    """Test login rate limiting."""
    for i in range(5):
        await client.post("/api/auth/login", json={
            "email": f"rate{i}@example.com",
            "password": "SecurePass123!",
        })
    resp = await client.post("/api/auth/login", json={
        "email": "rate5@example.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_register_writes_register_bonus_ledger(db):
    """Register via service directly and verify ledger entry exists."""
    from app.models.credit_transaction import (
        CreditTransaction, TX_REGISTER_BONUS,
    )
    from app.models.user import User
    from app.schemas.auth import UserRegister
    from app.services.auth_service import auth_service
    from sqlalchemy import select

    data = UserRegister(
        email="ledger@example.com",
        username="ledgeruser",
        password="SecurePass123!",
    )
    user = await auth_service.register(db, data)

    txs = (await db.execute(
        select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    )).scalars().all()
    assert len(txs) == 1
    assert txs[0].type == TX_REGISTER_BONUS
    assert txs[0].amount == settings.FREE_CREDITS_ON_REGISTER
    assert txs[0].balance_after == settings.FREE_CREDITS_ON_REGISTER
