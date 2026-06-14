"""Test Generation Services"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_image(authenticated_client: AsyncClient):
    """Test image generation endpoint."""
    with patch("app.services.image_service.image_service.generate") as mock_generate:
        mock_generate.return_value = AsyncMock(
            id=1,
            prompt="test prompt",
            image_url="https://example.com/image.jpg",
            image_b64=None,
            status="completed",
            seed=42,
            size="1024x768",
            style="cinematic",
            created_at="2026-01-01T00:00:00Z",
        )
        resp = await authenticated_client.post("/api/images/generate", json={
            "prompt": "A beautiful sunset",
            "size": "1024x768",
            "style": "cinematic",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["prompt"] == "test prompt"
        assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_generate_image_unauthorized(client: AsyncClient):
    """Test image generation without auth fails."""
    resp = await client.post("/api/images/generate", json={
        "prompt": "A beautiful sunset",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_image_styles(client: AsyncClient):
    """Test get available styles."""
    resp = await client.get("/api/images/styles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_image_sizes(client: AsyncClient):
    """Test get available sizes."""
    resp = await client.get("/api/images/sizes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_generate_video(authenticated_client: AsyncClient):
    """Test video generation endpoint."""
    with patch("app.services.video_service.video_service.create_video") as mock_create:
        mock_create.return_value = AsyncMock(
            id=1,
            prompt="test video",
            task_id="task123",
            video_id="video123",
            status="queued",
            created_at="2026-01-01T00:00:00Z",
        )
        resp = await authenticated_client.post("/api/videos/generate", json={
            "prompt": "A cat walking",
            "num_frames": 121,
            "frame_rate": 24,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["prompt"] == "test video"
        assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_gallery_public(client: AsyncClient):
    """Test public gallery endpoint."""
    resp = await client.get("/api/gallery/public")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


@pytest.mark.asyncio
async def test_get_public_gallery_item_detail(client: AsyncClient, authenticated_client: AsyncClient):
    """Public gallery item detail is available without auth and increments views."""
    created = await authenticated_client.post("/api/gallery/", json={
        "title": "Reusable prompt",
        "description": "A prompt worth reusing",
        "media_type": "image",
        "media_url": "https://example.com/reusable.png",
        "prompt": "cinematic robot portrait",
        "style": "cinematic",
        "tags": ["robot", "portrait"],
        "is_public": True,
    })
    assert created.status_code == 201
    item_id = created.json()["id"]

    resp = await client.get(f"/api/gallery/{item_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == item_id
    assert data["title"] == "Reusable prompt"
    assert data["prompt"] == "cinematic robot portrait"
    assert data["style"] == "cinematic"
    assert data["views"] == 1
