"""Schema Definitions for Auth Endpoints"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    avatar_url: Optional[str] = None
    credits: int
    is_verified: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenRefresh(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class CreditPurchaseRequest(BaseModel):
    amount: int = Field(..., ge=1, le=10000)
    payment_method: str = "stripe"  # stripe, alipay, wechat


class CreditResponse(BaseModel):
    credits: int
    balance: int
    transactions: list  # Will be replaced with proper model
