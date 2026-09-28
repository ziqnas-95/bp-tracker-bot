from datetime import datetime
from typing import Literal

from bpbot.config import LOCAL_TZ

TimeOfDay = Literal["morning", "evening"]


def get_time_of_day(timestamp: datetime) -> TimeOfDay:
    """Before 12:00 local time is morning, 12:00 onward is evening.
    `timestamp` must be timezone-aware (e.g. datetime.now(timezone.utc))."""
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return "morning" if timestamp.astimezone(LOCAL_TZ).hour < 12 else "evening"
