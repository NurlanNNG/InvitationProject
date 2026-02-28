# Invitation Platform — Backend Guide

## Что это такое

Бэкенд для платформы цифровых приглашений на казахские мероприятия (свадьбы, дни рождения, сүндет той и т.д.).

Пользователь создаёт приглашение, заполняет детали мероприятия, загружает фото, генерирует текст через AI,
оплачивает публикацию через Kaspi — и получает уникальную ссылку, которую можно отправить гостям.
Гости переходят по ссылке, видят красивую страницу и оставляют RSVP-ответ.

---

## Стек

| Компонент      | Технология                                  |
|----------------|---------------------------------------------|
| Язык           | Python 3.9                                  |
| Веб-фреймворк  | FastAPI 0.115                               |
| База данных    | PostgreSQL (asyncpg + SQLAlchemy 2.0 async) |
| Миграции       | Alembic                                     |
| Авторизация    | JWT (access 30 мин + refresh 1 день)        |
| Хэш паролей    | Argon2 (pwdlib)                             |
| AI             | Groq API (llama-3.3-70b-versatile)          |
| Файлы          | Локальная папка `media/`                    |
| Логи           | Ежедневные файлы в папке `logs/`            |

---

## Структура проекта

```
InvitationProject/
├── app/
│   ├── main.py               ← точка входа FastAPI, подключение всех роутеров
│   ├── config.py             ← настройки из .env
│   ├── database.py           ← SQLAlchemy engine + async session
│   ├── logging_config.py     ← настройка ежедневных лог-файлов
│   ├── utils.py              ← генерация slug (транслитерация кириллицы)
│   ├── init_db.py            ← скрипт для заполнения начальных данных
│   │
│   ├── auth/                 ← регистрация, вход, JWT, блокировка аккаунта
│   ├── categories/           ← категории мероприятий (свадьба, день рождения...)
│   ├── inv_templates/        ← шаблоны оформления приглашений
│   ├── invitations/          ← создание и управление приглашениями
│   ├── media/                ← загрузка и удаление фотографий
│   ├── rsvp/                 ← ответы гостей (RSVP)
│   ├── payments/             ← тарифные планы и платежи
│   ├── ai/                   ← генерация текста через Groq AI
│   └── admin/                ← панель администратора
│
├── alembic/                  ← миграции БД
│   └── versions/
│       ├── c79e...           ← создание таблицы users
│       ├── 936c...           ← добавление блокировки аккаунта
│       ├── a1b2...           ← добавление locked_until
│       ├── b1c2...           ← добавление full_name и is_admin
│       └── c2d3...           ← все остальные таблицы платформы
│
├── media/
│   ├── uploads/              ← загруженные фотографии
│   └── thumbs/               ← уменьшенные превью (300x300)
│
├── logs/
│   └── app.log               ← текущий лог (+ app.log.2026-03-01 и т.д.)
│
├── .env                      ← переменные окружения
├── alembic.ini
└── requirements/
    └── base_requirements.txt
```

---

## Быстрый старт

### 1. Установить зависимости

```bash
pip install -r requirements/base_requirements.txt
```

### 2. Настроить .env

Открыть файл `.env` и заполнить:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/invitation_db
JWT_SECRET_KEY=your-very-secret-key
GROQ_API_KEY=gsk_xxxxxxxx          # получить на groq.com (бесплатно)
PAYMENT_KASPI_PHONE=+77001234567   # ваш номер Kaspi для приёма платежей
```

### 3. Применить миграции

```bash
python -m alembic upgrade head
```

### 4. Заполнить начальные данные

```bash
python -m app.init_db
```

Создаёт:
- 9 категорий мероприятий (свадьба, день рождения, сүндет той и др.)
- 3 тарифных плана (Базовый 1990₸, Стандарт 3490₸, Премиум 5990₸)

### 5. Запустить сервер

```bash
# Разработка (с auto-reload)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Продакшн
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Документация API: http://localhost:8000/docs

---

## API Эндпоинты

### Авторизация — `/auth`

