import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from bpbot.db import users_repo

# These must work before someone has joined
EXEMPT_COMMANDS = {"/start", "/help", "/join"}
JOIN_PROMPT = (
    "You need to join first. Ask whoever shared this bot with you for "
    "the join code, then send: /join <code> in a private chat with this bot."
)
log = logging.getLogger(__name__)


async def guard_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.text or not msg.text.strip():
        return

    command = msg.text.split()[0].split("@")[0]  # strips args and @botname
    if command in EXEMPT_COMMANDS:
        return

    user = update.effective_user
    if user is None:
        raise ApplicationHandlerStop
    try:
        is_member = await asyncio.to_thread(users_repo.is_member, user.id)
    except Exception:
        log.exception("Failed to check membership")
        await msg.reply_text("Membership check is unavailable. Please try again later.")
        raise ApplicationHandlerStop
    if not is_member:
        await msg.reply_text(JOIN_PROMPT)
        raise ApplicationHandlerStop
