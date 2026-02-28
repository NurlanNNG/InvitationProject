from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.logging_config import get_logger
from app.auth.models import User
from app.auth.config import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
logger = get_logger("ai")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

_LANGUAGE_NAMES = {"kk": "казахском", "ru": "русском", "en": "English"}

_CATEGORY_NAMES = {
    "wedding": "Той / Свадьба",
    "birthday": "Туған күн / День рождения",
    "anniversary": "Мерейтой / Юбилей",
    "sundet_toi": "Сүндет той",
    "kyz_uzatu": "Қыз ұзату",
    "baby_shower": "Бесік той",
    "corporate": "Корпоративное мероприятие",
    "graduation": "Выпускной",
    "other": "Мероприятие",
}


class GenerateTextRequest(BaseModel):
    category: str = "wedding"
    organizer_name: str
    honoree_name: Optional[str] = None
    event_date: Optional[str] = None
    venue_name: Optional[str] = None
    language: str = "ru"
    custom_fields: Optional[dict] = None


class GenerateTextResponse(BaseModel):
    text: str


def _build_prompt(data: GenerateTextRequest) -> str:
    lang_name = _LANGUAGE_NAMES.get(data.language, "русском")
    category_name = _CATEGORY_NAMES.get(data.category, "Мероприятие")

    parts = [
        f"Создай торжественный текст приглашения на {lang_name} языке.",
        f"Тип мероприятия: {category_name}.",
        f"Организатор: {data.organizer_name}.",
    ]

    if data.honoree_name:
        parts.append(f"Именинник / Участник(и): {data.honoree_name}.")
    if data.event_date:
        parts.append(f"Дата мероприятия: {data.event_date}.")
    if data.venue_name:
        parts.append(f"Место: {data.venue_name}.")

    if data.custom_fields:
        for k, v in data.custom_fields.items():
            parts.append(f"{k}: {v}.")

    parts.append(
        "Напиши текст 3-4 абзаца, тёплым и торжественным стилем, "
        "с учётом казахских культурных традиций. "
        "Без технических деталей и форматирования — только текст приглашения."
    )
    return " ".join(parts)


@router.post("/generate-text", response_model=GenerateTextResponse)
async def generate_invitation_text(
    data: GenerateTextRequest,
    current_user: User = Depends(get_current_user),
):
    if not settings.GROQ_API_KEY:
        raise HTTPException(503, "AI сервис недоступен: GROQ_API_KEY не настроен")

    prompt = _build_prompt(data)

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — помощник по созданию торжественных приглашений. "
                    "Учитывай казахские культурные традиции. "
                    "Пиши тепло, торжественно и лаконично."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 600,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()

        logger.info(
            "AI text generated: category=%s language=%s user=%s",
            data.category, data.language, current_user.username,
        )
        return GenerateTextResponse(text=text)

    except httpx.HTTPStatusError as e:
        logger.error("Groq API HTTP error: %s %s", e.response.status_code, e.response.text)
        raise HTTPException(502, "Ошибка AI сервиса. Попробуйте позже.")
    except httpx.TimeoutException:
        logger.error("Groq API timeout for user %s", current_user.username)
        raise HTTPException(504, "AI сервис не отвечает. Попробуйте позже.")
    except Exception as e:
        logger.error("AI generation error for user %s: %s", current_user.username, e)
        raise HTTPException(500, f"Ошибка генерации текста: {str(e)}")
