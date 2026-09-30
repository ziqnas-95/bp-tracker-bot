import asyncio
import logging
from datetime import UTC, datetime

from telegram import Update
from telegram.ext import ContextTypes

from bpbot.db import readings_repo as repo
from bpbot.handlers import formatting as fmt
from bpbot.services.classification import classify, is_urgent
from bpbot.services.parsing import ParseError, parse_log_args
from bpbot.services.time_of_day import get_time_of_day

log = logging.getLogger(__name__)

DB_ERROR = "Something went wrong talking to the database. Please try again."


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_html(fmt.HELP_TEXT)


async def log_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    user_id = update.effective_user.id

    try:
        parsed = parse_log_args(" ".join(context.args))
    except ParseError as e:
        await msg.reply_text(str(e))
        return

    category = classify(parsed.systolic, parsed.diastolic)
    time_of_day = get_time_of_day(datetime.now(UTC))

    try:
        saved = await asyncio.to_thread(
            repo.insert_reading,
            user_id,
            parsed.systolic,
            parsed.diastolic,
            parsed.pulse,
            category,
            time_of_day,
        )
    except Exception:
        log.exception("Failed to insert reading")
        await msg.reply_text(DB_ERROR)
        return

    urgent = is_urgent(parsed.systolic, parsed.diastolic)
    await msg.reply_html(fmt.format_saved(saved, urgent))


async def recent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    try:
        rows = await asyncio.to_thread(repo.get_recent, update.effective_user.id, 5)
    except Exception:
        log.exception("Failed to fetch recent readings")
        await msg.reply_text(DB_ERROR)
        return
    await msg.reply_html(fmt.format_recent(rows))


async def recent20_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    try:
        rows = await asyncio.to_thread(repo.get_recent, update.effective_user.id, 20)
    except Exception:
        log.exception("Failed to fetch recent readings")
        await msg.reply_text(DB_ERROR)
        return
    await msg.reply_html(fmt.format_recent(rows))


async def del_recent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    try:
        deleted = await asyncio.to_thread(repo.delete_latest, update.effective_user.id)
    except Exception:
        log.exception("Failed to delete latest reading")
        await msg.reply_text(DB_ERROR)
        return

    if deleted is None:
        await msg.reply_text("Nothing to delete. You have no readings yet.")
    else:
        await msg.reply_html(fmt.format_deleted(deleted))
