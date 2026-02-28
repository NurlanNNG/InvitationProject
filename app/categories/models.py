from typing import Optional

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventCategory(Base):
    __tablename__ = "event_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор категории
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # URL-метка категории (только латиница, например «wedding»)
    name_kk: Mapped[str] = mapped_column(String(100), nullable=False)  # Название категории на казахском языке
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)  # Название категории на русском языке
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Название категории на английском языке (необязательно)
    icon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URL иконки или изображения категории
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Отображается ли категория пользователям
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Порядок сортировки при отображении списка категорий

    # Аудит: кто создал и кто последним изменил запись
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID администратора, создавшего категорию
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID администратора, последним изменившего категорию

    def __repr__(self) -> str:
        return f"<EventCategory slug={self.slug}>"
