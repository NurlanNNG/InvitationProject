import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, DateTime, func, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MediaType(str, enum.Enum):
    photo = "photo"            # Обычная фотография в галерее
    cover = "cover"            # Обложка (главное изображение) приглашения
    background = "background"  # Фоновое изображение всего приглашения


class DisplayStyle(str, enum.Enum):
    circle = "circle"        # Круглое отображение фотографии
    square = "square"        # Квадратное отображение фотографии
    rectangle = "rectangle"  # Прямоугольное отображение фотографии (по умолчанию)


class InvitationMedia(Base):
    __tablename__ = "invitation_media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Уникальный идентификатор медиафайла (UUID)
    invitation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invitations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )  # Приглашение, которому принадлежит данный медиафайл
    media_type: Mapped[MediaType] = mapped_column(
        SAEnum(MediaType, name="mediatype"), default=MediaType.photo, nullable=False
    )  # Тип медиафайла: обычное фото, обложка или фоновое изображение
    url: Mapped[str] = mapped_column(Text, nullable=False)  # Путь к оригинальному файлу на сервере (относительно /media)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Путь к миниатюре файла (300×300 пикс., генерируется автоматически)
    caption: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Подпись или описание к фотографии
    display_style: Mapped[DisplayStyle] = mapped_column(
        SAEnum(DisplayStyle, name="displaystyle"), default=DisplayStyle.rectangle, nullable=False
    )  # Форма отображения фотографии в приглашении (circle / square / rectangle)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Порядок сортировки медиафайла в галерее приглашения
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # Дата и время загрузки файла на сервер

    def __repr__(self) -> str:
        return f"<InvitationMedia id={self.id} type={self.media_type}>"
