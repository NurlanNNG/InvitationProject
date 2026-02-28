import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.auth.models import User
from app.auth.config import get_current_admin_user
from app.invitations.models import Invitation, InvitationStatus
from app.payments.models import Payment, PaymentStatus, PaymentPlan
from app.payments.schemas import PaymentOut, PaymentPlanOut
from app.categories.models import EventCategory
from app.categories.schemas import CategoryCreate, CategoryUpdate, CategoryOut
from app.inv_templates.models import InvitationTemplate
from app.inv_templates.schemas import TemplateCreate, TemplateUpdate, TemplateOut

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = get_logger("admin")


# ─── Payment management ───────────────────────────────────────────────────────

@router.get("/payments", response_model=list[PaymentOut])
async def list_payments(
    payment_status: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payment).order_by(Payment.created_at.desc())
    if payment_status:
        try:
            stmt = stmt.where(Payment.status == PaymentStatus(payment_status))
        except ValueError:
            raise HTTPException(400, f"Неверный статус: {payment_status}")
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/payments/{payment_id}/confirm", response_model=PaymentOut)
async def confirm_payment(
    payment_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin confirms that a Kaspi payment was received.
    Updates payment to success and publishes the associated invitation.
    """
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Платёж не найден")
    if payment.status != PaymentStatus.pending:
        raise HTTPException(400, f"Платёж уже имеет статус: {payment.status.value}")

    try:
        now = datetime.now(timezone.utc)
        payment.status = PaymentStatus.success
        payment.paid_at = now
        payment.confirmed_by = admin.id  # existing audit field on Payment

        if payment.invitation_id:
            inv_result = await db.execute(
                select(Invitation).where(Invitation.id == payment.invitation_id)
            )
            inv = inv_result.scalar_one_or_none()
            if inv:
                inv.status = InvitationStatus.published
                inv.is_paid = True
                inv.published_at = now
                inv.updated_by_id = admin.id  # audit: admin published it

                if payment.plan_id:
                    plan_result = await db.execute(
                        select(PaymentPlan).where(PaymentPlan.id == payment.plan_id)
                    )
                    plan = plan_result.scalar_one_or_none()
                    if plan:
                        inv.expires_at = now + timedelta(days=plan.validity_days)

        await db.commit()
        await db.refresh(payment)
        logger.info(
            "Payment confirmed: payment_id=%s invitation_id=%s admin=%s",
            payment_id, payment.invitation_id, admin.username,
        )
        return payment
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Payment confirmation error: payment_id=%s error=%s", payment_id, e)
        raise HTTPException(500, f"Ошибка подтверждения платежа: {str(e)}")


@router.post("/payments/{payment_id}/reject", response_model=PaymentOut)
async def reject_payment(
    payment_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Платёж не найден")
    if payment.status != PaymentStatus.pending:
        raise HTTPException(400, f"Платёж уже имеет статус: {payment.status.value}")

    payment.status = PaymentStatus.failed
    payment.confirmed_by = admin.id  # record who rejected it too
    await db.commit()
    await db.refresh(payment)
    logger.info("Payment rejected: payment_id=%s admin=%s", payment_id, admin.username)
    return payment


# ─── Category management ─────────────────────────────────────────────────────

@router.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(
    data: CategoryCreate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(EventCategory).where(EventCategory.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Категория со slug '{data.slug}' уже существует")

    cat = EventCategory(**data.model_dump(), created_by_id=admin.id, updated_by_id=admin.id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    logger.info("Category created: slug=%s admin=%s", data.slug, admin.username)
    return cat


@router.put("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EventCategory).where(EventCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Категория не найдена")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    cat.updated_by_id = admin.id

    await db.commit()
    await db.refresh(cat)
    logger.info("Category updated: id=%s admin=%s", category_id, admin.username)
    return cat


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EventCategory).where(EventCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Категория не найдена")
    await db.delete(cat)
    await db.commit()
    logger.info("Category deleted: id=%s admin=%s", category_id, admin.username)


# ─── Template management ─────────────────────────────────────────────────────

@router.post("/templates", response_model=TemplateOut, status_code=201)
async def create_template(
    data: TemplateCreate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    tpl = InvitationTemplate(**data.model_dump(), created_by_id=admin.id, updated_by_id=admin.id)
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    logger.info("Template created: id=%s admin=%s", tpl.id, admin.username)
    return tpl


@router.put("/templates/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InvitationTemplate).where(InvitationTemplate.id == template_id)
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(404, "Шаблон не найден")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tpl, field, value)
    tpl.updated_by_id = admin.id

    await db.commit()
    await db.refresh(tpl)
    logger.info("Template updated: id=%s admin=%s", template_id, admin.username)
    return tpl


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InvitationTemplate).where(InvitationTemplate.id == template_id)
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(404, "Шаблон не найден")
    await db.delete(tpl)
    await db.commit()
    logger.info("Template deleted: id=%s admin=%s", template_id, admin.username)


# ─── Payment plan management ─────────────────────────────────────────────────

@router.post("/plans", response_model=PaymentPlanOut, status_code=201)
async def create_plan(
    data: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    plan = PaymentPlan(**data, created_by_id=admin.id, updated_by_id=admin.id)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    logger.info("Payment plan created: id=%s admin=%s", plan.id, admin.username)
    return plan


# ─── User management ─────────────────────────────────────────────────────────

@router.get("/users", response_model=list[dict])
async def list_users(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.auth.schemas import UserOut
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserOut.model_validate(u).model_dump() for u in users]


@router.post("/users/{user_id}/make-admin", response_model=dict)
async def make_admin(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    user.is_admin = True
    await db.commit()
    logger.info("User promoted to admin: user_id=%s by admin=%s", user_id, admin.username)
    return {"message": f"Пользователь {user.username} назначен администратором"}
