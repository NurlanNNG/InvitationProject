from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)  # Уникальный идентификатор пользователя
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)  # Уникальное имя пользователя (логин)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # Хэш пароля (алгоритм Argon2)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, index=True, nullable=True)  # Электронная почта (необязательно, уникальна)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Полное имя пользователя (отображается в профиле)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Активен ли аккаунт (неактивный не может войти)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Является ли пользователь администратором

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Количество неудачных попыток входа подряд
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Заблокирован ли аккаунт (после 5 неудачных попыток)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # До какого момента заблокирован аккаунт

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # Дата и время регистрации аккаунта
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )  # Дата и время последнего обновления профиля

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"
