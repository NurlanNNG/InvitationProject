import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.logging_config import get_logger
from .models import User
from app.auth.schemas import UserCreate, UserOut, Token, RefreshTokenRequest, UserUpdate
from app.auth.config import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth")

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


def _set_token_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.username == user_in.username))
        if result.scalar_one_or_none():
            raise HTTPException(400, "Пользователь с таким именем уже существует")

        if user_in.email:
            result = await db.execute(select(User).where(User.email == user_in.email))
            if result.scalar_one_or_none():
                raise HTTPException(400, "Пользователь с такой почтой уже существует")

        new_user = User(
            username=user_in.username,
            password_hash=get_password_hash(user_in.password),
            email=user_in.email,
            full_name=user_in.full_name,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info("User registered: username=%s", new_user.username)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Registration error for %s: %s", user_in.username, e)
        raise HTTPException(status_code=500, detail=f"Ошибка регистрации: {str(e)}")


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("Login attempt with unknown username: %s", form_data.username)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неправильный логин или пароль")

        if user.is_locked:
            now = datetime.now(timezone.utc)
            if user.locked_until and user.locked_until > now:
                remaining = int((user.locked_until - now).total_seconds() // 60) + 1
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    f"Аккаунт заблокирован. Попробуйте через {remaining} минут(ы).",
                )
            user.is_locked = False
            user.failed_login_attempts = 0
            user.locked_until = None
            await db.commit()

        if not user.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Пользователь неактивен")

        if not verify_password(form_data.password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
                await db.commit()
                logger.warning("Account locked after failed attempts: %s", user.username)
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    f"Аккаунт заблокирован на {LOCKOUT_MINUTES} минут после {MAX_LOGIN_ATTEMPTS} неудачных попыток.",
                )
            remaining = MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
            await db.commit()
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                f"Неправильный логин или пароль. Осталось попыток: {remaining}.",
            )

        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            await db.commit()

        access_token = create_access_token(subject=user.username)
        refresh_token = create_refresh_token(subject=user.username)
        _set_token_cookies(response, access_token, refresh_token)
        logger.info("User logged in: username=%s", user.username)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Login error: %s", e)
        raise HTTPException(500, f"Ошибка авторизации: {str(e)}")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    request: Request,
    request_data: RefreshTokenRequest = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        token_value = (
            request_data.refresh_token
            if request_data and request_data.refresh_token
            else request.cookies.get("refresh_token")
        )
        if not token_value:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh токен не предоставлен")

        payload = jwt.decode(token_value, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None or payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неправильный refresh токен")

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Пользователь не найден или неактивен")

        new_access = create_access_token(subject=username)
        new_refresh = create_refresh_token(subject=username)
        _set_token_cookies(response, new_access, new_refresh)
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неправильный или истёкший refresh токен")


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    logger.info("User logged out: username=%s", current_user.username)
    return {"message": "Вы успешно вышли из системы."}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if update_data.email and update_data.email != current_user.email:
            result = await db.execute(select(User).where(User.email == update_data.email))
            if result.scalar_one_or_none():
                raise HTTPException(400, "Пользователь с такой почтой уже существует")
            current_user.email = update_data.email

        if update_data.full_name is not None:
            current_user.full_name = update_data.full_name

        if update_data.password:
            current_user.password_hash = get_password_hash(update_data.password)

        await db.commit()
        await db.refresh(current_user)
        logger.info("User profile updated: username=%s", current_user.username)
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Profile update error for %s: %s", current_user.username, e)
        raise HTTPException(500, f"Ошибка обновления профиля: {str(e)}")
