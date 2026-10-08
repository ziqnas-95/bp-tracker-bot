# BP Tracker Bot

A Telegram bot for logging blood pressure readings, shared with family. Send a reading, get it classified and saved, and review history and monthly averages, all from Telegram.

> **Disclaimer:** This is a tracking tool, not medical advice. It does not diagnose anything. Talk to a doctor about your readings.

## Features

- Log a reading with one command: `/log 120/80 72`
- Automatic category (green / yellow / orange / red) based on systolic and diastolic
- Automatic morning / evening tag, based on Kuala Lumpur time
- Urgent warning for very high readings
- View recent readings (5 or 20)
- Monthly summary with the average BP and pulse for any month this year
- Delete your most recent reading if you made a typo
- Daily reminder at 6:00 if you haven't logged a reading yet that day
- Shared with family via a join code, no public/open access
- Guards against duplicate entries if Telegram retries a message delivery

## Commands

| Command | What it does |
|---|---|
| `/join <code>` | Join the bot with the family join code |
| `/log 120/80 72` | Save a reading (`systolic/diastolic pulse`) |
| `/recent` | Show your last 5 readings, newest first |
| `/recent20` | Show your last 20 readings, newest first |
| `/month` | Summary and average for the current month |
| `/month <1-12>` | Summary and average for that month this year |
| `/del_recent` | Delete your most recent reading |
| `/help` or `/start` | Show usage instructions |

`/help` and `/start` work before joining. Send `/join <code>` in a private chat with the bot. Other commands require membership; if you have not joined, the bot tells you how.

## Categories

The higher of the two numbers decides the category. Rules are checked from most to least severe, so every reading gets exactly one category.

| Category | Rule |
|---|---|
| 🔴 Red (Stage 2 range) | systolic ≥ 140 **or** diastolic ≥ 90 |
| 🟠 Orange (Stage 1 range) | systolic 130-139 **or** diastolic 80-89 |
| 🟡 Yellow (Elevated) | systolic 120-129 **and** diastolic < 80 |
| 🟢 Green (Normal) | systolic < 120 **and** diastolic < 80 |

Readings with systolic ≥ 180 or diastolic ≥ 120 also show an urgent-care note.

**Morning** is before 12:00 local time, **evening** is 12:00 onward. This still drives the daily reminder logic even though it's no longer shown on `/recent`/`/recent20` lines.

The thresholds live in `src/bpbot/services/classification.py` and are covered by boundary tests.

## Tech stack

