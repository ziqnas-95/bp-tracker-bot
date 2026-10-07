import asyncio

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from bpbot.db import users_repo

# These must work before someone has joined
EXEMPT_COMMANDS = {"/start", "/help", "/join"}


async def guard_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or msg.text is None:
        return

    command = msg.text.split()[0].split("@")[0]  # strips args and @botname
    if command in EXEMPT_COMMANDS:
        return

    user_id = update.effective_user.id
    is_member = await asyncio.to_thread(users_repo.is_member, user_id)
    if not is_member:
        await msg.reply_text(
            "You need to join first. Ask whoever shared this bot with you for "
            "the join code, then send: /join <code>"
        )
        raise ApplicationHandlerStop
