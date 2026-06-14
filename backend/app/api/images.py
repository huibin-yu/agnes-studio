"""Image Generation API Routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    ImageDetailResponse,
    ImageSizeOption,
    ImageListResponse,
    IMAGE_SIZES,
    IMAGE_STYLES,
)
from app.models.user import User
from app.models.image import ImageGeneration
from app.services.image_service import image_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/styles", response_model=list)
async def get_styles():
    """Get available image styles"""
    return [{"value": s[0], "label": s[1]} for s in IMAGE_STYLES]


@router.get("/sizes", response_model=list[ImageSizeOption])
async def get_sizes():
    """Get available image sizes"""
    return IMAGE_SIZES


@router.post("/generate", response_model=ImageGenerateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_GENERATE)
async def generate_image(
    request: Request,
    data: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an image using Agnes AI"""
    try:
        image = await image_service.generate(db, current_user.id, data.model_dump())
        logger.info(f"Image generated for user {current_user.id}, image_id={image.id}")
        return image
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Image generation failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image generation failed. Please try again later."
        )


@router.get("/my", response_model=ImageListResponse)
async def get_my_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's image history with pagination"""
    images, total = await image_service.get_user_images(db, current_user.id, page, per_page)
    return ImageListResponse(
        items=images,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{image_id}", response_model=ImageGenerateResponse)
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get image by ID"""
    image = await image_service.get_by_id(db, image_id, current_user.id)
    return image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an image"""
    result = await db.execute(
        delete(ImageGeneration).where(
            ImageGeneration.id == image_id,
            ImageGeneration.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    await db.commit()
    logger.info(f"Image {image_id} deleted by user {current_user.id}")