| Метод | Путь            | Что делает                          | Auth? |
|-------|-----------------|-------------------------------------|-------|
| POST  | /auth/register  | Регистрация                         | Нет   |
| POST  | /auth/login     | Вход (username + password)          | Нет   |
| POST  | /auth/refresh   | Обновить access token               | Cookie|
| POST  | /auth/logout    | Выход                               | Да    |
| GET   | /auth/me        | Данные текущего пользователя        | Да    |
| PUT   | /auth/me        | Изменить имя, email, пароль         | Да    |

**Регистрация:**
```json
POST /auth/register
{
  "username": "nurlan",
  "password": "mypassword123",
  "email": "nurlan@example.com",   // необязательно
  "full_name": "Нурлан Ахметов"    // необязательно
}
```

**Вход** использует форму (OAuth2):
```
username=nurlan&password=mypassword123
```

После входа сервер ставит два httpOnly cookie: `access_token` и `refresh_token`.
Все защищённые запросы читают токен из cookie автоматически.

**Блокировка:** 5 неверных паролей → аккаунт блокируется на 30 минут.

---

### Публичные — `/api/v1`

| Метод | Путь                         | Что делает                            |
|-------|------------------------------|---------------------------------------|
| GET   | /api/v1/categories           | Список категорий мероприятий          |
| GET   | /api/v1/templates            | Каталог шаблонов                      |
| GET   | /api/v1/templates?category=wedding | Фильтр по категории             |
| GET   | /api/v1/templates/{id}       | Детали шаблона                        |
| GET   | /api/v1/invite/{slug}        | Публичная страница приглашения        |
| POST  | /api/v1/invite/{slug}/rsvp   | Отправить RSVP-ответ гостя            |

---

### Приглашения — `/api/v1/my/invitations` (требуют авторизации)

| Метод  | Путь                                | Что делает                        |
|--------|-------------------------------------|-----------------------------------|
| GET    | /api/v1/my/invitations              | Список моих приглашений           |
| POST   | /api/v1/my/invitations              | Создать приглашение               |
| GET    | /api/v1/my/invitations/{id}         | Получить приглашение              |
| PUT    | /api/v1/my/invitations/{id}         | Редактировать (только 3 дня)      |
| DELETE | /api/v1/my/invitations/{id}         | Удалить                           |
| GET    | /api/v1/my/invitations/{id}/guests  | RSVP-ответы гостей + статистика   |

**Создание приглашения:**
```json
POST /api/v1/my/invitations
{
  "title": "Свадьба Нурлана и Айгерим",
  "category_id": 1,
  "template_id": "uuid-шаблона",   // необязательно
  "details": {
    "organizer_name": "Семья Ахметовых",
    "honoree_name": "Нурлан и Айгерим",
    "event_date": "2026-06-15",
    "event_time": "18:00",
    "venue_name": "Ресторан Алтын Орда",
    "venue_address": "ул. Абая 10, Алматы",
    "venue_map_url": "https://2gis.kz/...",
    "contact_phone": "+77001234567",
    "custom_fields": {
      "bride_name": "Айгерим",
      "groom_name": "Нурлан"
    }
  }
}
```

Ответ содержит `id` и `slug` созданного приглашения.
Slug генерируется автоматически: `nurlan-wedding-2026`.

**Ограничение:** редактирование доступно только 3 дня с момента создания.
После этого `PUT` вернёт `403 Forbidden`.

---

### Фотографии — `/api/v1/my/invitations/{id}/media`

| Метод  | Путь                                        | Что делает        |
|--------|---------------------------------------------|-------------------|
| GET    | /api/v1/my/invitations/{id}/media           | Список фото       |
| POST   | /api/v1/my/invitations/{id}/media           | Загрузить фото    |
| DELETE | /api/v1/my/invitations/{id}/media/{mediaId} | Удалить фото      |

**Загрузка фото** — multipart/form-data:
```
file: <binary>
media_type: photo | cover | background
display_style: circle | square | rectangle
caption: "Подпись к фото"
sort_order: 0
```

- Форматы: JPEG, PNG, WebP
- Максимальный размер: 5 МБ
- Файл сохраняется в `media/uploads/{invitation_id}/`
- Превью 300×300 создаётся в `media/thumbs/{invitation_id}/`
- URL файла: `/media/uploads/{invitation_id}/{filename}`

---

### AI генерация текста — `/api/v1/ai`

