import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.logging_config import get_logger
from app.auth.models import User
from app.auth.config import get_current_user
from app.invitations.models import Invitation, InvitationStatus
from app.payments.models import PaymentPlan, Payment, PaymentStatus
from app.payments.schemas import (
    PaymentPlanOut, PaymentCreateRequest, PaymentOut, PaymentCreateResponse,
)

router = APIRouter(prefix="/api/v1/payment", tags=["payments"])
logger = get_logger("payments")


@router.get("/plans", response_model=list[PaymentPlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PaymentPlan).where(PaymentPlan.is_active == True).order_by(PaymentPlan.id)
    )
    return result.scalars().all()


@router.post("/create", response_model=PaymentCreateResponse)
async def create_payment(
    data: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates a payment for publishing an invitation.
    Returns Kaspi phone number and amount for manual transfer.
    The invitation will be published after admin confirmation.
    """
    # Verify invitation ownership
    inv_result = await db.execute(
        select(Invitation).where(
            Invitation.id == data.invitation_id,
            Invitation.user_id == current_user.id,
        )
    )
    inv = inv_result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Приглашение не найдено")

    if inv.status == InvitationStatus.published:
        raise HTTPException(400, "Приглашение уже опубликовано")

    # Check for pending/successful payment
    existing_result = await db.execute(
        select(Payment).where(
            Payment.invitation_id == data.invitation_id,
            Payment.status.in_([PaymentStatus.pending, PaymentStatus.success]),
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(400, "Платёж для этого приглашения уже существует или ожидает подтверждения")

    # Get plan
    plan_result = await db.execute(
        select(PaymentPlan).where(PaymentPlan.id == data.plan_id, PaymentPlan.is_active == True)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Тарифный план не найден")

    try:
        payment = Payment(
            user_id=current_user.id,
            invitation_id=data.invitation_id,
            plan_id=data.plan_id,
            amount=plan.price,
            currency=plan.currency,
            status=PaymentStatus.pending,
            payment_method="kaspi",
            kaspi_phone=settings.PAYMENT_KASPI_PHONE,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        logger.info(
            "Payment created: id=%s invitation=%s plan=%s amount=%s user=%s",
            payment.id, data.invitation_id, data.plan_id, plan.price, current_user.username,
        )

        return PaymentCreateResponse(
            payment=payment,
            kaspi_phone=settings.PAYMENT_KASPI_PHONE,
            amount=plan.price,
            currency=plan.currency,
            description=settings.PAYMENT_DESCRIPTION,
            message=(
                f"Переведите {plan.price} {plan.currency} на номер Kaspi "
                f"{settings.PAYMENT_KASPI_PHONE}. "
                f"После перевода ваше приглашение будет опубликовано в течение нескольких минут."
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Payment creation error: %s", e)
        raise HTTPException(500, f"Ошибка создания платежа: {str(e)}")


@router.get("/history", response_model=list[PaymentOut])
async def payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Платёж не найден")
    return payment
