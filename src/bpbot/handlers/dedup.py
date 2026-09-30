import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from bpbot.db import dedup_repo

log = logging.getLogger(__name__)


async def guard_duplicate_updates(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Runs before every other handler. Stops processing if this update_id
    has already been handled (e.g. a Telegram retry after a slow webhook)."""
    is_new = await asyncio.to_thread(dedup_repo.mark_processed_if_new, update.update_id)
    if not is_new:
        log.info("Ignoring duplicate update_id=%s", update.update_id)
        raise ApplicationHandlerStop
