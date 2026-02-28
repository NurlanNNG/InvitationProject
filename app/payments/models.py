import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, DECIMAL, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PaymentStatus(str, enum.Enum):
    pending = "pending"    # Ожидает подтверждения администратором
    success = "success"    # Платёж успешно подтверждён администратором
    failed = "failed"      # Платёж отклонён администратором
    refunded = "refunded"  # Средства возвращены пользователю


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор тарифного плана
    name_kk: Mapped[str] = mapped_column(String(100), nullable=False)  # Название тарифа на казахском языке
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)  # Название тарифа на русском языке
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)  # Стоимость тарифного плана
    currency: Mapped[str] = mapped_column(String(3), default="KZT", nullable=False)  # Валюта (по умолчанию KZT — казахстанский тенге)
    max_guests: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Максимальное число RSVP-ответов (NULL — без ограничений)
    max_photos: Mapped[int] = mapped_column(Integer, default=10, nullable=False)  # Максимальное количество фотографий в приглашении
    validity_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)  # Срок активности публикации в днях с момента оплаты
    features: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Дополнительные возможности тарифа в формате JSON
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Доступен ли тариф для выбора пользователями

    # Аудит: кто создал и кто последним изменил запись
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID администратора, создавшего тарифный план
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID администратора, последним изменившего тарифный план

    def __repr__(self) -> str:
        return f"<PaymentPlan id={self.id} name={self.name_ru} price={self.price}>"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Уникальный идентификатор платежа (UUID)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )  # ID пользователя, совершившего платёж
    invitation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invitations.id", ondelete="SET NULL"), nullable=True
    )  # Приглашение, за публикацию которого произведён данный платёж
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment_plans.id"), nullable=True
    )  # Выбранный тарифный план (определяет срок и лимиты)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)  # Сумма платежа (фиксируется на момент создания)
    currency: Mapped[str] = mapped_column(String(3), default="KZT", nullable=False)  # Валюта платежа (по умолчанию KZT)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="paymentstatus"), default=PaymentStatus.pending, nullable=False
    )  # Текущий статус платежа (pending / success / failed / refunded)
    payment_method: Mapped[str] = mapped_column(String(50), default="kaspi", nullable=False)  # Способ оплаты (по умолчанию kaspi — ручной перевод через Kaspi)
    kaspi_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Номер телефона Kaspi, на который пользователь переводит средства
    confirmed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # ID администратора, подтвердившего или отклонившего платёж
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Дата и время подтверждения оплаты администратором
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # Дата и время создания записи о платеже

    def __repr__(self) -> str:
        return f"<Payment id={self.id} status={self.status} amount={self.amount}>"
