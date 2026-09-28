from datetime import UTC, datetime

import pytest

from bpbot.services.time_of_day import get_time_of_day


def utc(hour, minute=0):
    return datetime(2026, 9, 28, hour, minute, tzinfo=UTC)


def test_just_before_noon_local_is_morning():
    assert get_time_of_day(utc(3, 59)) == "morning"  # 11:59 in KL


def test_noon_local_is_evening():
    assert get_time_of_day(utc(4, 0)) == "evening"  # 12:00 in KL


def test_midnight_local_counts_as_morning():
    assert get_time_of_day(utc(16, 0)) == "morning"  # 00:00 in KL


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        # We add both DTZ001 and UP017 to the ignore tag, separated by a comma
        get_time_of_day(datetime(2026, 9, 28, 8, 0)) # noqa: DTZ001
