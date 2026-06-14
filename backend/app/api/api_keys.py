"""API Key Management Routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.api_key import (
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeyListItem,
    ApiKeyListResponse,
)
from app.models.user import User
from app.models.api_key import ApiKey
from app.services.api_key_service import api_key_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key. The full key is only returned in this response."""
    key = await api_key_service.create_key(db, current_user.id, data.model_dump())
    logger.info(f"API key created for user {current_user.id}: {key.key[:8]}...")
    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        key=key.key,  # Only shown once at creation
        is_active=key.is_active,
        rate_limit=key.rate_limit,
        daily_limit=key.daily_limit,
        expires_at=key.expires_at,
        created_at=key.created_at,
    )


@router.get("/", response_model=ApiKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for current user (keys are masked)"""
    keys = await api_key_service.get_user_keys(db, current_user.id)
    items = [
        ApiKeyListItem(
            id=k.id,
            name=k.name,
            key_prefix=f"{k.key[:12]}..." if len(k.key) > 12 else k.key,
            is_active=k.is_active,
            rate_limit=k.rate_limit,
            daily_limit=k.daily_limit,
            expires_at=k.expires_at,
            created_at=k.created_at,
        )
        for k in keys
    ]
    return {
        "items": items,
        "total": len(items),
    }


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key"""
    await api_key_service.revoke_key(db, key_id, current_user.id)
    logger.info(f"API key {key_id} revoked by user {current_user.id}")
