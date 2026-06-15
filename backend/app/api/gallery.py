"""Gallery API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user, get_current_user_optional
from app.schemas.gallery import (
    GalleryCreateRequest,
    GalleryItemResponse,
    GalleryListResponse,
    GallerySearchRequest,
)
from app.models.user import User
from app.models.gallery import GalleryItem
from app.services.gallery_service import gallery_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/public", response_model=GalleryListResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_public_gallery(
    request: Request,
    query: Optional[str] = None,
    style: Optional[str] = None,
    tags: Optional[str] = None,
    sort: str = Query("newest", pattern="^(newest|popular|trending)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get public gallery (auth optional, used for is_liked)"""
    tag_list = tags.split(",") if tags else None
    viewer_id = current_user.id if current_user else None
    items, total, liked_ids = await gallery_service.get_public_gallery(
        db, page=page, per_page=per_page,
        query=query, style=style, tags=tag_list, sort=sort,
        viewer_id=viewer_id,
    )
    # Build response with is_liked field
    response_items = []
    for item in items:
        item_data = GalleryItemResponse.model_validate(item)
        item_data.is_liked = item.id in liked_ids
        response_items.append(item_data)
    return {
        "items": response_items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/", response_model=GalleryItemResponse, status_code=201)
async def create_gallery_item(
    data: GalleryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add item to gallery"""
    item = await gallery_service.create_item(db, current_user.id, data.model_dump())
    return item


@router.get("/my", response_model=GalleryListResponse)
async def get_my_gallery(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's gallery"""
    items, total = await gallery_service.get_user_gallery(db, current_user.id, page, per_page)
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/{item_id}/like")
async def toggle_like_gallery_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a gallery item (idempotent: clicking again unlikes)"""
    item, is_liked = await gallery_service.toggle_like(db, item_id, current_user.id)
    return {"likes": item.likes, "is_liked": is_liked}


@router.delete("/{item_id}", status_code=204)
async def delete_gallery_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a gallery item"""
    await gallery_service.delete_item(db, item_id, current_user.id)


@router.get("/search", response_model=GalleryListResponse)
async def search_gallery(
    q: Optional[str] = None,
    style: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Search gallery items"""
    viewer_id = current_user.id if current_user else None
    items, total, liked_ids = await gallery_service.get_public_gallery(
        db, query=q, style=style,
        page=page, per_page=per_page, sort="newest",
        viewer_id=viewer_id,
    )
    response_items = []
    for item in items:
        item_data = GalleryItemResponse.model_validate(item)
        item_data.is_liked = item.id in liked_ids
        response_items.append(item_data)
    return {
        "items": response_items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{item_id}", response_model=GalleryItemResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_gallery_item(
    request: Request,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get public gallery item detail"""
    viewer_id = current_user.id if current_user else None
    item, is_liked = await gallery_service.get_public_item(db, item_id, viewer_id=viewer_id)
    item_data = GalleryItemResponse.model_validate(item)
    item_data.is_liked = is_liked
    return item_data
