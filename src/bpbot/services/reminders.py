import logging

from telegram.ext import ContextTypes

from bpbot.db import readings_repo, users_repo
from bpbot.services.time_of_day import start_of_today_utc

log = logging.getLogger(__name__)

REMINDER_TEXT = (
    "⏰ No blood pressure reading logged yet today. Send /log when you get a chance."
)


async def send_morning_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    start = start_of_today_utc()
    user_ids = users_repo.get_active_user_ids()

    for telegram_id in user_ids:
        if readings_repo.has_reading_since(telegram_id, start):
            continue
        try:
            await context.bot.send_message(chat_id=telegram_id, text=REMINDER_TEXT)
        except Exception:
            log.exception("Failed to send reminder to %s", telegram_id)
