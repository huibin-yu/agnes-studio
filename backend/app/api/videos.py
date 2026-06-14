"""Video Generation API Routes - Based on official Agnes AI documentation"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, select
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.video import VideoGenerateRequest, VideoGenerateResponse, VideoDetailResponse, VideoPollResponse
from app.models.user import User
from app.models.video import VideoGeneration
from app.services.video_service import video_service
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/generate", response_model=VideoGenerateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_GENERATE)
async def generate_video(
    request: Request,
    data: VideoGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a video using Agnes AI"""
    try:
        video = await video_service.create_video(
            db=db,
            user_id=current_user.id,
            prompt=data.prompt,
            num_frames=data.num_frames,
            frame_rate=data.frame_rate,
            mode=data.mode,
            image=data.image,
            extra_images=data.extra_images,
            width=data.width,
            height=data.height,
            negative_prompt=data.negative_prompt
        )
        logger.info(f"Video generated for user {current_user.id}, video_id={video.id}")
        return video
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Video generation failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Video generation failed. Please try again later."
        )


@router.get("/my", response_model=list[VideoGenerateResponse])
async def get_my_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's video history"""
    videos, total = await video_service.get_user_videos(db, current_user.id, page, per_page)
    return videos


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get video by ID"""
    video = await video_service.get_video_by_id(db, video_id, current_user.id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/poll", response_model=VideoPollResponse)
async def poll_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll video generation status"""
    try:
        # Find video generation record
        result = await db.execute(
            select(VideoGeneration).where(
                VideoGeneration.id == video_id,
                VideoGeneration.user_id == current_user.id,
            )
        )
        video_gen = result.scalar_one_or_none()

        if not video_gen:
            raise HTTPException(status_code=404, detail="Video not found")

        # Poll using video_id
        status_result = await video_service.poll_video_status(
            db, video_gen.video_id, current_user.id
        )

        return VideoPollResponse(
            status=status_result.get("status"),
            progress=status_result.get("progress"),
            video_url=status_result.get("video_url"),
            error_message=status_result.get("error_message")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Video polling failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to poll video status. Please try again later."
        )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a video"""
    result = await db.execute(
        delete(VideoGeneration).where(
            VideoGeneration.id == video_id,
            VideoGeneration.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    await db.commit()
    logger.info(f"Video {video_id} deleted by user {current_user.id}")
