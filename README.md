# BP Tracker Bot

A personal Telegram bot for logging blood pressure readings. Send a reading, get it classified and saved, and review recent history, all from Telegram.

> **Disclaimer:** This is a tracking tool, not medical advice. It does not diagnose anything. Talk to a doctor about your readings.

## Features

- Log a reading with one command: `/log 120/80 72`
- Automatic category (green / yellow / orange / red) based on systolic and diastolic
- Automatic morning / evening tag, based on Kuala Lumpur time
- Urgent warning for very high readings
- View your 5 most recent readings
- Delete your most recent reading if you made a typo
- Locked to a single Telegram user: everyone else is ignored

## Commands

| Command | What it does |
|---|---|
| `/log 120/80 72` | Save a reading (`systolic/diastolic pulse`) |
| `/recent` | Show your last 5 readings, newest first |
| `/del_recent` | Delete your most recent reading |
| `/help` or `/start` | Show usage instructions |

## Categories

The higher of the two numbers decides the category. Rules are checked from most to least severe, so every reading gets exactly one category.

| Category | Rule |
|---|---|
| 🔴 Red (Stage 2 range) | systolic ≥ 140 **or** diastolic ≥ 90 |
| 🟠 Orange (Stage 1 range) | systolic 130-139 **or** diastolic 80-89 |
| 🟡 Yellow (Elevated) | systolic 120-129 **and** diastolic < 80 |
| 🟢 Green (Normal) | systolic < 120 **and** diastolic < 80 |

Readings with systolic ≥ 180 or diastolic ≥ 120 also show an urgent-care note.

**Morning** is before 12:00 local time, **evening** is 12:00 onward.

The thresholds live in `src/bpbot/services/classification.py` and are covered by boundary tests.

## Tech stack

