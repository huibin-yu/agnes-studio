"""Schema Definitions for Video Generation - Based on official Agnes AI docs"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Valid frame counts (must be 8n+1 and <= 441)
VALID_FRAME_COUNTS = [81, 121, 161, 241, 441]

# Valid frame rates (1-60)
VALID_FRAME_RATES = [16, 24, 30, 60]

# Video model from official documentation
VIDEO_MODEL = "agnes-video-v2.0"


class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Generation prompt")
    image: Optional[str] = Field(None, description="Input image URL for image-to-video")
    model: str = Field("agnes-video-v2.0", description="Model to use")
    num_frames: int = Field(121, description="Number of frames (must be 8n+1, max 441)")
    frame_rate: int = Field(24, ge=1, le=60, description="Frame rate (1-60)")
    width: int = Field(1152, description="Width")
    height: int = Field(768, description="Height")
    mode: str = Field("ti2vid", description="Generation mode (ti2vid or keyframes)")
    extra_images: Optional[List[str]] = Field(None, description="Extra images for multi-image mode")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "prompt": "A young astronaut walking across a red desert planet, dust blowing in the wind",
                    "num_frames": 121,
                    "frame_rate": 24,
                    "mode": "ti2vid",
                }
            ]
        }

    @property
    def duration_seconds(self) -> float:
        return self.num_frames / self.frame_rate


class VideoGenerateResponse(BaseModel):
    id: int
    task_id: str
    video_id: str
    status: str
    progress: int
    prompt: str
    estimated_time: int = 300
    video_url: Optional[str] = None
    num_frames: Optional[int] = None
    frame_rate: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    credits_charged: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class VideoDetailResponse(VideoGenerateResponse):
    video_url: Optional[str] = None
    duration: float
    width: int
    height: int
    num_frames: int
    frame_rate: int
    error_message: Optional[str] = None
    model_name: Optional[str] = None


class VideoPollResponse(BaseModel):
    status: str
    progress: int
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    model_name: Optional[str] = None


class VideoListResponse(BaseModel):
    items: List[VideoGenerateResponse]
    total: int
    page: int
    per_page: int
