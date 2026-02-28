import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TemplateOut(BaseModel):
    id: uuid.UUID
    category_id: Optional[int] = None
    name_kk: str
    name_ru: str
    preview_url: str
    thumbnail_url: Optional[str] = None
    config: dict
    is_premium: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None

    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    category_id: Optional[int] = None
    name_kk: str
    name_ru: str
    preview_url: str
    thumbnail_url: Optional[str] = None
    config: dict = {}
    is_premium: bool = False
    sort_order: int = 0


class TemplateUpdate(BaseModel):
    category_id: Optional[int] = None
    name_kk: Optional[str] = None
    name_ru: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    config: Optional[dict] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
