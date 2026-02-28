from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.categories.models import EventCategory
from app.categories.schemas import CategoryOut, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])
logger = get_logger("categories")


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EventCategory)
        .where(EventCategory.is_active == True)
        .order_by(EventCategory.sort_order)
    )
    return result.scalars().all()


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EventCategory).where(EventCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(404, "Категория не найдена")
    return category
