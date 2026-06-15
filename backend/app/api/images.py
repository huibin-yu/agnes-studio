"""Image Generation API Routes"""
import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File
from fastapi.responses import JSONResponse
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
    ImageToImageRequest,
    IMAGE_SIZES,
    IMAGE_STYLES,
)
from app.models.user import User
from app.models.image import ImageGeneration
from app.services.image_service import image_service
from app.services.agnes_ai import agnes_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Image upload constraints
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_REFERENCE_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


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


@router.post("/upload-reference")
async def upload_reference_image(
    current_user: User = Depends(get_current_user),
    image: UploadFile = File(...),
):
    """Upload a reference image for image-to-image generation"""
    # Validate content type
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type. Allowed: JPEG, PNG, GIF, WebP",
        )

    content = await image.read()

    # Validate size
    if len(content) > MAX_REFERENCE_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large (max 10MB)",
        )

    # Validate magic bytes
    is_valid = (
        content[:3] == b'\xff\xd8\xff' or       # JPEG
        content[:8] == b'\x89PNG\r\n\x1a\n' or  # PNG
        content[:4] == b'GIF8' or                # GIF
        (content[:4] == b'RIFF' and content[8:12] == b'WEBP')  # WebP
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Determine extension
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    ext = ext_map.get(image.content_type, ".jpg")

    # Save to uploads/references/
    upload_dir = Path(settings.UPLOAD_DIR) / "references"
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = upload_dir / filename
    filepath.write_bytes(content)

    # Build URL that Agnes AI API can access
    base_url = settings.BASE_URL.rstrip("/")
    image_url = f"{base_url}/uploads/references/{filename}"

    logger.info(f"Reference image uploaded by user {current_user.id}: {filename}")
    return {"image_url": image_url, "filename": filename}


@router.post("/img2img", response_model=ImageGenerateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_GENERATE)
async def generate_image_to_image(
    request: Request,
    data: ImageToImageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an image based on a reference image + prompt (image-to-image)"""
    try:
        result = await image_service.generate_img2img(db, current_user.id, data.model_dump())
        logger.info(f"Image-to-image generated for user {current_user.id}, image_id={result.id}")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Image-to-image failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image-to-image generation failed. Please try again later.",
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
