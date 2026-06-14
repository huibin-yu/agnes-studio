"""Auth Service"""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        pass

    async def register(self, db: AsyncSession, data: UserRegister) -> User:
        # Check if user already exists
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

        # Generate referral code
        referral_code = f"REF{secrets.token_hex(4).upper()}"

        # Create user
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
            referral_code=referral_code,
            credits=settings.FREE_CREDITS_ON_REGISTER,
        )

        # Handle referral
        if data.referral_code:
            result = await db.execute(
                select(User).where(User.referral_code == data.referral_code)
            )
            referrer = result.scalar_one_or_none()
            if referrer:
                user.referred_by = referrer.id
                referrer.credits += settings.REFERRAL_BONUS

        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"User registered: {user.email} (id={user.id})")
        return user

    async def login(self, db: AsyncSession, data: UserLogin):
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            logger.warning(f"Login attempt on disabled account: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        access_token = create_access_token(data={"sub": str(user.id)}, token_version=user.token_version)
        refresh_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)

        logger.info(f"User logged in: {user.email} (id={user.id})")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    async def refresh_tokens(self, db: AsyncSession, refresh_token: str):
        from jose import jwt, JWTError

        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            token_type = payload.get("type")
            token_version = payload.get("tv")

            if user_id is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Check token version - invalidate if password was changed
        if token_version is not None and token_version != user.token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired due to password change"
            )

        access_token = create_access_token(data={"sub": str(user.id)}, token_version=user.token_version)
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    async def change_password(
        self, db: AsyncSession, user_id: int, old_password: str, new_password: str
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Incorrect old password"
            )

        user.hashed_password = get_password_hash(new_password)
        user.token_version += 1  # Invalidate all existing tokens
        await db.commit()
        logger.info(f"Password changed for user {user_id}, token_version incremented to {user.token_version}")


auth_service = AuthService()
