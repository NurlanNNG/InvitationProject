"""
Seed script: populates initial data (categories, payment plans).
Run once after migrations: python -m app.init_db
"""
import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.categories.models import EventCategory
from app.payments.models import PaymentPlan


CATEGORIES = [
    {"slug": "wedding",     "name_kk": "Той / Үйлену тойы", "name_ru": "Той / Свадьба",          "name_en": "Wedding",        "sort_order": 1},
    {"slug": "birthday",    "name_kk": "Туған күн",          "name_ru": "День рождения",           "name_en": "Birthday",       "sort_order": 2},
    {"slug": "anniversary", "name_kk": "Мерейтой",           "name_ru": "Юбилей / Годовщина",      "name_en": "Anniversary",    "sort_order": 3},
    {"slug": "sundet_toi",  "name_kk": "Сүндет той",         "name_ru": "Сүндет той (обрезание)",  "name_en": "Sunnat Toi",     "sort_order": 4},
    {"slug": "kyz_uzatu",   "name_kk": "Қыз ұзату",          "name_ru": "Қыз ұзату (проводы)",     "name_en": "Kyz Uzatu",      "sort_order": 5},
    {"slug": "baby_shower", "name_kk": "Бесік той",          "name_ru": "Бесік той (новорождённый)","name_en": "Baby Shower",    "sort_order": 6},
    {"slug": "corporate",   "name_kk": "Корпоратив",         "name_ru": "Корпоративное мероприятие","name_en": "Corporate",      "sort_order": 7},
    {"slug": "graduation",  "name_kk": "Бітіру тойы",        "name_ru": "Выпускной",               "name_en": "Graduation",     "sort_order": 8},
    {"slug": "other",       "name_kk": "Басқа",              "name_ru": "Другое",                  "name_en": "Other",          "sort_order": 9},
]

PAYMENT_PLANS = [
    {
        "name_kk": "Базалық",
        "name_ru": "Базовый",
        "price": Decimal("1990.00"),
        "currency": "KZT",
        "max_guests": 100,
        "max_photos": 5,
        "validity_days": 30,
        "features": {
            "items": [
                "До 100 гостей",
                "До 5 фотографий",
                "Публикация на 30 дней",
                "RSVP форма",
            ]
        },
    },
    {
        "name_kk": "Стандарт",
        "name_ru": "Стандарт",
        "price": Decimal("3490.00"),
        "currency": "KZT",
        "max_guests": 500,
        "max_photos": 15,
        "validity_days": 60,
        "features": {
            "items": [
                "До 500 гостей",
                "До 15 фотографий",
                "Публикация на 60 дней",
                "RSVP форма",
                "AI генерация текста",
            ]
        },
    },
    {
        "name_kk": "Премиум",
        "name_ru": "Премиум",
        "price": Decimal("5990.00"),
        "currency": "KZT",
        "max_guests": None,  # unlimited
        "max_photos": 30,
        "validity_days": 90,
        "features": {
            "items": [
                "Неограниченное количество гостей",
                "До 30 фотографий",
                "Публикация на 90 дней",
                "RSVP форма",
                "AI генерация текста",
                "Приоритетная поддержка",
            ]
        },
    },
]


async def seed(db: AsyncSession) -> None:
    # Seed categories
    for cat_data in CATEGORIES:
        result = await db.execute(
            select(EventCategory).where(EventCategory.slug == cat_data["slug"])
        )
        if not result.scalar_one_or_none():
            db.add(EventCategory(**cat_data))
            print(f"  + Category: {cat_data['slug']}")
        else:
            print(f"  ~ Category already exists: {cat_data['slug']}")

    # Seed payment plans (only if none exist)
    plans_result = await db.execute(select(PaymentPlan))
    existing_plans = plans_result.scalars().all()
    if not existing_plans:
        for plan_data in PAYMENT_PLANS:
            db.add(PaymentPlan(**plan_data))
            print(f"  + Plan: {plan_data['name_ru']} — {plan_data['price']} KZT")
    else:
        print(f"  ~ Payment plans already exist ({len(existing_plans)} found)")

    await db.commit()
    print("Seeding complete.")


async def main() -> None:
    print("Running seed...")
    async with async_session() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
