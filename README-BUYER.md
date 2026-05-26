# ProductPhoto AI — Документация для владельца

> **ProductPhoto AI** — Telegram-бот для AI-генерации коммерческих фото товаров. Пользователь загружает фото товара, бот удаляет фон и генерирует профессиональные изображения в выбранном стиле.

---

## 📋 Содержание

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Технологии](#технологии)
4. [Структура проекта](#структура-проекта)
5. [Админ-панель](#админ-панель)
6. [API и интеграции](#api-и-интеграции)
7. [База данных](#база-данных)
8. [Безопасность](#безопасность)
9. [Монетизация](#монетизация)
10. [Поддержка и обслуживание](#поддержка-и-обслуживание)

---

## Обзор проекта

### Что делает бот

```
Пользователь → Загружает фото товара
      ↓
Бот → Удаляет фон (Remove.bg)
      ↓
Бот → Генерирует 4 изображения через Fal.ai (flux_schnell / flux_dev)
      ↓
Бот → Накладывает водяной знак (для free-пользователей)
      ↓
Бот → Загружает в Supabase Storage
      ↓
Пользователь ← Получает готовые фото + кнопки (регенерация / upscale)
```

### Функции

| Функция | Описание |
|---------|----------|
| **Генерация фото** | 4 стиля: White Background, Lifestyle, Studio Premium, Social Media |
| **Upscale** | Увеличение разрешения 2x через Real-ESRGAN |
| **Мультиязычность** | English + Russian |
| **Кредиты** | 1 генерация = 1 кредит. Пополнение через Stars / Stripe |
| **Реферальная программа** | +10 кредитов пригласившему, +5 приглашённому |
| **Подписки** | Free, Starter (100 cr/mo), Pro (500 cr/mo) |
| **Админ-панель** | Статистика, управление пользователями, рассылка, настройки |

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        Пользователь                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Telegram API                             │
│              Webhook: /webhook/telegram                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Caddy (авто-SSL) → FastAPI (uvicorn) → aiogram Bot        │
│  Порт 8000 внутри Docker-сети                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│   PostgreSQL 15     │   │   Supabase Storage  │
│   (users, gens,     │   │   (генерированные   │
│    payments)        │   │    изображения)     │
└─────────────────────┘   └─────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│              Внешние API (через интернет)                  │
│  Remove.bg → Fal.ai (flux) → Telegram Stars → Stripe       │
└─────────────────────────────────────────────────────────────┘
```

---

## Технологии

| Компонент | Технология |
|-----------|-----------|
| **Backend** | Python 3.11, FastAPI, uvicorn |
| **Bot** | aiogram 3.x, FSM |
| **Database** | PostgreSQL 15, SQLAlchemy 2.0 (async), asyncpg |
| **Migrations** | Alembic |
| **AI Generation** | Fal.ai (flux_schnell / flux_dev) |
| **Background Removal** | Remove.bg API |
| **Storage** | Supabase Storage |
| **Payments** | Telegram Stars, Stripe |
| **Queue** | Asyncio Semaphore (max 5 параллельно) |
| **Web Server** | Caddy (авто-SSL) |
| **Deployment** | Docker, Docker Compose |

---

## Структура проекта

```
backend/
├── .env                          # Переменные окружения (НЕ коммитить!)
├── .env.example                  # Шаблон переменных
├── docker-compose.yml            # Docker Compose (local dev)
├── Dockerfile                    # Многослойная сборка
├── requirements.txt              # Зависимости Python
├── alembic.ini                   # Миграции БД
├── README.md                     # Общая документация
├── README-BUYER.md               # Этот файл
├── DEPLOYMENT.md                 # Гайд по развёртыванию
└── app/
    ├── main.py                   # FastAPI + lifespan + webhooks
    ├── config/__init__.py        # Pydantic Settings
    ├── database/
    │   ├── engine.py             # SQLAlchemy async engine
    │   └── repositories.py       # CRUD операции
    ├── models/
    │   ├── user.py               # Пользователь
    │   ├── generation.py         # Генерации
    │   ├── payment.py            # Платежи
    │   ├── referral.py           # Рефералы
    │   └── settings.py           # Динамические настройки
    ├── bot/
    │   ├── handlers/
    │   │   ├── commands.py       # /start, /help, /balance
    │   │   ├── photos.py         # Обработка фото
    │   │   ├── callbacks.py      # Inline кнопки
    │   │   ├── payments.py       # Telegram Stars
    │   │   └── admin.py          # Админ-панель
    │   ├── services/
    │   │   ├── generator.py      # Полный пайплайн генерации
    │   │   ├── upscaler.py       # Апскейл
    │   │   ├── background_removal.py
    │   │   ├── fal_client.py     # Клиент Fal.ai
    │   │   └── task_queue.py     # Очередь задач
    │   ├── i18n.py               # Переводы EN/RU
    │   ├── keyboards.py          # Inline keyboards
    │   └── states.py             # FSM состояния
    ├── payments/
    │   ├── telegram_stars.py     # Stars инвойсы
    │   ├── stripe_client.py      # Stripe checkout
    │   └── credits.py            # Цены
    ├── prompts/
    │   └── templates.py          # Промпты для стилей
    └── utils/
        ├── image.py              # Pillow: watermark, resize
        └── storage.py            # Supabase upload/download
```

---

## Админ-панель

### Доступ

Отправьте боту команду `/admin`. Доступ только для владельца (Telegram ID указан в `.env` или коде).

### Разделы

| Раздел | Функции |
|--------|---------|
| **📊 Dashboard** | Пользователи, генерации, доход за сегодня/неделю/месяц |
| **👤 Пользователи** | Список с пагинацией, поиск, профиль, +/- кредиты, бан/разбан |
| **🎨 Генерации** | По стилям, по статусу (pending/completed/failed), повторить failed |
| **💰 Финансы** | Все платежи, Stars, Stripe, популярные тарифы, возвраты |
| **📢 Рассылка** | Рассылка всем/по языку/по тарифу с предпросмотром |
| **⚙️ Настройки** | Цены, стартовый бонус, включить/выключить генерацию |

---

## API и интеграции

### Обязательные API-ключи

| Сервис | Для чего | Где получить |
|--------|---------|-------------|
| **Telegram Bot Token** | Работа бота | @BotFather |
| **Fal.ai** | Генерация изображений | fal.ai |
| **Remove.bg** | Удаление фона | remove.bg |
| **Supabase** | Хранение фото | supabase.com |
| **Stripe** | Карточные платежи | stripe.com |

### Webhook endpoints

| Endpoint | Описание |
|----------|---------|
| `POST /webhook/telegram` | Получение обновлений от Telegram |
| `POST /webhook/stripe` | События оплаты Stripe |
| `GET /health` | Health check |
| `GET /admin/queue` | Статус очереди задач |

---

## База данных

### Таблицы

| Таблица | Назначение |
|---------|-----------|
| `users` | Пользователи, кредиты, язык, подписка, бан |
| `generations` | История генераций, статус, URL |
| `payments` | Платежи Stars + Stripe |
| `referrals` | Реферальные связи |
| `bot_settings` | Динамические настройки |

### Важные поля `users`

```sql
- telegram_id      BIGINT (ID пользователя в Telegram)
- credits          INTEGER (баланс кредитов)
- language         VARCHAR(5) ('en' или 'ru')
- subscription_type VARCHAR(20) ('free', 'starter', 'pro')
- is_banned        BOOLEAN (забанен или нет)
- referral_code    VARCHAR(8) (уникальный код)
```

---

## Безопасность

### Что уже реализовано

- ✅ Доступ к `/admin` только по Telegram ID владельца
- ✅ Вебхук Telegram защищён секретом
- ✅ База данных в изолированной Docker-сети
- ✅ HTTPS через Caddy (автоматические сертификаты)

### Рекомендации

- Храните `.env` в безопасности — там все ключи API
- Не коммитьте `.env` в Git (уже в `.gitignore`)
- Регулярно обновляйте зависимости: `pip list --outdated`
- Делайте бэкапы базы данных

---

## Монетизация

### Модели дохода

| Модель | Описание |
|--------|---------|
| **Кредиты** | Разовая покупка пакетов (50/100/500) |
| **Подписки** | Ежемесячная: Starter (100 cr), Pro (500 cr) |
| **Telegram Stars** | Нативная оплата внутри Telegram |
| **Stripe** | Карточные платежи |

### Цены (настраиваются в `app/payments/credits.py`)

```python
CREDIT_PACKS = {
    "50": {"price_stars": 50, "price_usd": 5.00},
    "100": {"price_stars": 100, "price_usd": 9.00},
    "500": {"price_stars": 450, "price_usd": 39.00},
}

SUBSCRIPTIONS = {
    "starter": {"credits": 100, "price_stars": 100, "price_usd": 9.99},
    "pro": {"credits": 500, "price_stars": 450, "price_usd": 39.99},
}
```

---

## Поддержка и обслуживание

### Ежедневные задачи

```bash
# Просмотр логов
ssh root@95.182.80.83
cd /opt/productphoto-bot
docker compose logs -f app

# Перезапуск при проблемах
docker compose restart app
```

### Еженедельные задачи

- Проверка свободного места на диске: `df -h`
- Проверка статуса подписок
- Анализ статистики через `/admin`

### Обновление бота

```bash
# На локальной машине
# Внесите изменения → git commit → git push

# На сервере
ssh root@95.182.80.83
cd /opt/productphoto-bot
git pull origin main
docker compose down
docker compose up --build -d
```

### Бэкап базы данных

```bash
# Экспорт
docker exec productphoto-db pg_dump -U postgres productphoto > backup_$(date +%Y%m%d).sql

# Импорт
cat backup_20250101.sql | docker exec -i productphoto-db psql -U postgres -d productphoto
```

---

## Контакты и поддержка

- **Владелец Telegram ID:** `1003330009`
- **Бот:** `@productphoto_ai_bot`
- **Публичный URL:** `https://productphoto.95.182.80.83.nip.io`

---

*Последнее обновление: 2026-05-26*
