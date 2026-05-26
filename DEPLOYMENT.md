# DEPLOYMENT.md — Гайд по развёртыванию на VPS

> Пошаговая инструкция по развёртыванию ProductPhoto AI на собственном VPS с Docker, Docker Compose и Caddy.

---

## 📋 Требования

### Сервер (VPS)

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| **OS** | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| **CPU** | 1 vCPU | 2 vCPU |
| **RAM** | 1 GB | 2 GB |
| **Disk** | 20 GB SSD | 40 GB SSD |
| **Network** | Публичный IP | Публичный IP + домен |

### Домен

- Можно использовать `nip.io` (бесплатно): `https://productphoto.YOUR-IP.nip.io`
- Или свой домен с A-записью на IP сервера

---

## 🔧 Шаг 1: Подготовка сервера

### 1.1 Подключение

```bash
# С локальной машины
ssh root@YOUR_SERVER_IP
# Введите пароль root
```

### 1.2 Обновление системы

```bash
apt update && apt upgrade -y
```

### 1.3 Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt install -y docker-compose-plugin

# Проверка
docker --version
docker compose version
```

### 1.4 Настройка timezone

```bash
timedatectl set-timezone Europe/Moscow
timedatectl status
```

---

## 📦 Шаг 2: Клонирование проекта

### 2.1 Создание директории

```bash
mkdir -p /opt/productphoto-bot
cd /opt/productphoto-bot
```

### 2.2 Клонирование из GitHub

```bash
git clone https://github.com/staralex338/productphoto-bot.git .
```

Или загрузите файлы через SFTP/SCP.

---

## 🔐 Шаг 3: Настройка окружения

### 3.1 Создание .env файла

```bash
cp .env.example .env
nano .env
```

Заполните ВСЕ переменные (см. `.env.example` для описания каждой).

### 3.2 Обязательные переменные

```ini
# Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_WEBHOOK_URL=https://productphoto.YOUR-IP.nip.io/webhook/telegram
TELEGRAM_WEBHOOK_SECRET=random-secret-string-min-32-chars

# Database (локальная в Docker)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/productphoto

# Supabase (только Storage!)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_STORAGE_BUCKET=product-images

# AI
FAL_KEY=your-fal-key
REMOVE_BG_API_KEY=your-removebg-key

# Stripe (опционально для карт)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# App
APP_NAME=ProductPhoto AI
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Business
FREE_CREDITS_ON_START=3
REFERRAL_BONUS_INVITER=10
REFERRAL_BONUS_INVITED=5
```

### 3.3 Сохранение

```bash
# Ctrl+O, Enter, Ctrl+X (в nano)
chmod 600 .env  # Только владелец может читать
```

---

## 🚀 Шаг 4: Первый запуск

### 4.1 Сборка и запуск

```bash
cd /opt/productphoto-bot
docker compose up --build -d
```

### 4.2 Проверка статуса

```bash
docker compose ps
```

Должно показать:
```
NAME                 STATUS          PORTS
productphoto-app     Up 10 seconds   8000/tcp
productphoto-caddy   Up 10 seconds   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
productphoto-db      Up 10 seconds   5432/tcp
```

### 4.3 Проверка логов

```bash
docker compose logs -f app
```

Должно быть:
```
🚀 Starting up ProductPhoto AI...
Bot handlers registered.
Database tables initialized successfully.
Database connected.
Application startup complete.
```

Нажмите `Ctrl+C` для выхода из логов.

---

## 🔗 Шаг 5: Настройка вебхука Telegram

### 5.1 Установка вебхука

Откройте в браузере или выполните с сервера:

```bash
curl -s "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://productphoto.YOUR-IP.nip.io/webhook/telegram&secret_token=YOUR_WEBHOOK_SECRET"
```

### 5.2 Проверка вебхука

```bash
curl -s "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

Должно показать:
```json
{
  "ok": true,
  "result": {
    "url": "https://productphoto.YOUR-IP.nip.io/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## ✅ Шаг 6: Проверка работы

### 6.1 Health check

```bash
curl https://productphoto.YOUR-IP.nip.io/health
```

Должно вернуть: `{"status":"ok"}`

### 6.2 Проверка в Telegram

1. Найдите бота по @username
2. Отправьте `/start`
3. Должно появиться приветственное сообщение с выбором языка

### 6.3 Тест генерации

1. Отправьте фото товара
2. Выберите стиль
3. Подождите 10-30 секунд
4. Должны прийти 4 сгенерированных фото

---

## 🔁 Шаг 7: Обновление бота

### 7.1 Обновление кода

```bash
cd /opt/productphoto-bot
git pull origin main
```

### 7.2 Пересборка

```bash
docker compose down
docker compose up --build -d
```

### 7.3 Проверка после обновления

```bash
docker compose ps
docker compose logs --tail=20 app
```

---

## 🛠️ Полезные команды

### Управление контейнерами

```bash
# Остановка
docker compose down

# Перезапуск
docker compose restart app

# Перезапуск только базы
docker compose restart db

# Просмотр логов в реальном времени
docker compose logs -f app

# Логи за последние 5 минут
docker compose logs --since="5m" app
```

### Работа с базой данных

```bash
# Подключение к PostgreSQL
docker compose exec db psql -U postgres -d productphoto

# Список таблиц
\dt

# Выход
\q

# Ручное добавление колонки (если миграция не применилась)
echo "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'en';" | docker compose exec -T db psql -U postgres -d productphoto
```

### Очистка

```bash
# Удалить все контейнеры и данные (!)
docker compose down -v

# Удалить неиспользуемые образы
docker image prune -a

# Удалить все volumes (!)
docker volume prune
```

---

## 🔒 Безопасность

### Firewall (UFW)

```bash
apt install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### SSL-сертификаты

Caddy автоматически получает и обновляет Let's Encrypt сертификаты. Ничего настраивать не нужно!

### Fail2ban (опционально)

```bash
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 📊 Мониторинг

### Проверка ресурсов

```bash
# CPU/RAM
top

# Диск
df -h

# Docker stats
docker stats
```

### Логи

```bash
# Логи приложения
docker compose logs -f app

# Логи базы
docker compose logs -f db

# Логи Caddy
docker compose logs -f caddy
```

---

## 🚨 Решение проблем

### "column does not exist"

```bash
# Проверить структуру таблицы
echo "SELECT column_name FROM information_schema.columns WHERE table_name = 'users';" | docker compose exec -T db psql -U postgres -d productphoto

# Добавить недостающую колонку
echo "ALTER TABLE users ADD COLUMN IF NOT EXISTS column_name TYPE;" | docker compose exec -T db psql -U postgres -d productphoto
```

### "400 Bad Request" на webhook

```bash
# Проверить URL вебхука
curl -s "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"

# Сбросить и установить заново
curl -s "https://api.telegram.org/botYOUR_TOKEN/deleteWebhook"
curl -s "https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=https://..."
```

### Контейнер unhealthy

```bash
# Пересобрать полностью
docker compose down
docker compose up --build -d

# Или только перезапустить
docker compose restart app
```

### Нет ответа от бота

1. Проверьте логи: `docker compose logs --tail=50 app`
2. Проверьте вебхук: `getWebhookInfo`
3. Проверьте health: `curl https://your-domain/health`
4. Убедитесь, что `.env` правильный
5. Проверьте, что API-ключи валидны

---

## 📞 Поддержка

Если что-то не работает:

1. Проверьте логи: `docker compose logs -f app`
2. Проверьте статус: `docker compose ps`
3. Проверьте health: `curl https://your-domain/health`
4. Создайте issue в GitHub репозитории

---

*Последнее обновление: 2026-05-26*
