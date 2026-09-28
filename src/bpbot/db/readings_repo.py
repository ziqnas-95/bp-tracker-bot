from bpbot.db.client import get_client

TABLE = "bp_readings"


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
        .table(TABLE)
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
        .table(TABLE)
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
        .table(TABLE)
        .delete()
        .eq("id", row["id"])
        .eq("user_id", user_id)  # always scoped, even though the id is unique
        .execute()
    )
    return row
