import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from bpbot.db import dedup_repo
from bpbot.handlers.membership import EXEMPT_COMMANDS

log = logging.getLogger(__name__)


async def guard_duplicate_updates(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Record only authorized updates; public commands never write to the DB."""
    msg = update.effective_message
    if msg is None or not msg.text or not msg.text.strip():
        return
    if msg.text.split()[0].split("@")[0] in EXEMPT_COMMANDS:
        return

    is_new = await asyncio.to_thread(dedup_repo.mark_processed_if_new, update.update_id)
    if not is_new:
        log.info("Ignoring duplicate update_id=%s", update.update_id)
        raise ApplicationHandlerStop
