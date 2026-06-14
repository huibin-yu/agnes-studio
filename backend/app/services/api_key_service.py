"""API Key Service"""
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.api_key import ApiKey
from app.models.user import User


class ApiKeyService:
    async def create_key(self, db: AsyncSession, user_id: int, data: Dict) -> ApiKey:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        key = ApiKey(
            user_id=user_id,
            name=data["name"],
            rate_limit=data.get("rate_limit", 10),
            daily_limit=data.get("daily_limit", 100),
            expires_at=data.get("expires_at"),
        )
        key.key = ApiKey.generate_key()

        db.add(key)
        await db.commit()
        await db.refresh(key)
        return key

    async def get_key(self, db: AsyncSession, api_key: str) -> ApiKey:
        result = await db.execute(select(ApiKey).where(ApiKey.key == api_key))
        key = result.scalar_one_or_none()
        if not key or not key.is_active:
            return None

        # Check expiry
        if key.expires_at and key.expires_at < datetime.now(timezone.utc):
            key.is_active = False
            await db.commit()
            return None

        return key

    async def get_user_keys(self, db: AsyncSession, user_id: int):
        result = await db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        )
        return result.scalars().all()

    async def revoke_key(self, db: AsyncSession, key_id: int, user_id: int) -> ApiKey:
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        )
        key = result.scalar_one_or_none()
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found")

        key.is_active = False
        await db.commit()
        return key


api_key_service = ApiKeyService()
