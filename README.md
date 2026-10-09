# BP Tracker Bot

A private Telegram bot for recording blood pressure readings and reviewing your history.

## Commands

| Command | Description |
|---|---|
| `/join <code>` | Join with the family code (send in a private chat) |
| `/log 120/80 72` | Save blood pressure and pulse |
| `/recent` | Show your latest 5 readings |
| `/recent20` | Show your latest 20 readings |
| `/month` | Show this month's summary |
| `/month 9` | Show a month's summary (1-12) |
| `/del_recent` | Delete your latest reading |
| `/help` or `/start` | Show commands |

Users must join before using the tracking commands. If you have not joined, the bot explains how. A failed join does not add a database row.

## Reading details

The bot classifies readings as Normal, Elevated, High (stage 1), or High (stage 2). It tags readings as morning or evening in Kuala Lumpur time and warns about very high values. This is a tracking tool, not medical advice.

## Setup

1. Install [uv](https://docs.astral.sh/uv/) and run `uv sync`.
2. Create a Supabase project and run [`schema.sql`](schema.sql) in its SQL editor.
3. Copy `.env.example` to `.env` and fill in the Telegram token, Supabase URL and service key, readings table, allowed user ID, and family join code.
4. Start the bot:

   ```sh
   uv run python -m bpbot.main
   ```

Set `READINGS_TABLE=bp_readings_dev` for local development or `bp_readings` for production. The matching users and duplicate-tracking tables are selected automatically. Leave `WEBHOOK_BASE_URL` empty to use long polling; set it and `WEBHOOK_SECRET` for webhook mode.

## Data and access

Supabase stores readings, joined users, and processed Telegram update IDs. Readings are scoped by Telegram user ID. The bot uses the Supabase service-role key, so keep it and the family code private. In production, use a long random join code.
