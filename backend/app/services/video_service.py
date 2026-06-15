"""Video Service - Handles video generation based on official Agnes AI documentation"""
import logging
import math
import time
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status as http_status
from app.core.config import settings
from app.core.database import async_session
from app.schemas.video import VALID_FRAME_COUNTS, VALID_FRAME_RATES
from app.services.agnes_ai import agnes_service
from app.models.user import User
from app.models.video import VideoGeneration
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def _extract_video_url(payload: dict) -> Optional[str]:
    """Extract a video URL from upstream payload across known shapes.

    Returns None if no plausible URL is found. Pure function, no IO.
    """
    def _is_url(v):
        return isinstance(v, str) and v.startswith(("http://", "https://"))

    if not isinstance(payload, dict):
        return None

    for key in ("video_url", "url", "download_url", "output_url"):
        v = payload.get(key)
        if _is_url(v):
            return v

    output = payload.get("output")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            for key in ("video_url", "url", "download_url"):
                v = first.get(key)
                if _is_url(v):
                    return v
        elif _is_url(first):
            return first
    elif isinstance(output, dict):
        for key in ("video_url", "url", "download_url"):
            v = output.get(key)
            if _is_url(v):
                return v

    data = payload.get("data")
    if isinstance(data, dict):
        return _extract_video_url(data)

    return None


class VideoService:
    """Service for video generation workflow"""

    async def create_video(self, db: AsyncSession, user_id: int,
                          prompt: str, num_frames: int = 121,
                          frame_rate: int = 24, mode: str = "ti2vid",
                          image: str = None, extra_images: list = None,
                          width: int = 1152, height: int = 768,
                          negative_prompt: str = None) -> Dict:
        # Validate frame count
        if num_frames not in VALID_FRAME_COUNTS:
            raise ValueError(f"Invalid num_frames: {num_frames}. Must be one of {VALID_FRAME_COUNTS}")

        # Validate frame rate
        if frame_rate not in VALID_FRAME_RATES:
            raise ValueError(f"Invalid frame_rate: {frame_rate}. Must be one of {VALID_FRAME_RATES}")

        # Calculate cost (ceil duration * per-second rate)
        duration = num_frames / frame_rate
        cost = math.ceil(duration * settings.VIDEO_COST_PER_SECOND)

        # Load user and check balance
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.credits < cost:
            raise HTTPException(
                status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits. Please recharge.",
            )

        # Create database record (queued)
        video_gen = VideoGeneration(
            user_id=user_id,
            prompt=prompt,
            num_frames=num_frames,
            frame_rate=frame_rate,
            width=width,
            height=height,
            status="queued",
            progress=0,
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
                negative_prompt=negative_prompt,
            )
        except Exception as e:
            video_gen.status = "failed"
            video_gen.error_message = "Video task creation failed"
            await db.commit()
            logger.error(f"Failed to create video task for user {user_id}: {e}")
            raise Exception("Failed to create video task. Please try again later.")

        # Upstream succeeded -> charge credits via ledger
        video_gen.task_id = api_response.get("id") or api_response.get("task_id")
        video_gen.video_id = api_response.get("video_id")
        video_gen.status = api_response.get("status", "queued")
        video_gen.progress = api_response.get("progress", 0)

        from app.services.credit_service import credit_service, InsufficientCreditsError
        from app.models.credit_transaction import TX_VIDEO_GENERATE

        try:
            await credit_service.charge(
                db, user_id, cost,
                type=TX_VIDEO_GENERATE,
                ref_type="video", ref_id=video_gen.id,
            )
        except InsufficientCreditsError:
            await db.rollback()
            logger.error(
                f"Race: insufficient credits for user {user_id} after upstream "
                f"created video task. video_id={video_gen.video_id}"
            )
            raise HTTPException(
                status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits at charge time. Please retry.",
            )
        video_gen.credits_charged = cost
        await db.commit()
        await db.refresh(video_gen)

        logger.info(
            f"Video task created for user {user_id}, video_id={video_gen.video_id}, "
            f"charged {cost} credits, balance: {user.credits}"
        )

        return {
            "id": video_gen.id,
            "task_id": video_gen.task_id,
            "video_id": video_gen.video_id,
            "status": video_gen.status,
            "progress": video_gen.progress,
            "prompt": prompt,
            "estimated_time": 300,
            "video_url": video_gen.video_url,
            "num_frames": video_gen.num_frames,
            "frame_rate": video_gen.frame_rate,
            "width": video_gen.width,
            "height": video_gen.height,
            "credits_charged": video_gen.credits_charged,
            "created_at": video_gen.created_at,
        }

    async def poll_video_status(
        self, db: AsyncSession, video_id: str, user_id: int = None,
    ) -> Dict:
        """Poll video generation status.

        - 强制 user_id 校验：找不到记录或不属于该用户都返回 404。
        - 成功时按 fallback 顺序提取 video URL；提取失败按"完成但无 URL"处理并退款。
        - 失败时退款一次（防重入：credits_charged > 0 才退）。
        """
        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id is required")

        result = await db.execute(
            select(VideoGeneration).where(
                VideoGeneration.video_id == video_id,
                VideoGeneration.user_id == user_id,
            )
        )
        video_gen = result.scalar_one_or_none()
        if not video_gen:
            raise HTTPException(status_code=404, detail="Video not found")

        try:
            api_response = await agnes_service.poll_video_status(video_id)
        except Exception as e:
            logger.error(f"Failed to poll video status for {video_id}: {e}")
            raise Exception("Failed to poll video status. Please try again later.")

        upstream_status = api_response.get("status")
        progress = api_response.get("progress", 0)

        from app.services.credit_service import credit_service
        from app.models.credit_transaction import TX_VIDEO_REFUND

        async def _refund_if_needed(reason: str):
            if video_gen.credits_charged and video_gen.credits_charged > 0:
                await credit_service.grant(
                    db, video_gen.user_id, video_gen.credits_charged,
                    type=TX_VIDEO_REFUND,
                    ref_type="video", ref_id=video_gen.id,
                    note=reason,
                )
                video_gen.credits_charged = 0

        video_gen.progress = progress

        error_message = None
        if upstream_status == "completed":
            url = _extract_video_url(api_response)
            if url:
                video_gen.video_url = url
                video_gen.status = "completed"
                video_gen.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            else:
                logger.error(
                    f"Video {video_gen.id} marked completed but URL missing. "
                    f"Response: {str(api_response)[:500]}"
                )
                video_gen.status = "failed"
                video_gen.error_message = "Upstream completed but no video URL"
                error_message = video_gen.error_message
                await _refund_if_needed("completed_no_url")
                upstream_status = "failed"
        elif upstream_status == "failed":
            err = api_response.get("error") or {}
            video_gen.status = "failed"
            video_gen.error_message = err.get("message", "Unknown error") if isinstance(err, dict) else str(err)
            error_message = video_gen.error_message
            await _refund_if_needed("generation_failed")
        else:
            video_gen.status = upstream_status or video_gen.status

        await db.commit()

        return {
            "status": upstream_status,
            "progress": progress,
            "video_url": video_gen.video_url if upstream_status == "completed" else None,
            "error_message": error_message,
            "seconds": api_response.get("seconds"),
            "size": api_response.get("size"),
        }

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
