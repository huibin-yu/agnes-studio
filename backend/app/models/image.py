"""Image Generation Model"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime as SqlAlchemyDateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ImageGeneration(Base):
    __tablename__ = "image_generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, default="")
    model = Column(String(100), default="agnes-image-2.1-flash")
    size = Column(String(20), default="1024x768")
    style = Column(String(100), default="none")  # none, cinematic, anime, realistic, etc.
    seed = Column(Integer, default=None)
    steps = Column(Integer, default=30)
    cfg_scale = Column(Float, default=7.5)

    # Output
    image_url = Column(String(500), nullable=False)
    status = Column(String(20), default="completed")  # pending, generating, completed, failed
    error_message = Column(Text, default=None)

    # Metadata
    parameters = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="images")

    created_at = Column(SqlAlchemyDateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ImageGeneration(id={self.id}, prompt='{self.prompt[:30]}...')>"
