"""Credit ledger service: charges, grants, queries.

Methods do NOT commit -- caller controls transaction boundary so the
ledger row and any business rows commit atomically.
"""
import logging
from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.credit_transaction import CreditTransaction

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Raised when a charge would drive balance below zero."""


class CreditService:
    async def charge(
        self,
        db: AsyncSession,
        user_id: int,
        amount: int,
        type: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> CreditTransaction:
        """Deduct `amount` credits from user. amount must be positive.

        Locks the users row with SELECT ... FOR UPDATE (no-op on SQLite).
        Raises InsufficientCreditsError if balance < amount.
        Does NOT commit.
        """
        if amount <= 0:
            raise ValueError("charge amount must be positive")

        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} not found")

        if user.credits < amount:
            raise InsufficientCreditsError(
                f"User {user_id} has {user.credits} credits, needs {amount}"
            )

        user.credits -= amount
        await db.flush()

        tx = CreditTransaction(
            user_id=user_id,
            amount=-amount,
            balance_after=user.credits,
            type=type,
            ref_type=ref_type,
            ref_id=ref_id,
            note=note,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def grant(
        self,
        db: AsyncSession,
        user_id: int,
        amount: int,
        type: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> CreditTransaction:
        """Credit `amount` to user. amount must be positive. Does NOT commit."""
        if amount <= 0:
            raise ValueError("grant amount must be positive")

        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} not found")

        user.credits += amount
        await db.flush()

        tx = CreditTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=user.credits,
            type=type,
            ref_type=ref_type,
            ref_id=ref_id,
            note=note,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def get_user_transactions(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[CreditTransaction], int]:
        """List user's credit transactions, newest first.

        Returns (items, total).
        """
        offset = (page - 1) * per_page

        count_result = await db.execute(
            select(func.count(CreditTransaction.id))
            .where(CreditTransaction.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(
                CreditTransaction.created_at.desc(),
                CreditTransaction.id.desc(),
            )
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        return items, total


credit_service = CreditService()
