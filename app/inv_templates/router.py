import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.inv_templates.models import InvitationTemplate
from app.inv_templates.schemas import TemplateOut

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])
logger = get_logger("templates")


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    db: AsyncSession = Depends(get_db),
):
    from app.categories.models import EventCategory

    stmt = select(InvitationTemplate).where(InvitationTemplate.is_active == True)

    if category:
        cat_result = await db.execute(
            select(EventCategory).where(EventCategory.slug == category)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            stmt = stmt.where(InvitationTemplate.category_id == cat.id)

    stmt = stmt.order_by(InvitationTemplate.sort_order)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(template_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvitationTemplate).where(InvitationTemplate.id == template_id)
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(404, "Шаблон не найден")
    return tpl
