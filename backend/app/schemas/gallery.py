"""Schema Definitions for Gallery"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GalleryCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field("", max_length=1000)
    media_type: str = Field(..., pattern="^(image|video)$")
    media_url: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    style: Optional[str] = Field("")
    tags: Optional[List[str]] = Field(default_factory=list, max_items=20)
    is_public: bool = True


class GalleryItemResponse(BaseModel):
    id: int
    title: str
    description: str
    media_type: str
    media_url: str
    prompt: str
    style: str
    tags: List[str]
    is_public: bool
    likes: int
    views: int
    is_liked: bool = False
    user: "GalleryUser"
    created_at: datetime

    class Config:
        from_attributes = True


class GalleryUser(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None


class GalleryListResponse(BaseModel):
    items: List[GalleryItemResponse]
    total: int
    page: int
    per_page: int


class GallerySearchRequest(BaseModel):
    query: Optional[str] = None
    style: Optional[str] = None
    tags: Optional[List[str]] = None
    sort: str = Field("newest", pattern="^(newest|popular|trending)$")
    page: int = 1
    per_page: int = 20
