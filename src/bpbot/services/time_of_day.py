from datetime import UTC, datetime
from typing import Literal

from bpbot.config import LOCAL_TZ

TimeOfDay = Literal["morning", "evening"]


def get_time_of_day(timestamp: datetime) -> TimeOfDay:
    """Before 12:00 local time is morning, 12:00 onward is evening.
    `timestamp` must be timezone-aware (e.g. datetime.now(timezone.utc))."""
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return "morning" if timestamp.astimezone(LOCAL_TZ).hour < 12 else "evening"


def month_range_utc(year: int, month: int) -> tuple[datetime, datetime]:
    """UTC [start, end) boundaries for a calendar month in local time."""
    start_local = datetime(year, month, 1, tzinfo=LOCAL_TZ)
    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=LOCAL_TZ)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=LOCAL_TZ)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def start_of_today_utc() -> datetime:
    now_local = datetime.now(LOCAL_TZ)
    midnight_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight_local.astimezone(UTC)
