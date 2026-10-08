import logging
from datetime import time as dt_time

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, TypeHandler

from bpbot.config import LOCAL_TZ, get_settings
from bpbot.handlers import commands, dedup, membership
from bpbot.services.reminders import send_morning_reminders

log = logging.getLogger(__name__)


async def _on_error(update, context) -> None:
    log.error("Unhandled error", exc_info=context.error)


async def _post_init(app: Application) -> None:
    """Registers the command menu shown when you type '/' in Telegram."""
    await app.bot.set_my_commands(
        [
            BotCommand("log", "Save a reading, e.g. /log 120/80 72"),
            BotCommand("recent", "Show your last 5 readings"),
            BotCommand("recent20", "Show your last 20 readings"),
            BotCommand("del_recent", "Delete your most recent reading"),
            BotCommand(
                "month", "Monthly summary, e.g. /month 9 (defaults to current month)"
            ),
            BotCommand("help", "How to use this bot"),
            BotCommand("join", "Join with your family code"),
        ]
    )


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    # httpx logs full request URLs at INFO, and Telegram URLs contain the bot token
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = get_settings()  # fails fast if .env is incomplete

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .build()
    )

    # group=-1 runs before the default group (0), so this checks every
    # update for duplicates before any command handler sees it
    app.add_handler(TypeHandler(Update, dedup.guard_duplicate_updates), group=-1)
    app.add_handler(TypeHandler(Update, membership.guard_membership), group=-1)

    app.add_handler(
        CommandHandler(
            ["start", "help"],
            commands.help_cmd,
        )
    )
    app.add_handler(
        CommandHandler(
            "log",
            commands.log_cmd,
        )
    )
    app.add_handler(
        CommandHandler(
            "recent",
            commands.recent_cmd,
        )
    )
    app.add_handler(
        CommandHandler(
            "recent20",
            commands.recent20_cmd,
        )
    )
    app.add_handler(
        CommandHandler(
            "month",
            commands.month_cmd,
        )
    )
    app.add_handler(
        CommandHandler(
            "del_recent",
            commands.del_recent_cmd,
        )
    )
    app.add_error_handler(_on_error)

    app.job_queue.run_daily(
        send_morning_reminders,
        time=dt_time(hour=6, minute=0, tzinfo=LOCAL_TZ),
        name="morning_reminder",
    )

    if settings.webhook_base_url:
        log.info("Bot starting (webhook mode)")
        app.run_webhook(
            listen="0.0.0.0",
            port=settings.port,
            url_path="webhook",
            webhook_url=f"{settings.webhook_base_url}/webhook",
            secret_token=settings.webhook_secret,
        )
    else:
        log.info("Bot starting (long polling)")
        app.run_polling()


if __name__ == "__main__":
    main()
