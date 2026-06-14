"""Schema Definitions for API Keys"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rate_limit: Optional[int] = Field(10, ge=1, le=100, description="Requests per minute")
    daily_limit: Optional[int] = Field(100, ge=1, le=10000, description="Daily request limit")
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    """Response for API key creation - includes the key (shown only once)"""
    id: int
    name: str
    key: str  # Only shown on creation
    is_active: bool
    rate_limit: int
    daily_limit: int
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyListItem(BaseModel):
    """Response for API key list - does NOT include the key value"""
    id: int
    name: str
    key_prefix: str  # e.g. "agsk_xxxx" - only show first 8 chars
    is_active: bool
    rate_limit: int
    daily_limit: int
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyListItem]
    total: int


class ApiKeyUsageResponse(BaseModel):
    total_requests: int
    today_requests: int
    remaining_today: int
    daily_limit: int