- **Python 3.12**, managed with [uv](https://docs.astral.sh/uv/)
- **python-telegram-bot** (with the `webhooks` extra) for the Telegram interface: long polling locally, webhooks in production
- **Supabase** (PostgreSQL) for storage
- **Ruff** for linting and formatting, **pytest** for tests

## Project structure

```
bp-tracker-bot/
├── schema.sql                     # database schema (run in Supabase SQL editor)
├── scripts/
│   └── smoke_db.py                # end-to-end check of the database layer
├── src/bpbot/
│   ├── main.py                    # entry point: builds the bot, registers commands
│   ├── config.py                  # env vars and timezone constant
│   ├── handlers/
│   │   ├── commands.py            # one thin handler per command
│   │   └── formatting.py          # all user-facing text
│   ├── services/                  # pure logic, no Telegram or database
│   │   ├── classification.py      # (systolic, diastolic) -> category
│   │   ├── time_of_day.py         # timestamp -> morning/evening
│   │   └── parsing.py             # "120/80 72" -> validated numbers
│   └── db/
│       ├── client.py              # Supabase client
│       └── readings_repo.py       # insert, get recent, delete latest (table name from settings)
└── tests/                         # unit tests for the pure logic
```

The layers depend inward: handlers know Telegram, the repository knows Supabase, and services know neither. This keeps the logic easy to test.

## Setup (local)

### Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Two Telegram bot tokens from [@BotFather](https://t.me/BotFather): one for local dev, one for production. Using separate tokens means polling locally never conflicts with the deployed webhook.
- Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
- A [Supabase](https://supabase.com) project

### Steps

```bash
git clone <your-repo-url>
cd bp-tracker-bot
uv sync
cp .env.example .env      # then fill in the values
```

1. In Supabase, open **SQL Editor** and run the contents of `schema.sql`. This creates both `bp_readings` (prod) and `bp_readings_dev` (local dev), so test logging never touches real data.
2. Fill in `.env` with the **dev** bot token and the **dev** table:

| Variable | Local value | Where to find it |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | dev bot token | BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | your Telegram ID | @userinfobot |
| `SUPABASE_URL` | your project URL | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | your service_role key | Supabase → Settings → API → `service_role` key |
| `READINGS_TABLE` | `bp_readings_dev` | — |
| `WEBHOOK_BASE_URL` | leave empty | production only, see Deployment |
| `WEBHOOK_SECRET` | leave empty | production only, see Deployment |

Leaving `WEBHOOK_BASE_URL` unset is what makes the bot poll instead of trying to start a webhook server locally.

3. Run the bot:

```bash
uv run python -m bpbot.main
```

4. Optional: check the database layer against your real project:

```bash
uv run python scripts/smoke_db.py
```

## Development

```bash
uv run pytest -v            # run tests
uv run ruff check .         # lint
uv run ruff format .        # format
```

Workflow: create a feature branch, open a PR, merge into `main`.

## Data model

One schema, used by two tables in the same Supabase project:

| Table | Used by |
|---|---|
| `bp_readings` | production (Render) |
| `bp_readings_dev` | local development |

`bp_readings_dev` is created with `like public.bp_readings including all`, so it has identical columns, constraints and indexes. Which table the bot reads and writes is controlled by the `READINGS_TABLE` environment variable, read in `config.py` and applied in `db/readings_repo.py`. This keeps local testing completely separate from real data while sharing one Supabase project and one service-role key.

| Column | Type | Notes |
|---|---|---|
| id | uuid | primary key, generated |
| user_id | bigint | Telegram user ID |
| systolic | smallint | 50-300 |
| diastolic | smallint | 30-200, must be lower than systolic |
| pulse | smallint | 20-250 |
| category | text | green / yellow / orange / red |
| time_of_day | text | morning / evening |
| created_at | timestamptz | stored in UTC |

Value ranges are enforced both in the bot and by database CHECK constraints. Row Level Security is enabled with no policies on both tables, so only the service-role key (used by the bot) can access the data. Each table has an index on `(user_id, created_at desc)`.

## Deployment

Production runs on a **Render free web service** using **Telegram webhooks**. Locally the bot uses long polling. The mode is controlled by `WEBHOOK_BASE_URL` in `config.py`: when it's set, the bot starts a webhook server (`app.run_webhook`); when it's empty, it polls (`app.run_polling`). This is set explicitly in Render's environment variables rather than relying on Render's auto-injected `RENDER_EXTERNAL_URL`, since that turned out not to be picked up reliably.

Free Render web services spin down after 15 minutes without inbound traffic. The next incoming webhook request wakes the service, which takes roughly 30-60 seconds, so the first reply after a quiet period is delayed but not lost, since Telegram retries failed deliveries. A retry landing mid-spin-up can occasionally cause a duplicate reading; `/del_recent` removes it. A proper duplicate guard is on the roadmap.

### Dev/prod separation

Local dev and Render production are kept fully separate, using one Supabase project:

| | Bot token | `READINGS_TABLE` | Mode |
|---|---|---|---|
| **Local dev** | dev bot | `bp_readings_dev` | long polling |
| **Render prod** | prod bot | `bp_readings` | webhook |

This means running the bot locally for testing never touches production data or the production bot's webhook.

### Render settings

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Region | Singapore |
| Build command | `pip install uv && uv sync --frozen --no-dev` |
| Start command | `uv run --frozen --no-dev python -m bpbot.main` |
| Instance type | Free |

Environment variables set in Render's **Environment** tab:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | production bot token |
| `TELEGRAM_ALLOWED_USER_ID` | your Telegram ID |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service_role key |
| `READINGS_TABLE` | `bp_readings` |
| `WEBHOOK_BASE_URL` | the service's own Render URL, e.g. `https://bp-tracker-bot-xxxx.onrender.com` (no trailing slash) |
| `WEBHOOK_SECRET` | a generated secret (below); Telegram must send this in its webhook requests or they're rejected |

Generate the secret with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Merging a code change into `main` triggers an automatic redeploy. Changing an environment variable in the Render dashboard also redeploys on its own; no push needed for that.

### Dependency note

Webhook mode requires the `webhooks` extra: `uv add "python-telegram-bot[webhooks]"`. Make sure `uv.lock` is committed after adding it, since Render's build (`uv sync --frozen`) installs strictly from the lockfile and silently won't include the extra otherwise.

### Verifying the webhook

```bash
curl "https://api.telegram.org/bot<PROD_TOKEN>/getWebhookInfo"
```

`url` should show your Render URL, and `last_error_message` should be empty.

### Optional: keep the service awake

Point a free uptime monitor (for example UptimeRobot, 5-minute interval) at the Render URL. This removes the cold-start delay but uses most of the 750 free monthly instance hours, and it is not an officially supported way to keep a free service running.

## Security notes

- `.env` is git-ignored. Never commit tokens or the service-role key.
- The service-role key bypasses Row Level Security. Treat it like a root password.
- All database queries are filtered by `user_id`.
- The bot silently ignores every Telegram user except the one in `TELEGRAM_ALLOWED_USER_ID`.
- In webhook mode, requests without the correct `WEBHOOK_SECRET` header are rejected.
- Dev and prod share one Supabase service-role key but write to different tables (`READINGS_TABLE`), so a misconfigured table name is the main risk to watch for after any config change.
- HTTP request logging is set to WARNING so the bot token never appears in logs.
- If a token leaks: revoke it with BotFather (`/revoke`) and rotate the Supabase key. Deleting the commit is not enough.

## Roadmap

- [x] MVP: `/log`, `/recent`, `/del_recent`, `/help`
- [x] Deployed to Render with webhooks, dev/prod separation (separate bot tokens and tables)
- [ ] Duplicate-reading guard (webhook retries can occasionally double-submit)
- [ ] Confirmation button on `/del_recent`
- [ ] Backdated readings (log a reading taken earlier)
- [ ] Analytics: daily/weekly averages, morning vs evening comparison
- [ ] Reminders
- [ ] CSV export and charts

## License

Personal project. Add a license if you decide to share it.