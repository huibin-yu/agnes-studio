"""Schemas for credit ledger API."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CreditTransactionResponse(BaseModel):
    id: int
    amount: int
    balance_after: int
    type: str
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreditTransactionListResponse(BaseModel):
    items: List[CreditTransactionResponse]
    total: int
    page: int
    per_page: int
