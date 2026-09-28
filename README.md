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
- **python-telegram-bot** for the Telegram interface (long polling)
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
│       └── readings_repo.py       # insert, get recent, delete latest
└── tests/                         # unit tests for the pure logic
```

The layers depend inward: handlers know Telegram, the repository knows Supabase, and services know neither. This keeps the logic easy to test.

## Setup (local)

### Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
- A [Supabase](https://supabase.com) project

### Steps

```bash
git clone <your-repo-url>
cd bp-tracker-bot
uv sync
cp .env.example .env      # then fill in the values
```

1. In Supabase, open **SQL Editor** and run the contents of `schema.sql`.
2. Fill in `.env`:

| Variable | Where to find it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | @userinfobot |
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → `service_role` key |

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

A single table, `bp_readings`:

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

Value ranges are enforced both in the bot and by database CHECK constraints. Row Level Security is enabled with no policies, so only the service-role key (used by the bot) can access the data. There is an index on `(user_id, created_at desc)`.

## Deployment

The bot is a long-running process that uses long polling, so it needs an always-on machine that makes outbound connections only (no open ports).

Current setup: an Oracle Cloud Always Free Ubuntu VM running the bot as a `systemd` service.

Server setup, in short:

1. Clone the repo using a read-only GitHub deploy key.
2. `uv sync --no-dev`
3. Create `.env` on the server with `chmod 600`.
4. Install a `systemd` unit that runs `uv run --no-dev python -m bpbot.main` with `Restart=always`.

To update after merging changes:

```bash
cd ~/bp-tracker-bot && git pull && uv sync --no-dev && sudo systemctl restart bpbot
```

View logs with `journalctl -u bpbot -f`.

Only one instance of the bot may run per token. Stop local copies before starting the server, or use a separate dev bot token.

## Security notes

- `.env` is git-ignored. Never commit tokens or the service-role key.
- The service-role key bypasses Row Level Security. Treat it like a root password.
- All database queries are filtered by `user_id`.
- The bot silently ignores every Telegram user except the one in `TELEGRAM_ALLOWED_USER_ID`.
- HTTP request logging is set to WARNING so the bot token never appears in logs.
- If a token leaks: revoke it with BotFather (`/revoke`) and rotate the Supabase key. Deleting the commit is not enough.

## Roadmap

- [x] MVP: `/log`, `/recent`, `/del_recent`, `/help`
- [ ] Confirmation button on `/del_recent`
- [ ] Backdated readings (log a reading taken earlier)
- [ ] Analytics: daily/weekly averages, morning vs evening comparison
- [ ] Reminders
- [ ] CSV export and charts

## License

Personal project. Add a license if you decide to share it.