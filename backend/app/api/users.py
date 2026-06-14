"""User Profile API Routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pathlib import Path

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.auth import UserResponse, CreditResponse
from app.models.user import User
from app.models.image import ImageGeneration
from app.models.video import VideoGeneration
from app.core.config import settings
from app.utils.helpers import sanitize_filename

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed image MIME types and max size (5MB)
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return current_user


@router.put("/profile")
async def update_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    avatar: UploadFile = File(None),
):
    """Update user profile"""
    if avatar:
        # Validate MIME type by content, not header
        content = await avatar.read()
        if len(content) > MAX_AVATAR_SIZE:
            raise HTTPException(status_code=413, detail="Avatar file too large (max 5MB)")

        # Check magic bytes for common image formats
        is_valid_image = (
            content[:3] == b'\xff\xd8\xff' or  # JPEG
            content[:8] == b'\x89PNG\r\n\x1a\n' or  # PNG
            content[:4] == b'GIF8' or  # GIF
            content[:4] == b'RIFF' and content[8:12] == b'WEBP'  # WebP
        )
        if not is_valid_image:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Save avatar with sanitized filename
        upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = sanitize_filename(avatar.filename or "avatar.jpg")
        avatar_path = upload_dir / f"{current_user.id}_{safe_name}"
        avatar_path.write_bytes(content)

        current_user.avatar_url = f"/uploads/avatars/{safe_name}"

    await db.commit()
    await db.refresh(current_user)
    logger.info(f"Profile updated for user {current_user.id}")
    return current_user


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user statistics"""
    image_count_result = await db.execute(
        select(func.count(ImageGeneration.id)).where(ImageGeneration.user_id == current_user.id)
    )
    video_count_result = await db.execute(
        select(func.count(VideoGeneration.id)).where(VideoGeneration.user_id == current_user.id)
    )

    return {
        "credits": current_user.credits,
        "total_images": image_count_result.scalar() or 0,
        "total_videos": video_count_result.scalar() or 0,
    }
