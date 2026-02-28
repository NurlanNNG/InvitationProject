import io
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.logging_config import get_logger
from app.auth.models import User
from app.auth.config import get_current_user
from app.invitations.models import Invitation
from app.media.models import InvitationMedia, MediaType, DisplayStyle
from app.media.schemas import MediaOut

router = APIRouter(tags=["media"])
logger = get_logger("media")

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def _get_media_dir(invitation_id: uuid.UUID) -> Path:
    p = Path(settings.MEDIA_DIR) / str(invitation_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_thumb_dir(invitation_id: uuid.UUID) -> Path:
    p = Path(settings.MEDIA_THUMBS_DIR) / str(invitation_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


async def _count_media(invitation_id: uuid.UUID, db: AsyncSession) -> int:
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(InvitationMedia.id)).where(
            InvitationMedia.invitation_id == invitation_id
        )
    )
    return result.scalar() or 0


def _save_thumbnail(src_path: Path, thumb_dir: Path, filename: str) -> str:
    """Generate a 300x300 thumbnail using Pillow. Returns thumb filename."""
    try:
        from PIL import Image  # type: ignore
        with Image.open(src_path) as img:
            img.thumbnail((300, 300))
            thumb_path = thumb_dir / filename
            img.save(thumb_path, optimize=True, quality=85)
        return filename
    except Exception:
        return ""


@router.post("/api/v1/my/invitations/{invitation_id}/media", response_model=MediaOut, status_code=201)
async def upload_media(
    invitation_id: uuid.UUID,
    file: UploadFile = File(...),
    media_type: MediaType = Form(MediaType.photo),
    display_style: DisplayStyle = Form(DisplayStyle.rectangle),
    caption: Optional[str] = Form(None),
    sort_order: int = Form(0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    inv_result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.user_id == current_user.id,
        )
    )
    inv = inv_result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Приглашение не найдено")

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Допустимые форматы: {', '.join(ALLOWED_CONTENT_TYPES)}")

    # Read and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(400, f"Файл слишком большой. Максимум {settings.MAX_FILE_SIZE_MB} МБ")

    # Check photo limit against payment plan (if paid)
    if inv.is_paid:
        from app.payments.models import Payment, PaymentStatus, PaymentPlan
        pay_result = await db.execute(
            select(Payment).where(
                Payment.invitation_id == invitation_id,
                Payment.status == PaymentStatus.success,
            )
        )
        payment = pay_result.scalar_one_or_none()
        if payment and payment.plan_id:
            plan_result = await db.execute(
                select(PaymentPlan).where(PaymentPlan.id == payment.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                current_count = await _count_media(invitation_id, db)
                if current_count >= plan.max_photos:
                    raise HTTPException(400, f"Лимит фотографий по тарифу: {plan.max_photos}")

    try:
        ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
        file_uuid = str(uuid.uuid4())
        filename = f"{file_uuid}{ext}"

        media_dir = _get_media_dir(invitation_id)
        file_path = media_dir / filename
        file_path.write_bytes(contents)

        # Generate thumbnail
        thumb_dir = _get_thumb_dir(invitation_id)
        thumb_filename = _save_thumbnail(file_path, thumb_dir, filename)

        relative_url = f"{settings.MEDIA_BASE_URL}/uploads/{invitation_id}/{filename}"
        thumb_url = (
            f"{settings.MEDIA_BASE_URL}/thumbs/{invitation_id}/{thumb_filename}"
            if thumb_filename
            else relative_url
        )

        media = InvitationMedia(
            invitation_id=invitation_id,
            media_type=media_type,
            url=relative_url,
            thumbnail_url=thumb_url,
            caption=caption,
            display_style=display_style,
            sort_order=sort_order,
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)

        logger.info(
            "Media uploaded: invitation=%s file=%s type=%s user=%s",
            invitation_id, filename, media_type, current_user.username,
        )
        return media
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Media upload error for invitation %s: %s", invitation_id, e)
        raise HTTPException(500, f"Ошибка загрузки файла: {str(e)}")


@router.get("/api/v1/my/invitations/{invitation_id}/media", response_model=list[MediaOut])
async def list_media(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inv_result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.user_id == current_user.id,
        )
    )
    if not inv_result.scalar_one_or_none():
        raise HTTPException(404, "Приглашение не найдено")

    result = await db.execute(
        select(InvitationMedia)
        .where(InvitationMedia.invitation_id == invitation_id)
        .order_by(InvitationMedia.sort_order)
    )
    return result.scalars().all()


@router.delete("/api/v1/my/invitations/{invitation_id}/media/{media_id}", status_code=204)
async def delete_media(
    invitation_id: uuid.UUID,
    media_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inv_result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.user_id == current_user.id,
        )
    )
    if not inv_result.scalar_one_or_none():
        raise HTTPException(404, "Приглашение не найдено")

    m_result = await db.execute(
        select(InvitationMedia).where(
            InvitationMedia.id == media_id,
            InvitationMedia.invitation_id == invitation_id,
        )
    )
    media = m_result.scalar_one_or_none()
    if not media:
        raise HTTPException(404, "Файл не найден")

    # Delete physical files
    try:
        inv_dir = Path(settings.MEDIA_DIR) / str(invitation_id)
        thumb_dir = Path(settings.MEDIA_THUMBS_DIR) / str(invitation_id)
        filename = Path(media.url).name
        for target in [inv_dir / filename, thumb_dir / filename]:
            if target.exists():
                target.unlink()
    except Exception as e:
        logger.warning("Could not delete file on disk: %s", e)

    await db.delete(media)
    await db.commit()
    logger.info(
        "Media deleted: id=%s invitation=%s user=%s",
        media_id, invitation_id, current_user.username,
    )
