# ProductPhoto AI

AI-powered Telegram bot for generating professional product photography.

Upload a product photo → Choose a style → Get stunning AI-generated images in seconds.

---

## Features (MVP)

- **4 Generation Styles:** White Background, Lifestyle, Studio Premium, Social Media Ad
- **Background Removal:** Automatic via Remove.bg / ClipDrop
- **AI Pipeline:** Flux + ControlNet via Fal.ai (primary), Replicate (fallback)
- **Credit System:** Free credits on signup, subscription plans, one-time packs
- **Payments:** Telegram Stars (primary), Stripe (secondary)
- **Referrals:** Invite friends, earn credits
- **History:** View past generations with details
- **Upscale:** Real-ESRGAN enhancement
- **Watermark:** Free users get branded images

---

## Tech Stack

- **Python 3.11+**
- **aiogram 3.x** — Telegram Bot Framework
- **FastAPI** — Web server & webhooks
- **Supabase** — PostgreSQL database & file storage
- **Fal.ai** — AI image generation
- **Railway.app / Render.com** — Deployment

---

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` with your keys (see [Environment Variables](#environment-variables) below).

### 3. Database Setup (Supabase)

1. Go to [supabase.com](https://supabase.com) and create a project
2. In **Project Settings → Database**, copy the connection string
3. In **Project Settings → API**, copy `Project URL` and `service_role_key`
4. Create a Storage bucket named `product-images`
5. Set bucket policy to allow public read (for generated images)
6. Run migrations:

```bash
# Install alembic if not already available
pip install alembic

# Run migrations
alembic upgrade head

# Or auto-create tables (development only)
python -c "import asyncio; from app.database.engine import init_db; asyncio.run(init_db())"
```

### 4. Run Locally

```bash
# Development (auto-reload)
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --port 8000

# With Docker Compose
docker-compose up --build
```

For webhook testing locally, use **ngrok**:

```bash
ngrok http 8000
# Then set TELEGRAM_WEBHOOK_URL to https://xxx.ngrok.io/webhook/telegram
```

---

## Telegram Bot Setup

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` and follow instructions
3. Copy the **HTTP API token**
4. Set bot name and description with `/setname`, `/setdescription`
5. (Optional) Enable Telegram Payments for Stars:
   - Send `/mybots` → select your bot → Payments
   - Choose a provider or use Telegram Stars (built-in)

---

## AI API Setup

