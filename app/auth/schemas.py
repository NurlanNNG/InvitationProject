from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class UserOut(UserBase):
    id: int
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_locked: bool
    locked_until: Optional[datetime] = None
    failed_login_attempts: int
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
