from typing import Optional
from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    slug: str
    name_kk: str
    name_ru: str
    name_en: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool
    sort_order: int
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    slug: str
    name_kk: str
    name_ru: str
    name_en: Optional[str] = None
    icon_url: Optional[str] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name_kk: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