1. **Fal.ai**: Sign up at [fal.ai](https://fal.ai), copy your API key
2. **Remove.bg**: Get a free key at [remove.bg](https://www.remove.bg/api)
3. (Optional) **Replicate**: Get token at [replicate.com](https://replicate.com)
4. (Optional) **ClipDrop**: Get key at [clipdrop.co](https://clipdrop.co)

---

## Payment Setup

### Telegram Stars (Primary)

No extra setup needed beyond bot token. Telegram Stars work natively.

1. Users tap "Buy Credits" → select item → "Pay with Telegram Stars"
2. Bot sends invoice via `sendInvoice`
3. User pays in Telegram
4. Bot receives `successful_payment` update
5. Credits added automatically

### Stripe (Secondary)

1. Create account at [stripe.com](https://stripe.com)
2. Get `Secret key` from Dashboard → Developers → API Keys
3. Create a webhook endpoint pointing to `https://your-domain/webhook/stripe`
4. Select events: `checkout.session.completed`
5. Copy `Webhook signing secret`
6. Add both keys to `.env`

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | From @BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_WEBHOOK_URL` | For prod | Public webhook URL | `https://app.com/webhook/telegram` |
| `TELEGRAM_WEBHOOK_SECRET` | ❌ | Webhook validation | `random-secret-string` |
| `DATABASE_URL` | ✅ | Supabase connection string | `postgresql+asyncpg://...` |
| `SUPABASE_URL` | ✅ | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | ✅ | Service role key | `eyJhbG...` |
| `SUPABASE_STORAGE_BUCKET` | ❌ | Storage bucket name | `product-images` |
| `FAL_KEY` | ✅ | Fal.ai API key | `your-fal-key` |
| `REMOVE_BG_API_KEY` | ✅ | Remove.bg API key | `your-rbg-key` |
| `REPLICATE_API_TOKEN` | ❌ | Fallback AI provider | `your-replicate-token` |
| `CLIPDROP_API_KEY` | ❌ | Fallback bg removal | `your-clipdrop-key` |
| `STRIPE_SECRET_KEY` | ❌ | Stripe secret key | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | ❌ | Stripe webhook secret | `whsec_...` |
| `APP_ENV` | ❌ | Environment | `development` / `production` |
| `DEBUG` | ❌ | Debug mode | `true` / `false` |

---

## Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
├── app/
│   ├── bot/
│   │   ├── handlers/           # Telegram message & callback handlers
│   │   │   ├── __init__.py
│   │   │   ├── commands.py     # /start, /help, /balance, /history
│   │   │   ├── photos.py       # Photo upload & validation
│   │   │   ├── callbacks.py    # Inline keyboard callbacks
│   │   │   └── payments.py     # Pre-checkout & successful payment
│   │   ├── services/           # Business logic
│   │   │   ├── storage.py      # File download from Telegram
│   │   │   ├── background_removal.py  # Remove.bg / ClipDrop
│   │   │   ├── fal_client.py   # Fal.ai API client
│   │   │   ├── generator.py    # Full generation pipeline
│   │   │   ├── upscaler.py     # Real-ESRGAN upscale
│   │   │   ├── task_queue.py   # Async task queue with semaphore
│   │   │   └── referrals.py    # Referral system logic
│   │   ├── keyboards.py        # Inline keyboard builders
│   │   ├── messages.py         # Text message templates
│   │   └── states.py           # FSM states
│   ├── config/                 # Configuration & settings
│   ├── database/               # DB engine & repositories
│   ├── models/                 # SQLAlchemy ORM models
│   ├── payments/               # Payment integrations
│   ├── prompts/                # AI prompt templates
│   ├── utils/                  # Image processing & storage
│   └── main.py                 # FastAPI entry point
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info |
| GET | `/health` | Health check (Docker/Railway) |
| GET | `/docs` | Swagger UI |
| POST | `/webhook/telegram` | Telegram updates |
| POST | `/webhook/fal` | Fal.ai callbacks |
| POST | `/webhook/stripe` | Stripe events |
| GET | `/admin/queue` | Task queue status |

---

## Deployment

### Railway.app (Recommended)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard (copy from `.env`)
4. Set `TELEGRAM_WEBHOOK_URL` to `https://your-app.up.railway.app/webhook/telegram`
5. Set `APP_ENV=production`
6. Deploy! Railway auto-detects Dockerfile

### Render.com

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New + → Web Service
3. Connect repo, select **Docker** runtime
4. Add environment variables
5. Set `APP_ENV=production`
6. Deploy!

### Docker (Self-hosted)

```bash
# Build
docker build -t productphoto-bot .

# Run
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name productphoto \
  productphoto-bot
```

---

## User Flow

```
/start
  → Welcome + Main Menu

📸 Generate Photo
  → Send product photo
  → Validate (size, format, dimensions)
  → Choose style (4 options)
  → Check credits → Deduct 1
  → Queue generation task
  → Receive 2-4 generated images
  → Buttons: Regenerate / Upscale

💰 Buy Credits
  → Choose plan or pack
  → Choose payment (Stars / Stripe)
  → Pay → Credits added automatically

📜 History
  → List past generations with details

👤 Profile
  → Credits, plan, referral code

🎁 Referral Program
  → Share link
  → +10 credits per friend, friend gets +5
```

---

## Architecture Decisions

- **No Celery/RabbitMQ**: Uses `asyncio.Semaphore` + background tasks for simplicity
- **No Redis**: FSM uses `MemoryStorage` (upgrade to Redis for multi-worker setups)
- **No Microservices**: Single FastAPI app for easy deployment
- **Supabase over AWS S3**: Simpler setup, built-in auth, PostgreSQL + Storage in one
- **Fal.ai over self-hosted**: No GPU infrastructure needed, pay-per-use

---

## Troubleshooting

**Bot doesn't respond:**
- Check `TELEGRAM_BOT_TOKEN` is correct
- Verify webhook URL is accessible
- Check `/health` endpoint

**Database connection errors:**
- Ensure `DATABASE_URL` uses `postgresql+asyncpg://` format
- Check Supabase connection string includes password
- Verify IP is allowlisted in Supabase

**Generation fails:**
- Check `FAL_KEY` is set
- Verify `REMOVE_BG_API_KEY` for background removal
- Check logs for specific error messages

**Payments not working:**
- For Stars: Bot must be started by user before invoice works
- For Stripe: Verify webhook secret and endpoint URL

---

## License

MIT
