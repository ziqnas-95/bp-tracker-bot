from bpbot.config import get_settings
from bpbot.db.client import get_client


def _table() -> str:
    readings_table = get_settings().readings_table
    return (
        "processed_updates_dev"
        if readings_table.endswith("_dev")
        else "processed_updates"
    )


def mark_processed_if_new(update_id: int) -> bool:
    """Records this update_id. Returns True the first time it's seen,
    False if it's a duplicate (already recorded)."""
    try:
        get_client().table(_table()).insert({"update_id": update_id}).execute()
        return True
    except Exception as e:
        if "duplicate key" in str(e).lower() or "23505" in str(e):
            return False
        raise
