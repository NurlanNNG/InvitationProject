from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None


class UserOut(UserBase):
    id: int
    email: Optional[EmailStr] = None
    is_active: bool
    is_locked: bool
    failed_login_attempts: int
    created_at: datetime

    class Config:
        from_attributes = True  # allows orm_mode-like behavior in Pydantic v2


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str