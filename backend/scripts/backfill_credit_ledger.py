"""Backfill `credit_transactions` for users who pre-date the ledger.

Idempotent: safe to re-run. For each user that has 0 transaction rows,
inserts a single `migration_initial` row with amount=balance_after=user.credits.

Usage:
    cd backend
    python -m scripts.backfill_credit_ledger
"""
import asyncio
import logging

from sqlalchemy import select, func

from app.core.database import async_session
from app.models.user import User
from app.models.credit_transaction import (
    CreditTransaction, TX_MIGRATION_INITIAL,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("backfill_credit_ledger")


async def backfill():
    inserted = 0
    skipped = 0
    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()
        for user in users:
            count = (await session.execute(
                select(func.count(CreditTransaction.id))
                .where(CreditTransaction.user_id == user.id)
            )).scalar() or 0
            if count > 0:
                skipped += 1
                continue
            tx = CreditTransaction(
                user_id=user.id,
                amount=user.credits,
                balance_after=user.credits,
                type=TX_MIGRATION_INITIAL,
                note="initial backfill",
            )
            session.add(tx)
            inserted += 1
        await session.commit()
    logger.info(f"Backfill complete: inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(backfill())
