import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class TemplateOut(BaseModel):
    id: uuid.UUID
    category_id: Optional[int] = None
    name_kk: str
    name_ru: str
    description: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    images: List[str] = []
    config: dict
    is_premium: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None

    model_config = {"from_attributes": True}

    @field_validator("images", mode="before")
    @classmethod
    def coerce_images(cls, v: object) -> List[str]:
        return v if v is not None else []


class TemplateCreate(BaseModel):
    category_id: Optional[int] = None
    name_kk: str
    name_ru: str
    description: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    images: Optional[List[str]] = None
    config: dict = {}
    is_premium: bool = False
    sort_order: int = 0


class TemplateUpdate(BaseModel):
    category_id: Optional[int] = None
    name_kk: Optional[str] = None
    name_ru: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    images: Optional[List[str]] = None
    config: Optional[dict] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
