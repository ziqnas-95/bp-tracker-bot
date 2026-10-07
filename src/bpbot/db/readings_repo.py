from datetime import datetime

from bpbot.config import get_settings
from bpbot.db.client import get_client


def insert_reading(
    user_id: int,
    systolic: int,
    diastolic: int,
    pulse: int,
    category: str,
    time_of_day: str,
) -> dict:
    """Insert one reading and return the saved row (includes id and created_at)."""
    result = (
        get_client()
        .table(_table())
        .insert(
            {
                "user_id": user_id,
                "systolic": systolic,
                "diastolic": diastolic,
                "pulse": pulse,
                "category": category,
                "time_of_day": time_of_day,
            }
        )
        .execute()
    )
    return result.data[0]


def get_recent(user_id: int, limit: int = 5) -> list[dict]:
    """Newest first."""
    result = (
        get_client()
        .table(_table())
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def delete_latest(user_id: int) -> dict | None:
    """Delete the user's most recent reading. Returns the deleted row, or None if there was none."""
    latest = get_recent(user_id, limit=1)
    if not latest:
        return None
    row = latest[0]
    (
        get_client()
        .table(_table())
        .delete()
        .eq("id", row["id"])
        .eq("user_id", user_id)  # always scoped, even though the id is unique
        .execute()
    )
    return row


def _table() -> str:
    return get_settings().readings_table


def get_month_readings(
    user_id: int, start_utc: datetime, end_utc: datetime
) -> list[dict]:
    """All readings in [start_utc, end_utc), newest first."""
    result = (
        get_client()
        .table(_table())
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", start_utc.isoformat())
        .lt("created_at", end_utc.isoformat())
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def has_reading_since(user_id: int, start_utc: datetime) -> bool:
    result = (
        get_client()
        .table(_table())
        .select("id")
        .eq("user_id", user_id)
        .gte("created_at", start_utc.isoformat())
        .limit(1)
        .execute()
    )
    return len(result.data) > 0
