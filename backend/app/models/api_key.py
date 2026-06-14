"""API Key Model"""
import secrets
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime as SqlAlchemyDateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=10)  # requests per minute
    daily_limit = Column(Integer, default=100)
    expires_at = Column(SqlAlchemyDateTime(timezone=True), default=None)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    created_at = Column(SqlAlchemyDateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @classmethod
    def generate_key(cls, prefix="agsk_"):
        return f"{prefix}{secrets.token_hex(32)}"

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', key='{self.key[:10]}...')>"
