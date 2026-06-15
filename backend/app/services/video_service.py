"""Video Service - Handles video generation based on official Agnes AI documentation"""
import logging
import time
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import async_session
from app.schemas.video import VALID_FRAME_COUNTS, VALID_FRAME_RATES
from app.services.agnes_ai import agnes_service
from app.models.video import VideoGeneration
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class VideoService:
    """Service for video generation workflow"""

    async def create_video(self, db: AsyncSession, user_id: int,
                          prompt: str, num_frames: int = 121,
                          frame_rate: int = 24, mode: str = "ti2vid",
                          image: str = None, extra_images: list = None,
                          width: int = 1152, height: int = 768,
                          negative_prompt: str = None) -> Dict:
        """
        Create a video generation task

        Args:
            db: Database session
            user_id: User ID
            prompt: Video prompt
            num_frames: Number of frames (8n+1, max 441)
            frame_rate: Frame rate (1-60)
            mode: Generation mode
            image: Input image URL for image-to-video
            extra_images: Additional images for multi-image mode
            width: Video width
            height: Video height
            negative_prompt: Negative prompt

        Returns:
            Dict with video generation info
        """
        # Validate frame count
        if num_frames not in VALID_FRAME_COUNTS:
            raise ValueError(f"Invalid num_frames: {num_frames}. Must be one of {VALID_FRAME_COUNTS}")

        # Validate frame rate
        if frame_rate not in VALID_FRAME_RATES:
            raise ValueError(f"Invalid frame_rate: {frame_rate}. Must be one of {VALID_FRAME_RATES}")

        # Create database record
        video_gen = VideoGeneration(
            user_id=user_id,
            prompt=prompt,
            num_frames=num_frames,
            frame_rate=frame_rate,
            width=width,
            height=height,
            status="queued",
            progress=0
        )
        db.add(video_gen)
        await db.commit()
        await db.refresh(video_gen)

        # Prepare extra_body for multi-image/keyframes mode
        extra_body = {}
        if extra_images and len(extra_images) > 0:
            extra_body["image"] = extra_images
            if mode == "keyframes":
                extra_body["mode"] = "keyframes"

        # Call Agnes AI API to create video task
        try:
            api_response = await agnes_service.create_video_task(
                prompt=prompt,
                mode=mode,
                image=image,
                extra_body=extra_body if extra_body else None,
                num_frames=num_frames,
                frame_rate=frame_rate,
                height=height,
                width=width,
                negative_prompt=negative_prompt
            )

            # Store task info
            video_gen.task_id = api_response.get("id") or api_response.get("task_id")
            video_gen.video_id = api_response.get("video_id")
            video_gen.status = api_response.get("status", "queued")
            video_gen.progress = api_response.get("progress", 0)

            await db.commit()
            logger.info(f"Video task created for user {user_id}, video_id={video_gen.video_id}")

            return {
                "id": video_gen.id,
                "task_id": video_gen.task_id,
                "video_id": video_gen.video_id,
                "status": video_gen.status,
                "progress": video_gen.progress,
                "prompt": prompt,
                "estimated_time": 300,  # 5 minutes estimate
                "video_url": video_gen.video_url,
                "num_frames": video_gen.num_frames,
                "frame_rate": video_gen.frame_rate,
                "width": video_gen.width,
                "height": video_gen.height,
                "created_at": video_gen.created_at,
            }
        except Exception as e:
            video_gen.status = "failed"
            video_gen.error_message = "Video task creation failed"
            await db.commit()
            logger.error(f"Failed to create video task for user {user_id}: {e}")
            raise Exception("Failed to create video task. Please try again later.")

    async def poll_video_status(self, db: AsyncSession, video_id: str,
                               user_id: int = None) -> Dict:
        """
        Poll video generation status using video_id (RECOMMENDED method)

        Args:
            db: Database session
            video_id: Video ID to poll
            user_id: Optional user ID for permission check

        Returns:
            Dict with video status and result
        """
        # Find video generation record
        result = await db.execute(
            select(VideoGeneration).where(VideoGeneration.video_id == video_id)
        )
        video_gen = result.scalar_one_or_none()

        if not video_gen:
            raise ValueError(f"Video not found: {video_id}")

        # Call Agnes AI API to poll status
        try:
            api_response = await agnes_service.poll_video_status(video_id)

            # Update database record
            video_gen.status = api_response.get("status")
            video_gen.progress = api_response.get("progress", 0)
            video_gen.model_name = api_response.get("model")

            # Update video URL if completed
            if api_response.get("status") == "completed":
                video_gen.video_url = api_response.get("remixed_from_video_id")
                video_gen.expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            # Handle failure
            if api_response.get("status") == "failed":
                video_gen.error_message = api_response.get("error", {}).get("message", "Unknown error")

            await db.commit()

            return {
                "status": api_response.get("status"),
                "progress": api_response.get("progress", 0),
                "video_url": api_response.get("remixed_from_video_id") if api_response.get("status") == "completed" else None,
                "error_message": api_response.get("error", {}).get("message") if api_response.get("status") == "failed" else None,
                "seconds": api_response.get("seconds"),
                "size": api_response.get("size")
            }
        except Exception as e:
            logger.error(f"Failed to poll video status for {video_id}: {e}")
            raise Exception("Failed to poll video status. Please try again later.")

    async def get_video_by_id(self, db: AsyncSession, video_id: int,
                             user_id: int = None) -> VideoGeneration:
        """Get video generation record by ID"""
        query = select(VideoGeneration).where(VideoGeneration.id == video_id)

        if user_id:
            query = query.where(VideoGeneration.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_videos(self, db: AsyncSession, user_id: int,
                             page: int = 1, per_page: int = 20) -> tuple:
        """Get user's video history"""
        # Get total count
        count_result = await db.execute(
            select(func.count(VideoGeneration.id)).where(
                VideoGeneration.user_id == user_id
            )
        )
        total = count_result.scalar() or 0

        # Get page data
        offset = (page - 1) * per_page
        result = await db.execute(
            select(VideoGeneration)
            .where(VideoGeneration.user_id == user_id)
            .order_by(VideoGeneration.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        videos = result.scalars().all()

        return videos, total


# Global instance
video_service = VideoService()
