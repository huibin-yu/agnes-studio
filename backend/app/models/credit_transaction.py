"""Credit Transaction (Ledger) Model."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime as SqlAlchemyDateTime,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# Allowed `type` values
TX_IMAGE_GENERATE = "image_generate"
TX_VIDEO_GENERATE = "video_generate"
TX_VIDEO_REFUND = "video_refund"
TX_TOPUP = "topup"
TX_REGISTER_BONUS = "register_bonus"
TX_REFERRAL_BONUS = "referral_bonus"
TX_ADMIN_ADJUST = "admin_adjust"
TX_MIGRATION_INITIAL = "migration_initial"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    type = Column(String(32), nullable=False, index=True)
    ref_type = Column(String(32), nullable=True)
    ref_id = Column(Integer, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(
        SqlAlchemyDateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user = relationship("User")

    def __repr__(self):
        return (
            f"<CreditTransaction(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, type={self.type})>"
        )
