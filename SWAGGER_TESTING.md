# Swagger Testing Guide

Полная инструкция по тестированию всего бэкенда через Swagger UI.

## Подготовка

### 1. Запустить сервер
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Открыть Swagger UI
Перейти в браузере: **http://localhost:8000/docs**

Swagger отобразит все эндпоинты, сгруппированные по тегам:
- **auth** — авторизация
- **categories** — категории мероприятий
- **templates** — шаблоны оформления
- **invitations** — приглашения
- **rsvp** — ответы гостей
- **media** — фотографии
- **payments** — оплата
- **ai** — генерация текста
- **admin** — панель администратора

---

## Шаг 1 — Регистрация пользователя

**POST /auth/register**

1. Нажать на эндпоинт → кнопка **Try it out**
2. В поле `Request body` вставить:
```json
{
  "username": "testuser",
  "password": "password123",
  "email": "test@example.com",
  "full_name": "Тестовый Пользователь"
}
```
3. Нажать **Execute**
4. Ожидаемый ответ `201`:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Тестовый Пользователь",
  "is_active": true,
  "is_admin": false,
  ...
}
```

---

## Шаг 2 — Вход и авторизация в Swagger

**POST /auth/login**

1. Нажать **Try it out**
2. Заполнить форму (это форма, не JSON):
   - `username`: `testuser`
   - `password`: `password123`
3. Нажать **Execute**
4. Ответ `200` вернёт `access_token`

### Авторизовать Swagger

> Swagger не использует cookies — нужно вручную передать токен через Bearer.

1. Скопировать значение `access_token` из ответа
2. Нажать кнопку **Authorize** (замочек) в верхней части страницы
3. В поле `Value` ввести: `Bearer <скопированный_токен>`
   Пример: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
4. Нажать **Authorize** → **Close**

Теперь все последующие запросы будут отправляться с токеном.

---

## Шаг 3 — Проверить свой профиль

**GET /auth/me**

1. Нажать **Try it out** → **Execute**
2. Ответ `200` вернёт данные текущего пользователя

**PUT /auth/me** — обновить профиль:
```json
{
  "full_name": "Новое Имя",
  "email": "new@example.com"
}
```

---

## Шаг 4 — Категории мероприятий

**GET /api/v1/categories**

1. Нажать **Try it out** → **Execute** (авторизация не нужна)
2. Ответ вернёт 9 предустановленных категорий:
```json
[
  { "id": 1, "slug": "wedding", "name_ru": "Той / Свадьба", ... },
  { "id": 2, "slug": "birthday", "name_ru": "День рождения", ... },
  ...
]
```
3. **Сохранить `id` нужной категории** — понадобится при создании приглашения.

---

## Шаг 5 — Шаблоны оформления

**GET /api/v1/templates**

1. Нажать **Try it out**
2. В поле `category` (необязательно) ввести `wedding`
3. Нажать **Execute**
4. Список пока пуст — шаблоны создаются через админ-панель (Шаг 11)

---

## Шаг 6 — Создать приглашение

**POST /api/v1/my/invitations**

1. Нажать **Try it out**
2. Вставить тело запроса:
```json
{
  "title": "Свадьба Нурлана и Айгерим",
  "category_id": 1,
  "details": {
    "organizer_name": "Семья Ахметовых",
    "honoree_name": "Нурлан и Айгерим",
    "event_date": "2026-06-15",
    "event_time": "18:00",
    "event_end_time": "23:00",
    "venue_name": "Ресторан Алтын Орда",
    "venue_address": "ул. Абая 10, Алматы",
    "venue_map_url": "https://2gis.kz/almaty",
    "contact_phone": "+77001234567",
    "contact_name": "Нурлан",
    "dress_code": "Праздничный",
    "custom_fields": {
      "bride_name": "Айгерим",
      "groom_name": "Нурлан"
    }
  }
}
```
3. Нажать **Execute**
4. Ответ `201` вернёт приглашение с автоматически сгенерированным `slug`:
```json
{
  "id": "uuid...",
  "slug": "semya-akhmetovykh-wedding-2026",
  "status": "draft",
  "is_paid": false,
  "editable_until": "2026-03-04T...",
  ...
}
```
5. **Сохранить `id` и `slug`** — понадобятся в следующих шагах.

---

## Шаг 7 — Просмотр и редактирование приглашения

**GET /api/v1/my/invitations**
Список всех своих приглашений.

**GET /api/v1/my/invitations/{invitation_id}**
Вставить `id` из Шага 6 в поле `invitation_id`.

**PUT /api/v1/my/invitations/{invitation_id}**
Редактирование доступно 3 дня с момента создания:
```json
{
  "title": "Торжество Нурлана и Айгерим",
  "details": {
    "organizer_name": "Семья Ахметовых",
    "event_date": "2026-06-15",
    "invitation_text": "Дорогие друзья! Приглашаем вас разделить с нами радость...",
    "additional_info": "Парковка на 200 мест рядом с рестораном"
  }
}
```
В ответе поле `updated_by_id` будет содержать id редактировавшего пользователя.

---

## Шаг 8 — AI генерация текста приглашения

**POST /api/v1/ai/generate-text**

> Требуется `GROQ_API_KEY` в `.env`. Получить бесплатно на https://console.groq.com

1. Нажать **Try it out**
2. Вставить:
```json
{
  "category": "wedding",
  "organizer_name": "Семья Ахметовых",
  "honoree_name": "Нурлан и Айгерим",
  "event_date": "2026-06-15",
  "venue_name": "Ресторан Алтын Орда, Алматы",
  "language": "ru",
  "custom_fields": {
    "bride_name": "Айгерим",
    "groom_name": "Нурлан"
  }
}
```
3. Нажать **Execute**
4. Ответ вернёт готовый текст:
```json
{
  "text": "Дорогие друзья и родственники! С великой радостью семья Ахметовых приглашает вас..."
}
```
5. Скопировать текст → обновить приглашение через PUT (поле `invitation_text`)

Поддерживаемые языки: `ru`, `kk`, `en`

---

## Шаг 9 — Загрузка фотографий

**POST /api/v1/my/invitations/{invitation_id}/media**

> Запрос типа `multipart/form-data` — в Swagger будет форма с полями.

1. Нажать **Try it out**
2. Вставить `invitation_id`
3. Заполнить форму:
   - `file`: выбрать файл JPG/PNG/WebP (до 5 МБ)
   - `media_type`: `photo` (или `cover`, `background`)
   - `display_style`: `rectangle` (или `circle`, `square`)
   - `caption`: `Наш день` (необязательно)
   - `sort_order`: `0`
4. Нажать **Execute**
5. Ответ вернёт URL загруженного файла:
```json
{
  "id": "uuid...",
  "url": "/media/uploads/uuid.../filename.jpg",
  "thumbnail_url": "/media/thumbs/uuid.../filename.jpg",
  ...
}
```

**GET /api/v1/my/invitations/{invitation_id}/media** — список фотографий

**DELETE /api/v1/my/invitations/{invitation_id}/media/{media_id}** — удалить фото
Ответ `204 No Content` (пустой ответ — это норма)

---

## Шаг 10 — Оплата и публикация

### 10.1 Посмотреть тарифные планы

**GET /api/v1/payment/plans** (без авторизации)

Ответ вернёт 3 плана: Базовый (1990₸), Стандарт (3490₸), Премиум (5990₸).
Сохранить `id` нужного плана.

### 10.2 Создать платёж

**POST /api/v1/payment/create**

```json
{
  "invitation_id": "uuid-приглашения-из-шага-6",
  "plan_id": 1
}
```

Ответ вернёт инструкцию:
```json
{
  "payment": { "id": "uuid...", "status": "pending", ... },
  "kaspi_phone": "+77001234567",
  "amount": 1990.00,
  "message": "Переведите 1990 KZT на номер +77001234567..."
}
```
Сохранить `payment.id` — понадобится администратору.

### 10.3 Посмотреть историю платежей

**GET /api/v1/payment/history**

---

## Шаг 11 — Действия администратора

> Сначала нужно назначить пользователя администратором через SQL:
> ```sql
> UPDATE users SET is_admin = true WHERE username = 'testuser';
> ```
> После этого заново войти (Шаг 2) и обновить токен в Swagger (Authorize).

### 11.1 Подтвердить платёж → опубликовать приглашение

**POST /api/v1/admin/payments/{payment_id}/confirm**

1. Вставить `payment_id` из Шага 10.2
2. Нажать **Execute**
3. Ответ `200`: платёж получит `status: success`, приглашение — `status: published`
4. В поле `confirmed_by` будет `id` администратора

После подтверждения:
- `invitation.status` → `published`
- `invitation.is_paid` → `true`
- `invitation.updated_by_id` → id администратора (аудит)
- `invitation.expires_at` → текущая дата + срок тарифа

**POST /api/v1/admin/payments/{payment_id}/reject** — отклонить платёж

### 11.2 Посмотреть все/ожидающие платежи

**GET /api/v1/admin/payments** — все платежи
**GET /api/v1/admin/payments?status=pending** — только ожидающие подтверждения

### 11.3 Создать шаблон оформления

**POST /api/v1/admin/templates**

```json
{
  "category_id": 1,
  "name_kk": "Алтын той",
  "name_ru": "Золотая свадьба",
  "preview_url": "/media/uploads/templates/gold-preview.jpg",
  "config": {
    "primary_color": "#C8A96E",
    "secondary_color": "#F5F0E8",
    "font_heading": "Playfair Display",
    "ornament_style": "kazakh_pattern_1",
    "blocks": ["hero", "event_info", "location", "gallery", "rsvp"]
  },
  "is_premium": false,
  "sort_order": 1
}
```

В ответе поля `created_by_id` и `updated_by_id` будут содержать id администратора.

**PUT /api/v1/admin/templates/{template_id}** — обновить шаблон
После обновления `updated_by_id` изменится на id редактировавшего администратора.

### 11.4 Создать категорию

**POST /api/v1/admin/categories**

```json
{
  "slug": "nikahnama",
  "name_kk": "Неке қию",
  "name_ru": "Никях",
  "name_en": "Nikah",
  "sort_order": 10
}
```

В ответе `created_by_id` = id создавшего администратора.

### 11.5 Список пользователей

**GET /api/v1/admin/users**

### 11.6 Назначить администратора

**POST /api/v1/admin/users/{user_id}/make-admin**

Вставить `user_id` нужного пользователя (из списка пользователей).

---

## Шаг 12 — Публичная страница приглашения

> Только после подтверждения оплаты (Шаг 11.1).

**GET /api/v1/invite/{slug}** (без авторизации)

1. Вставить `slug` приглашения (из Шага 6)
2. Нажать **Execute**
3. Ответ вернёт полные данные: детали мероприятия + список фотографий

Если приглашение не оплачено или не опубликовано — ответ `404`.

---

## Шаг 13 — RSVP: ответ гостя

**POST /api/v1/invite/{slug}/rsvp** (без авторизации)

1. Вставить `slug` из Шага 6
2. Тело запроса:
```json
{
  "guest_name": "Алия Сейткали",
  "guest_phone": "+77771234567",
  "will_attend": true,
  "guest_count": 2,
  "message": "Поздравляем! Обязательно придём!"
}
```
3. Ответ `200` — ответ сохранён

**Повторный RSVP с тем же номером телефона** обновит существующий ответ, а не создаст дубликат.

---

## Шаг 14 — Аналитика гостей

**GET /api/v1/my/invitations/{invitation_id}/guests**

Ответ вернёт сводку и полный список ответов:
```json
{
  "total_responses": 3,
  "attending": 2,
  "not_attending": 1,
  "total_guests": 5,
  "responses": [ ... ]
}
```

---

## Шаг 15 — RSVP вопросы (кастомные)

**POST /api/v1/my/invitations/{invitation_id}/questions**

Добавить собственный вопрос к анкете гостей:
```json
{
  "question_text_kk": "Аллергия бар ма?",
  "question_text_ru": "Есть ли у вас аллергия на продукты?",
  "question_type": "text",
  "is_required": false,
  "sort_order": 1
}
```

Типы вопросов: `boolean`, `number`, `text`, `select`

**GET /api/v1/my/invitations/{invitation_id}/questions** — список вопросов
**DELETE /api/v1/my/invitations/{invitation_id}/questions/{question_id}** — удалить вопрос

---

## Шаг 16 — Удалить приглашение

**DELETE /api/v1/my/invitations/{invitation_id}**

Ответ `204 No Content` (пустой ответ).
Удаляет приглашение вместе со всеми деталями, медиафайлами и RSVP-ответами (CASCADE).

---

## Токены: что делать при 401

Если Swagger начинает возвращать `401 Unauthorized`:

1. Открыть **POST /auth/refresh** → **Try it out**
2. Тело:
```json
{ "refresh_token": "ваш_refresh_token_из_шага_2" }
```
3. Скопировать новый `access_token`
4. Нажать **Authorize** (замочек) → обновить токен

---

## Аудит: где видны поля

| Таблица              | `created_by_id`    | `updated_by_id`               |
|----------------------|--------------------|-------------------------------|
| `event_categories`   | Кто создал (admin) | Кто последний редактировал (admin) |
| `invitation_templates` | Кто создал (admin) | Кто последний редактировал (admin) |
| `payment_plans`      | Кто создал (admin) | Кто последний редактировал (admin) |
| `invitations`        | — (это `user_id`) | Кто последний редактировал (user или admin) |
| `payments`           | — (это `user_id`) | `confirmed_by` — кто подтвердил (admin) |

---

## Порядок статусов приглашения

```
draft  →  (оплата создана)  →  pending payment
      →  (admin confirm)    →  published
      →  (expires_at < now) →  expired   (авто при запросе)
```

---

## Быстрая проверка через curl

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'

# Вход
curl -X POST http://localhost:8000/auth/login \
  -d "username=test&password=password123"

# Категории (без токена)
curl http://localhost:8000/api/v1/categories

# Создать приглашение (с токеном)
curl -X POST http://localhost:8000/api/v1/my/invitations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Тест","category_id":1,"details":{"organizer_name":"Тест","event_date":"2026-06-15"}}'
```