- **Python 3.12**, managed with [uv](https://docs.astral.sh/uv/)
- **python-telegram-bot** (with the `webhooks` and `job-queue` extras) for the Telegram interface and the daily reminder scheduler: long polling locally, webhooks in production
- **Supabase** (PostgreSQL) for storage
- **Ruff** for linting and formatting, **pytest** for tests

## Project structure

```
bp-tracker-bot/
├── schema.sql                     # database schema (run in Supabase SQL editor)
├── git_cmd.md                     # personal git command reference
├── scripts/
│   ├── smoke_db.py                # end-to-end check of the readings database layer
│   └── smoke_dedup.py             # checks the duplicate-update guard
├── src/bpbot/
│   ├── main.py                    # entry point: builds the bot, registers handlers, schedules the reminder job
│   ├── config.py                  # env vars and timezone constant
│   ├── handlers/
│   │   ├── commands.py            # one thin handler per command
│   │   ├── formatting.py          # all user-facing text
│   │   ├── dedup.py               # blocks re-processing a duplicate Telegram update
│   │   └── membership.py          # blocks commands from non-members (except /start, /help, /join)
│   ├── services/                  # pure logic, no Telegram or database
│   │   ├── classification.py      # (systolic, diastolic) -> category
│   │   ├── time_of_day.py         # timestamp -> morning/evening, month/day boundaries
│   │   ├── parsing.py             # "/log" and "/month" argument parsing and validation
│   │   ├── analytics.py           # monthly averages
│   │   └── reminders.py           # daily job: who hasn't logged today
│   └── db/
│       ├── client.py              # Supabase client
│       ├── readings_repo.py       # insert, get recent, get month, delete latest, has-logged-today
│       ├── users_repo.py          # membership checks and joining
│       └── dedup_repo.py          # records processed Telegram update_ids
└── tests/                         # unit tests for the pure logic
```

The layers depend inward: handlers know Telegram, the repositories know Supabase, and services know neither. This keeps the logic easy to test.

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

1. In Supabase, open **SQL Editor** and run the contents of `schema.sql`. This creates the prod and dev versions of every table (`bp_readings` / `bp_readings_dev`, `users` / `users_dev`, `processed_updates` / `processed_updates_dev`), and seeds the owner (you) into both `users` tables so you never need to `/join` yourself.
2. Fill in `.env` with the **dev** bot token and the **dev** table:

| Variable | Local value | Where to find it |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | dev bot token | BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | your Telegram ID | @userinfobot |
| `SUPABASE_URL` | your project URL | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | your service_role key | Supabase → Settings → API → `service_role` key |
| `READINGS_TABLE` | `bp_readings_dev` | — |
| `FAMILY_JOIN_CODE` | any value for local testing | shared with family in production, see Deployment |
| `WEBHOOK_BASE_URL` | leave empty | production only, see Deployment |
| `WEBHOOK_SECRET` | leave empty | production only, see Deployment |

Leaving `WEBHOOK_BASE_URL` unset is what makes the bot poll instead of trying to start a webhook server locally.

3. Run the bot:

```bash
uv run python -m bpbot.main
```

4. Optional: check the database layers against your real project:

```bash
uv run python scripts/smoke_db.py
uv run python scripts/smoke_dedup.py
```

## Development

```bash
uv run pytest -v            # run tests
uv run ruff check .         # lint
uv run ruff format .        # format
```

Workflow: create a feature branch, open a PR, merge into `main`. See `git_cmd.md` for the exact commands used day to day on this project.

## Data model

One schema, used by parallel prod/dev tables in the same Supabase project. Which set the bot uses is controlled by the `READINGS_TABLE` environment variable: `users_repo.py` and `dedup_repo.py` derive their own table name from whether it ends in `_dev`.

| Prod table | Dev table | Purpose |
|---|---|---|
| `bp_readings` | `bp_readings_dev` | blood pressure readings |
| `users` | `users_dev` | who's allowed to use the bot |
| `processed_updates` | `processed_updates_dev` | Telegram `update_id`s already handled, to block duplicates |

### `bp_readings`

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

Value ranges are enforced both in the bot and by database CHECK constraints. There is an index on `(user_id, created_at desc)`, which also serves `/month`'s date-range query.

### `users`

| Column | Type | Notes |
|---|---|---|
| id | uuid | primary key, generated |
| telegram_id | bigint | unique |
| display_name | text | Telegram first name, best-effort |
| joined_at | timestamptz | |
| is_active | boolean | lets a member be disabled without deleting their data |

### `processed_updates`

| Column | Type | Notes |
|---|---|---|
| update_id | bigint | primary key — the natural uniqueness check |
| processed_at | timestamptz | |

Grows by one row per message with nothing pruning it automatically; for family-scale use this is negligible, but an occasional manual cleanup (delete rows older than N days) is harmless if it's ever wanted.

Row Level Security is enabled with no policies on every table, so only the service-role key (used by the bot) can access the data.

## Deployment

Production runs on a **Render free web service** using **Telegram webhooks**. Locally the bot uses long polling. The mode is controlled by `WEBHOOK_BASE_URL` in `config.py`: when it's set, the bot starts a webhook server (`app.run_webhook`); when it's empty, it polls (`app.run_polling`). This is set explicitly in Render's environment variables rather than relying on Render's auto-injected `RENDER_EXTERNAL_URL`, since that turned out not to be picked up reliably.

Free Render web services spin down after 15 minutes without inbound traffic. The next incoming webhook request wakes the service, which takes roughly 30-60 seconds, so the first reply after a quiet period is delayed but not lost, since Telegram retries failed deliveries. A retry landing mid-spin-up is caught by the duplicate-update guard (`processed_updates`), so it no longer causes a double-logged reading.

### Family access

The bot isn't public. New users send `/join <code>` with a shared join code (`FAMILY_JOIN_CODE`) to be added to the `users` table. Every command except `/start`, `/help`, and `/join` is blocked for anyone not in that table (`handlers/membership.py`). There's no per-user approval step — anyone with the code can join — so treat the code like a shared password and change it (update the env var on Render) if it's ever shared outside the family.

### Daily reminder

A `JobQueue` job (`services/reminders.py`) runs once a day at **06:00 Asia/Kuala_Lumpur**, scheduled in `main.py`. For each active user it checks whether they've logged any reading since local midnight, and only messages the ones who haven't. All users currently share the one hardcoded timezone (`LOCAL_TZ` in `config.py`); there's no per-user timezone setting, which is fine as long as everyone using the bot is in the same timezone.

### Dev/prod separation

Local dev and Render production are kept fully separate, using one Supabase project:

| | Bot token | `READINGS_TABLE` | Mode |
|---|---|---|---|
| **Local dev** | dev bot | `bp_readings_dev` | long polling |
| **Render prod** | prod bot | `bp_readings` | webhook |

This means running the bot locally for testing never touches production data, the production bot's webhook, or real family members' reminders.

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
| `FAMILY_JOIN_CODE` | the code shared with family |
| `WEBHOOK_BASE_URL` | the service's own Render URL, e.g. `https://bp-tracker-bot-xxxx.onrender.com` (no trailing slash) |
| `WEBHOOK_SECRET` | a generated secret (below); Telegram must send this in its webhook requests or they're rejected |

Generate the secret with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Merging a code change into `main` triggers an automatic redeploy. Changing an environment variable in the Render dashboard also redeploys on its own; no push needed for that. **Add any new required env var in Render before merging the code that requires it**, or the deploy will crash at startup with a "Missing environment variable" error.

### Dependency note

Webhook mode requires the `webhooks` extra, and the daily reminder requires `job-queue`: `uv add "python-telegram-bot[webhooks,job-queue]"`. Make sure `uv.lock` is committed after adding extras, since Render's build (`uv sync --frozen`) installs strictly from the lockfile and silently won't include them otherwise.

### Verifying the webhook

```bash
curl "https://api.telegram.org/bot<PROD_TOKEN>/getWebhookInfo"
```

`url` should show your Render URL, and `last_error_message` should be empty.

### Optional: keep the service awake

Point a free uptime monitor (for example UptimeRobot, 5-minute interval) at the Render URL. This removes the cold-start delay but uses most of the 750 free monthly instance hours, and it is not an officially supported way to keep a free service running.

## Security notes

- `.env` is git-ignored. Never commit tokens, the service-role key, or the family join code.
- The service-role key bypasses Row Level Security. Treat it like a root password.
- All database queries are filtered by `user_id`.
- Every command except `/start`, `/help`, and `/join` requires prior membership (`users` table), checked before duplicate tracking or the command handler runs. Public commands and failed joins do not create database rows.
- `FAMILY_JOIN_CODE` has no rate limiting or lockout on wrong guesses. Fine for a small shared code among family; rotate it if it ever leaks further.
- In webhook mode, requests without the correct `WEBHOOK_SECRET` header are rejected.
- Repeated Telegram updates (`update_id`) are recorded and ignored on the second attempt, so webhook retries can't double-submit a reading.
- Dev and prod share one Supabase service-role key but write to different tables (`READINGS_TABLE` and its dev-suffix siblings), so a misconfigured table name is the main risk to watch for after any config change.
- HTTP request logging is set to WARNING so the bot token never appears in logs.
- If a token, key, or join code leaks: revoke/rotate it (BotFather `/revoke` for the token, rotate the Supabase key, change `FAMILY_JOIN_CODE` on Render) and redeploy. Deleting the commit is not enough.

## Roadmap

- [x] MVP: `/log`, `/recent`, `/del_recent`, `/help`
- [x] Deployed to Render with webhooks, dev/prod separation (separate bot tokens and tables)
- [x] Duplicate-reading guard (webhook retries can occasionally double-submit)
- [x] `/recent20`
- [x] Simplified `/recent` output format
- [x] `/month [1-12]` with monthly average
- [x] Family join code and membership guard
- [x] Daily 6am reminder if no reading logged yet
- [ ] Confirmation step on `/del_recent`
- [ ] Notify the owner when someone new joins
- [ ] Per-user timezone (only needed if family spreads across timezones)
- [ ] CSV export and charts

## License

Personal/family project. Add a license if you decide to share it more widely.
