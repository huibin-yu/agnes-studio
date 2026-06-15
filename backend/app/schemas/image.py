"""Schema Definitions for Image Generation - Based on official Agnes AI docs"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Valid image sizes from official documentation
VALID_IMAGE_SIZES = [
    "1024x768",   # Standard (4:3)
    "1024x1024",  # Square (1:1)
    "768x1024",   # Portrait (3:4)
    "2048x2048",  # 2K Square (1:1)
    "4096x4096",  # 4K Square (1:1)
    "1816x1024",  # Wide (16:9)
    "1024x1816",  # Tall (9:16)
]

# Valid image models from official documentation
VALID_IMAGE_MODELS = [
    "agnes-image-2.1-flash",  # Recommended (better high-density details)
    "agnes-image-2.0-flash",  # Fast generation
]

# Style presets for image generation
IMAGE_STYLES = [
    ("none", "No Style"),
    ("cinematic", "Cinematic"),
    ("anime", "Anime"),
    ("realistic", "Photorealistic"),
    ("digital-art", "Digital Art"),
    ("oil-painting", "Oil Painting"),
    ("watercolor", "Watercolor"),
    ("pixel-art", "Pixel Art"),
    ("3d-render", "3D Render"),
    ("fantasy", "Fantasy"),
    ("scifi", "Sci-Fi"),
    ("horror", "Horror"),
    ("minimalist", "Minimalist"),
    ("pop-art", "Pop Art"),
    ("comic", "Comic"),
]


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Generation prompt")
    negative_prompt: Optional[str] = Field(None, max_length=1000, description="Negative prompt")
    model: str = Field("agnes-image-2.1-flash", description="Model to use")
    size: str = Field("1024x768", description="Image size (e.g., '1024x768')")
    style: str = Field("none", description="Style preset")
    seed: Optional[int] = Field(None, ge=-1, le=2**32-1, description="Random seed")
    return_base64: bool = Field(False, description="Return base64 instead of URL")


class ImageGenerateResponse(BaseModel):
    id: int
    prompt: str
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    status: str
    seed: Optional[int]
    size: str
    style: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ImageDetailResponse(ImageGenerateResponse):
    negative_prompt: Optional[str] = None
    model: str
    style: str
    revised_prompt: Optional[str] = None


class ImageSizeOption(BaseModel):
    id: str
    label: str
    ratio: str


IMAGE_SIZE_OPTIONS = [
    ImageSizeOption(id="1024x768", label="1024×768 (Standard)", ratio="4:3"),
    ImageSizeOption(id="1024x1024", label="1024×1024 (Square)", ratio="1:1"),
    ImageSizeOption(id="768x1024", label="768×1024 (Portrait)", ratio="3:4"),
    ImageSizeOption(id="2048x2048", label="2048×2048 (2K)", ratio="1:1"),
    ImageSizeOption(id="4096x4096", label="4096×4096 (4K)", ratio="1:1"),
    ImageSizeOption(id="1816x1024", label="1816×1024 (Wide)", ratio="16:9"),
    ImageSizeOption(id="1024x1816", label="1024×1816 (Tall)", ratio="9:16"),
]

IMAGE_SIZES = IMAGE_SIZE_OPTIONS


class ImageListResponse(BaseModel):
    items: List[ImageGenerateResponse]
    total: int
    page: int
    per_page: int


# Image-to-image schema
class ImageToImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Editing instruction")
    image_url: str = Field(..., description="URL of input image")
    model: str = Field("agnes-image-2.1-flash", description="Model to use")
    size: str = Field("1024x768", description="Output image size")
    return_base64: bool = Field(False, description="Return base64 instead of URL")


# Gallery schema
class GalleryItem(BaseModel):
    id: int
    type: str  # "image" or "video"
    prompt: str
    media_url: str
    style: Optional[str] = None
    created_at: datetime
    user_id: int
    username: Optional[str] = None
    likes_count: int = 0
    is_liked: bool = False


class GalleryListResponse(BaseModel):
    items: List[GalleryItem]
    total: int
    page: int
    per_page: int
