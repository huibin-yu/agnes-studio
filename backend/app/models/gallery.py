"""Gallery Model"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime as SqlAlchemyDateTime, Boolean, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class GalleryItem(Base):
    __tablename__ = "gallery_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    media_type = Column(String(20))  # image or video
    media_url = Column(String(500), nullable=False)
    prompt = Column(Text, nullable=False)
    style = Column(String(100), default="")
    tags = Column(JSON, default=list)
    is_public = Column(Boolean, default=True, index=True)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="gallery_items")

    created_at = Column(SqlAlchemyDateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<GalleryItem(id={self.id}, title='{self.title}')>"
