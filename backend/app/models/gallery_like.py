"""Gallery Like Model - tracks per-user likes for deduplication"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, ForeignKey, DateTime as SqlAlchemyDateTime, UniqueConstraint

from app.core.database import Base


class GalleryLike(Base):
    __tablename__ = "gallery_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("gallery_items.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(SqlAlchemyDateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_gallery_like_user_item"),
    )