| Метод | Путь                     | Что делает                       |
|-------|--------------------------|----------------------------------|
| POST  | /api/v1/ai/generate-text | Сгенерировать текст приглашения  |

```json
POST /api/v1/ai/generate-text
{
  "category": "wedding",
  "organizer_name": "Семья Ахметовых",
  "honoree_name": "Нурлан и Айгерим",
  "event_date": "2026-06-15",
  "venue_name": "Ресторан Алтын Орда",
  "language": "ru",
  "custom_fields": {
    "bride_name": "Айгерим",
    "groom_name": "Нурлан"
  }
}
```

Ответ:
```json
{ "text": "Дорогие друзья и родственники! С радостью приглашаем вас..." }
```

Текст генерируется моделью `llama-3.3-70b-versatile` через Groq API.
Требуется `GROQ_API_KEY` в `.env`. Ключ бесплатный: https://console.groq.com

---

### Оплата — `/api/v1/payment`

| Метод | Путь                    | Что делает                          | Auth? |
|-------|-------------------------|-------------------------------------|-------|
| GET   | /api/v1/payment/plans   | Список тарифных планов              | Нет   |
| POST  | /api/v1/payment/create  | Создать платёж                      | Да    |
| GET   | /api/v1/payment/history | История платежей пользователя       | Да    |
| GET   | /api/v1/payment/{id}    | Статус конкретного платежа          | Да    |

**Как работает оплата:**

1. Пользователь выбирает тарифный план и вызывает:
```json
POST /api/v1/payment/create
{
  "invitation_id": "uuid-приглашения",
  "plan_id": 1
}
```

2. Сервер возвращает инструкцию:
```json
{
  "payment": { "id": "uuid", "status": "pending", ... },
  "kaspi_phone": "+77001234567",
  "amount": 1990.00,
  "currency": "KZT",
  "message": "Переведите 1990 KZT на номер +77001234567..."
}
```

3. Пользователь переводит деньги через Kaspi и ждёт подтверждения.

4. Администратор подтверждает платёж (см. раздел "Администратор").

5. Приглашение автоматически публикуется.

---

### RSVP — ответы гостей

**Гость** отправляет ответ по публичной ссылке (без авторизации):
```json
POST /api/v1/invite/{slug}/rsvp
{
  "guest_name": "Алия Сейткали",
  "guest_phone": "+77771234567",
  "will_attend": true,
  "guest_count": 2,
  "message": "Поздравляем! Обязательно придём!"
}
```

- Если номер телефона уже есть — ответ обновляется (не дублируется)
- Rate limit: 5 ответов с одного IP в час

**Организатор** просматривает ответы:
```
GET /api/v1/my/invitations/{id}/guests
```
Ответ содержит статистику: сколько придут, сколько не придут, общее число гостей.

---

### Администратор — `/api/v1/admin`

Требует `is_admin = true` у пользователя.

| Метод | Путь                               | Что делает                         |
|-------|------------------------------------|------------------------------------|
| GET   | /api/v1/admin/payments             | Все платежи                        |
| GET   | /api/v1/admin/payments?status=pending | Ожидающие подтверждения        |
| POST  | /api/v1/admin/payments/{id}/confirm | Подтвердить платёж → публикация   |
| POST  | /api/v1/admin/payments/{id}/reject  | Отклонить платёж                  |
| POST  | /api/v1/admin/categories           | Создать категорию                  |
| PUT   | /api/v1/admin/categories/{id}      | Изменить категорию                 |
| DELETE| /api/v1/admin/categories/{id}      | Удалить категорию                  |
| POST  | /api/v1/admin/templates            | Создать шаблон                     |
| PUT   | /api/v1/admin/templates/{id}       | Изменить шаблон                    |
| DELETE| /api/v1/admin/templates/{id}       | Удалить шаблон                     |
| GET   | /api/v1/admin/users                | Список пользователей               |
| POST  | /api/v1/admin/users/{id}/make-admin | Назначить администратором         |

**Как назначить первого администратора:**

Напрямую в базе данных:
```sql
UPDATE users SET is_admin = true WHERE username = 'your_username';
```

После этого можно назначать других через API.

---

## Жизненный цикл приглашения

