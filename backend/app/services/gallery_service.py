"""Gallery Service"""
import logging
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, literal_column
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.gallery import GalleryItem
from app.models.user import User

logger = logging.getLogger(__name__)


def escape_like_pattern(query: str) -> str:
    """Escape LIKE metacharacters to prevent wildcard injection"""
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class GalleryService:
    async def create_item(
        self, db: AsyncSession, user_id: int, data: Dict
    ) -> GalleryItem:
        item = GalleryItem(
            user_id=user_id,
            title=data["title"],
            description=data.get("description", ""),
            media_type=data["media_type"],
            media_url=data["media_url"],
            prompt=data["prompt"],
            style=data.get("style", ""),
            tags=data.get("tags", []),
            is_public=data.get("is_public", True),
        )

        db.add(item)
        await db.commit()
        await db.refresh(item)
        logger.info(f"Gallery item {item.id} created by user {user_id}")
        return item

    async def get_public_gallery(
        self, db: AsyncSession, page: int = 1, per_page: int = 20,
        query: Optional[str] = None, style: Optional[str] = None,
        tags: Optional[List[str]] = None, sort: str = "newest"
    ):
        q = select(GalleryItem).options(
            joinedload(GalleryItem.user)
        ).where(GalleryItem.is_public == True)

        if query:
            escaped = escape_like_pattern(query)
            q = q.where(
                GalleryItem.title.ilike(f"%{escaped}%", escape="\\") |
                GalleryItem.prompt.ilike(f"%{escaped}%", escape="\\")
            )

        if style:
            q = q.where(GalleryItem.style == style)

        if tags:
            for tag in tags:
                q = q.where(GalleryItem.tags.contains([tag]))

        # Sorting
        if sort == "newest":
            q = q.order_by(GalleryItem.created_at.desc())
        elif sort == "popular":
            q = q.order_by(GalleryItem.likes.desc())
        elif sort == "trending":
            q = q.order_by((GalleryItem.likes + GalleryItem.views).desc())

        # Pagination - use subquery count
        total_result = await db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        q = q.offset(offset).limit(per_page)

        result = await db.execute(q)
        items = result.scalars().all()

        # Atomically increment views for displayed items (no race condition)
        item_ids = [item.id for item in items]
        if item_ids:
            await db.execute(
                update(GalleryItem)
                .where(GalleryItem.id.in_(item_ids))
                .values(views=GalleryItem.views + 1)
            )
            await db.commit()

        return items, total

    async def get_user_gallery(self, db: AsyncSession, user_id: int, page: int = 1, per_page: int = 20):
        offset = (page - 1) * per_page
        result = await db.execute(
            select(GalleryItem)
            .where(GalleryItem.user_id == user_id)
            .options(joinedload(GalleryItem.user))
            .order_by(GalleryItem.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        items = result.scalars().all()

        count_result = await db.execute(
            select(func.count(GalleryItem.id)).where(GalleryItem.user_id == user_id)
        )
        total = count_result.scalar() or 0

        return items, total

    async def get_public_item(self, db: AsyncSession, item_id: int) -> GalleryItem:
        result = await db.execute(
            select(GalleryItem)
            .where(
                GalleryItem.id == item_id,
                GalleryItem.is_public == True,
            )
            .options(joinedload(GalleryItem.user))
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Gallery item not found")

        await db.execute(
            update(GalleryItem)
            .where(GalleryItem.id == item_id)
            .values(views=GalleryItem.views + 1)
        )
        await db.commit()
        await db.refresh(item)
        return item

    async def like_item(self, db: AsyncSession, item_id: int, user_id: int) -> GalleryItem:
        """Atomically increment like count"""
        result = await db.execute(
            select(GalleryItem).where(GalleryItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Gallery item not found")

        # Atomic increment to prevent race condition
        await db.execute(
            update(GalleryItem)
            .where(GalleryItem.id == item_id)
            .values(likes=GalleryItem.likes + 1)
        )
        await db.commit()
        await db.refresh(item)
        return item

    async def delete_item(self, db: AsyncSession, item_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(GalleryItem).where(
                GalleryItem.id == item_id,
                GalleryItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Gallery item not found")

        await db.delete(item)
        await db.commit()
        return True


gallery_service = GalleryService()
