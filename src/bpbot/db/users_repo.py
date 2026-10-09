from bpbot.config import get_settings
from bpbot.db.client import get_client


def _table() -> str:
    readings_table = get_settings().readings_table
    return "users_dev" if readings_table.endswith("_dev") else "users"


def is_member(telegram_id: int) -> bool:
    result = (
        get_client()
        .table(_table())
        .select("telegram_id")
        .eq("telegram_id", telegram_id)
        .eq("is_active", True)
        .execute()
    )
    return len(result.data) > 0


def add_member(telegram_id: int, display_name: str | None) -> None:
    get_client().table(_table()).upsert(
        {"telegram_id": telegram_id, "display_name": display_name, "is_active": True},
        on_conflict="telegram_id",
    ).execute()


def get_active_user_ids() -> list[int]:
    result = (
        get_client()
        .table(_table())
        .select("telegram_id")
        .eq("is_active", True)
        .execute()
    )
    return [row["telegram_id"] for row in result.data]
