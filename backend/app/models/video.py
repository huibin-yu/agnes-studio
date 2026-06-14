"""Video Generation Model"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime as SqlAlchemyDateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class VideoGeneration(Base):
    __tablename__ = "video_generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, default="")
    model = Column(String(100), default="agnes-video-v2.0")
    num_frames = Column(Integer, default=121)
    frame_rate = Column(Integer, default=24)
    width = Column(Integer, default=1152)
    height = Column(Integer, default=768)
    seed = Column(Integer, default=None)
    style = Column(String(100), default="cinematic")

    # Task IDs from Agnes API
    task_id = Column(String(200), nullable=False)
    video_id = Column(String(500), nullable=False, index=True)

    # Output
    video_url = Column(String(500), default=None)
    status = Column(String(20), default="queued")  # queued, generating, completed, failed
    progress = Column(Integer, default=0)
    error_message = Column(Text, default=None)
    expires_at = Column(SqlAlchemyDateTime(timezone=True), default=None)

    # Metadata
    parameters = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="videos")

    created_at = Column(SqlAlchemyDateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(SqlAlchemyDateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def duration_seconds(self) -> float:
        return self.num_frames / self.frame_rate

    def __repr__(self):
        return f"<VideoGeneration(id={self.id}, task_id='{self.task_id[:15]}...')>"
