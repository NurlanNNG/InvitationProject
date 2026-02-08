from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False,)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False,)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, index=True, nullable=True,)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, )

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False,)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True,)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"