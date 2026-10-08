import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from telegram.ext import ApplicationHandlerStop

from bpbot.handlers import commands, dedup, membership


def make_update(text, chat_type="private"):
    message = SimpleNamespace(text=text, reply_text=AsyncMock())
    user = SimpleNamespace(id=123, first_name="Tester")
    update = SimpleNamespace(
        effective_message=message,
        effective_user=user,
        effective_chat=SimpleNamespace(type=chat_type),
        update_id=42,
    )
    return update


@pytest.mark.parametrize("text", ["/log 120/80 72", "/recent", "hello"])
def test_unjoined_user_stops_before_dedup_or_command(monkeypatch, text):
    update = make_update(text)
    calls = []
    monkeypatch.setattr(
        membership.users_repo,
        "is_member",
        lambda user_id: calls.append(user_id) or False,
    )
    monkeypatch.setattr(
        dedup.dedup_repo,
        "mark_processed_if_new",
        lambda _: pytest.fail("database write"),
    )

    async def process():
        with pytest.raises(ApplicationHandlerStop):
            await membership.guard_membership(update, None)
        # ApplicationHandlerStop prevents later handler groups from running.

    asyncio.run(process())
    assert calls == [123]
    assert "/join <code>" in update.effective_message.reply_text.call_args.args[0]


@pytest.mark.parametrize("text", ["/start", "/help", "/join wrong"])
def test_public_commands_never_create_dedup_rows(monkeypatch, text):
    update = make_update(text)
    monkeypatch.setattr(
        membership.users_repo, "is_member", lambda _: pytest.fail("membership lookup")
    )
    monkeypatch.setattr(
        dedup.dedup_repo,
        "mark_processed_if_new",
        lambda _: pytest.fail("database write"),
    )
    asyncio.run(membership.guard_membership(update, None))
    asyncio.run(dedup.guard_duplicate_updates(update, None))


@pytest.mark.parametrize(
    "args,chat_type,expected_write",
    [
        ([], "private", False),
        (["wrong"], "private", False),
        (["correct", "extra"], "private", False),
        (["correct"], "group", False),
        (["correct"], "private", True),
    ],
)
def test_join_only_writes_for_valid_private_code(
    monkeypatch, args, chat_type, expected_write
):
    update = make_update("/join", chat_type)
    writes = []
    monkeypatch.setattr(
        commands,
        "get_settings",
        lambda: SimpleNamespace(family_join_code="correct"),
    )
    monkeypatch.setattr(
        commands.users_repo,
        "add_member",
        lambda *values: writes.append(values),
    )
    asyncio.run(commands.join_cmd(update, SimpleNamespace(args=args)))
    assert writes == ([(123, "Tester")] if expected_write else [])


def test_member_command_gets_deduplicated(monkeypatch):
    update = make_update("/log 120/80 72")
    writes = []
    monkeypatch.setattr(membership.users_repo, "is_member", lambda _: True)
    monkeypatch.setattr(
        dedup.dedup_repo,
        "mark_processed_if_new",
        lambda update_id: writes.append(update_id) or True,
    )
    asyncio.run(membership.guard_membership(update, None))
    asyncio.run(dedup.guard_duplicate_updates(update, None))
    assert writes == [42]


def test_blank_message_does_not_write(monkeypatch):
    update = make_update("   ")
    monkeypatch.setattr(
        dedup.dedup_repo,
        "mark_processed_if_new",
        lambda _: pytest.fail("database write"),
    )
    asyncio.run(membership.guard_membership(update, None))
    asyncio.run(dedup.guard_duplicate_updates(update, None))
