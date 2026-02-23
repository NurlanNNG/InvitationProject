from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from config import settings
from app.database import get_db
from models import User
from app.auth.schemas import (
    UserCreate, UserOut, Token, RefreshTokenRequest
)
from app.auth.config import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.username == user_in.username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )

        if user_in.email:
            result = await db.execute(select(User).where(User.email == user_in.email))
            if result.scalar_one_or_none():
                raise HTTPException(400, "Пользователь с такой почтой уже существует")

        # Hash password and create user
        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            username=user_in.username,
            password_hash=hashed_password,
            email=user_in.email
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500,
                            detail=f"Ошибка регистрации пользователя {str(e)}")


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:

        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неправильный логин или пароль"
            )

        password_correct = verify_password(form_data.password, user.password_hash)
        if not password_correct:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                await db.commit()
                raise HTTPException(
                    status_code=403,
                    detail="Ваш аккаунт заблокирован в связи с 5 неправильных попыток. "
                           "Пожалуйста обратитесь к тех поддержке."
                )
            await db.commit()
            raise HTTPException(401, "Неправильный логин или пароль")

            # Success → reset counter
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            await db.commit()

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь неактивен"
            )

        # Create tokens
        access_token = create_access_token(subject=user.username)
        refresh_token = create_refresh_token(subject=user.username)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
            # "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500,
                            detail=f"Ошибка авторизации пользователя {str(e)}")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Неправильный refresh токен")

        # Optional: check if user still exists / active
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Пользователь не найден или он не активен")

        # Issue new access token (and optionally new refresh)
        new_access = create_access_token(subject=username)
        # You can also issue new refresh token here (rotate) or keep old one

        return {
            "access_token": new_access,
            # "refresh_token": request.refresh_token,  # or create new one
            # "token_type": "bearer"
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Неправильный refresh token")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # For stateless JWT → client just deletes tokens
    # If you implement blacklist → add token to redis/blacklist here
    return {"message": "Logged out successfully. Please remove tokens from client."}

