"""Image Generation Service"""
import logging
import os
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.image import ImageGeneration
from app.models.user import User
from app.services.agnes_ai import agnes_service

logger = logging.getLogger(__name__)


class ImageService:
    async def generate(self, db: AsyncSession, user_id: int, data: Dict) -> ImageGeneration:
        # Check credits
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.credits < settings.IMAGE_COST:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits. Please recharge."
            )

        # Call Agnes AI
        try:
            agnes_response = await agnes_service.generate_image(
                prompt=data["prompt"],
                model=data.get("model", "agnes-image-2.1-flash"),
                size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
                negative_prompt=data.get("negative_prompt", ""),
                style=data.get("style", "none"),
            )
        except Exception as e:
            logger.error(f"Image generation service error for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image generation service is temporarily unavailable. Please try again later."
            )

        # Save to DB
        image_url = agnes_response.get("image_url", "")

        image_gen = ImageGeneration(
            user_id=user_id,
            prompt=data["prompt"],
            negative_prompt=data.get("negative_prompt", ""),
            model=data.get("model", "agnes-image-2.1-flash"),
            size=data.get("size", settings.IMAGE_DEFAULT_SIZE),
            style=data.get("style", "none"),
            image_url=image_url,
            status="completed" if image_url else "failed",
            parameters=data,
        )

        if not image_url:
            image_gen.error_message = "Image generation returned no result"

        db.add(image_gen)

        # Only charge on success
        if image_url:
            user.credits -= settings.IMAGE_COST

        await db.commit()
        await db.refresh(image_gen)
        logger.info(
            f"Image {image_gen.id} generated for user {user_id}, "
            f"status={image_gen.status}, credits remaining: {user.credits}"
        )
        return image_gen

    async def get_by_id(self, db: AsyncSession, image_id: int, user_id: int) -> ImageGeneration:
        result = await db.execute(
            select(ImageGeneration).where(
                ImageGeneration.id == image_id,
                ImageGeneration.user_id == user_id
            )
        )
        image = result.scalar_one_or_none()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return image

    async def get_user_images(
        self, db: AsyncSession, user_id: int, page: int = 1, per_page: int = 20
    ):
        offset = (page - 1) * per_page
        result = await db.execute(
            select(ImageGeneration)
            .where(ImageGeneration.user_id == user_id)
            .order_by(ImageGeneration.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        images = result.scalars().all()

        count_result = await db.execute(
            select(func.count(ImageGeneration.id)).where(ImageGeneration.user_id == user_id)
        )
        total = count_result.scalar() or 0

        return images, total


image_service = ImageService()