```
[Создание] → status: draft, is_paid: false
     ↓
[Редактирование] — только 3 дня с момента создания
     ↓
[Оплата] → POST /payment/create → статус платежа: pending
     ↓
[Администратор подтверждает] → POST /admin/payments/{id}/confirm
     ↓
status: published, is_paid: true → ссылка /invite/{slug} становится доступной
     ↓
[По истечении срока] → status: expired (проверяется при каждом запросе)
```

---

## Статусы приглашения

| Статус      | Описание                                        |
|-------------|-------------------------------------------------|
| `draft`     | Черновик, не опубликован                        |
| `published` | Опубликован, ссылка доступна гостям             |
| `expired`   | Срок публикации истёк (expires_at < сейчас)     |
| `archived`  | Архивирован пользователем                       |

---

## Тарифные планы

| План      | Цена    | Гости   | Фото | Срок   |
|-----------|---------|---------|------|--------|
| Базовый   | 1990 ₸  | до 100  | 5    | 30 дней|
| Стандарт  | 3490 ₸  | до 500  | 15   | 60 дней|
| Премиум   | 5990 ₸  | без лим.| 30   | 90 дней|

---

## Логирование

Все действия с данными автоматически записываются в лог-файлы:

```
logs/
├── app.log              ← текущий день
├── app.log.2026-03-01   ← вчера
├── app.log.2026-02-29   ← позавчера
└── ...                  ← хранится 30 дней
```

Формат строки лога:
```
2026-03-01 14:35:22 | INFO     | invitation_app.auth | User registered: username=nurlan
2026-03-01 14:36:01 | INFO     | invitation_app.invitations | Invitation created: id=abc slug=nurlan-wedding-2026
2026-03-01 14:40:15 | INFO     | invitation_app.payments | Payment confirmed: payment_id=xyz invitation_id=abc
```

---

## Медиафайлы

Файлы хранятся локально в папке `media/`:

```
media/
├── uploads/
│   └── {invitation_id}/
│       ├── abc123.jpg       ← оригинал
│       └── def456.png
└── thumbs/
    └── {invitation_id}/
        ├── abc123.jpg       ← превью 300×300
        └── def456.png
```

Файлы доступны через URL:
- Оригинал: `http://localhost:8000/media/uploads/{id}/filename.jpg`
- Превью: `http://localhost:8000/media/thumbs/{id}/filename.jpg`

---

## Переменные окружения (.env)

| Переменная             | Описание                              | Обязательно |
|------------------------|---------------------------------------|-------------|
| `DATABASE_URL`         | Строка подключения к PostgreSQL       | Да          |
| `JWT_SECRET_KEY`       | Секретный ключ для JWT                | Да          |
| `JWT_ALGORITHM`        | Алгоритм JWT (HS256)                  | Нет         |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Срок access token (30 мин)   | Нет         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Срок refresh token (1 день)  | Нет         |
| `GROQ_API_KEY`         | Ключ Groq API для AI генерации        | Нет*        |
| `GROQ_MODEL`           | Модель (llama-3.3-70b-versatile)      | Нет         |
| `PAYMENT_KASPI_PHONE`  | Номер Kaspi для приёма платежей       | Да          |
| `PAYMENT_DESCRIPTION`  | Описание платежа                      | Нет         |
| `MEDIA_DIR`            | Папка для загрузок (media/uploads)    | Нет         |
| `MEDIA_THUMBS_DIR`     | Папка для превью (media/thumbs)       | Нет         |
| `MAX_FILE_SIZE_MB`     | Максимальный размер файла (5 МБ)      | Нет         |
| `LOGS_DIR`             | Папка для логов (logs)                | Нет         |
| `ENVIRONMENT`          | development / production              | Нет         |
| `FRONTEND_URL`         | URL фронтенда для CORS                | Нет         |

*без `GROQ_API_KEY` эндпоинт `/ai/generate-text` вернёт 503

---

## Полезные команды

```bash
# Применить миграции
python -m alembic upgrade head

# Откатить последнюю миграцию
python -m alembic downgrade -1

# Заполнить начальные данные
python -m app.init_db

# Запустить сервер (разработка)
python -m uvicorn app.main:app --reload --port 8000

# Сгенерировать миграцию после изменения моделей
python -m alembic revision --autogenerate -m "описание изменений"
```
