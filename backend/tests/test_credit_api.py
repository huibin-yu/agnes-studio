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
