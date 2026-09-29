import logging

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, filters

from bpbot.config import get_settings
from bpbot.handlers import commands

log = logging.getLogger(__name__)


async def _on_error(update, context) -> None:
    log.error("Unhandled error", exc_info=context.error)


async def _post_init(app: Application) -> None:
    """Registers the command menu shown when you type '/' in Telegram."""
    await app.bot.set_my_commands(
        [
            BotCommand("log", "Save a reading, e.g. /log 120/80 72"),
            BotCommand("recent", "Show your last 5 readings"),
            BotCommand("del_recent", "Delete your most recent reading"),
            BotCommand("help", "How to use this bot"),
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

    # Only you: messages from anyone else match no handler and are ignored
    only_me = filters.User(user_id=settings.allowed_user_id)

    app.add_handler(
        CommandHandler(["start", "help"], commands.help_cmd, filters=only_me)
    )
    app.add_handler(CommandHandler("log", commands.log_cmd, filters=only_me))
    app.add_handler(CommandHandler("recent", commands.recent_cmd, filters=only_me))
    app.add_handler(
        CommandHandler("del_recent", commands.del_recent_cmd, filters=only_me)
    )
    app.add_error_handler(_on_error)

    log.info("Bot starting (long polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
