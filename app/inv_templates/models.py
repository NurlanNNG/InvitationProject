import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InvitationTemplate(Base):
    __tablename__ = "invitation_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Уникальный идентификатор шаблона (UUID)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("event_categories.id"), nullable=True
    )  # Категория мероприятия, к которой относится шаблон
    name_kk: Mapped[str] = mapped_column(String(150), nullable=False)  # Название шаблона на казахском языке
    name_ru: Mapped[str] = mapped_column(String(150), nullable=False)  # Название шаблона на русском языке
    preview_url: Mapped[str] = mapped_column(Text, nullable=False)  # Ссылка на полное превью-изображение шаблона
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Ссылка на миниатюру шаблона для отображения в списке
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # Настройки дизайна шаблона: цвета, шрифты, расположение элементов
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Является ли шаблон премиальным (требует оплаты по тарифу)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Доступен ли шаблон для выбора пользователями
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Порядок сортировки при отображении списка шаблонов
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # Дата и время создания шаблона

    # Аудит: кто создал и кто последним изменил запись
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID администратора, создавшего шаблон
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID администратора, последним изменившего шаблон

    def __repr__(self) -> str:
        return f"<InvitationTemplate id={self.id} name_ru={self.name_ru}>"
