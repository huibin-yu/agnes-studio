"""User Model"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(500), default=None)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    credits = Column(Integer, default=10)  # Free credits on register
    referral_code = Column(String(32), unique=True, index=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Referrer user ID
    token_version = Column(Integer, default=1)  # Increment on password change to invalidate old tokens

    # Relationships
    images = relationship("ImageGeneration", back_populates="user")
    videos = relationship("VideoGeneration", back_populates="user")
    gallery_items = relationship("GalleryItem", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    referrer = relationship("User", remote_side=[id], back_populates="referrals")
    referrals = relationship("User", back_populates="referrer")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
