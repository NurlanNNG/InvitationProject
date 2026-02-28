import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Integer, Boolean, Text, ForeignKey, DateTime, func,
    Enum as SAEnum, Date, DECIMAL,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InvitationStatus(str, enum.Enum):
    draft = "draft"          # Черновик: приглашение создано, но не опубликовано
    published = "published"  # Опубликовано: доступно по публичной ссылке
    expired = "expired"      # Срок действия истёк (expires_at прошёл)
    archived = "archived"    # Архивировано вручную владельцем


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Уникальный идентификатор приглашения (UUID)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )  # ID пользователя-владельца (создателя) приглашения
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invitation_templates.id"), nullable=True
    )  # Шаблон оформления приглашения (необязательно)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("event_categories.id"), nullable=True
    )  # Категория мероприятия (свадьба, день рождения и т.д.)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)  # Уникальная URL-метка для публичной ссылки (например «ivan-wedding-2025»)
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Заголовок приглашения, видимый владельцу в списке
    status: Mapped[InvitationStatus] = mapped_column(
        SAEnum(InvitationStatus, name="invitationstatus"),
        default=InvitationStatus.draft,
        nullable=False,
    )  # Текущий статус приглашения (draft / published / expired / archived)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Оплачено ли приглашение (публикация доступна только после оплаты)
    editable_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # Крайний срок редактирования (3 дня с момента создания)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Дата и время публикации (заполняется после подтверждения оплаты)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Дата и время истечения срока публикации (зависит от тарифного плана)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # Дата и время создания приглашения
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )  # Дата и время последнего изменения приглашения

    # Аудит: user_id является создателем; updated_by_id фиксирует последнего редактора
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID пользователя или администратора, последним изменившего приглашение

    def __repr__(self) -> str:
        return f"<Invitation slug={self.slug} status={self.status}>"


class InvitationDetails(Base):
    __tablename__ = "invitation_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Уникальный идентификатор записи деталей
    invitation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invitations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )  # Приглашение, к которому относятся эти детали (связь один к одному)
    organizer_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Имя организатора или отправителя приглашения
    honoree_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Имя именинника или главного гостя мероприятия
    invitation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Основной текст приглашения (поздравление, обращение к гостям)
    event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Описание мероприятия (программа, детали)
    event_date: Mapped[datetime] = mapped_column(Date, nullable=False)  # Дата проведения мероприятия
    event_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Время начала мероприятия в формате HH:MM
    event_end_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Время окончания мероприятия в формате HH:MM
    dress_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Дресс-код мероприятия (например «чёрный галстук»)
    venue_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Название места проведения (ресторан, зал и т.д.)
    venue_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Полный адрес места проведения мероприятия
    venue_lat: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 8), nullable=True)  # Широта координат места проведения (для карты)
    venue_lng: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(11, 8), nullable=True)  # Долгота координат места проведения (для карты)
    venue_map_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Ссылка на карту (2GIS, Google Maps и т.п.)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Контактный номер телефона организатора
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Имя контактного лица для связи
    additional_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Дополнительная информация и пожелания для гостей
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Произвольные дополнительные поля в формате JSON

    def __repr__(self) -> str:
        return f"<InvitationDetails invitation_id={self.invitation_id}>"
