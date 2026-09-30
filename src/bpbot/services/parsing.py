import re
from dataclasses import dataclass


class ParseError(ValueError):
    """Carries a user-friendly message that the handler can send straight back."""


@dataclass(frozen=True)
class ParsedReading:
    systolic: int
    diastolic: int
    pulse: int


USAGE = "Use the format: /log 120/80 72  (systolic/diastolic pulse)"

# Mirrors the database CHECK constraints
SYSTOLIC_RANGE = (50, 300)
DIASTOLIC_RANGE = (30, 200)
PULSE_RANGE = (20, 250)

_PATTERN = re.compile(r"^\s*(\d{1,3})\s*/\s*(\d{1,3})\s+(\d{1,3})\s*$")


def _check_range(name: str, value: int, low_high: tuple[int, int]) -> None:
    low, high = low_high
    if not low <= value <= high:
        raise ParseError(f"{name} {value} looks wrong (expected {low}-{high}). {USAGE}")


def parse_log_args(text: str) -> ParsedReading:
    """Parse the text after /log, e.g. '120/80 99'."""
    match = _PATTERN.match(text or "")
    if not match:
        raise ParseError(f"I couldn't read that. {USAGE}")

    systolic, diastolic, pulse = (int(g) for g in match.groups())

    _check_range("Systolic", systolic, SYSTOLIC_RANGE)
    _check_range("Diastolic", diastolic, DIASTOLIC_RANGE)
    _check_range("Pulse", pulse, PULSE_RANGE)

    if systolic <= diastolic:
        raise ParseError(f"Systolic must be higher than diastolic. {USAGE}")

    return ParsedReading(systolic, diastolic, pulse)


def parse_month_arg(args: list[str], current_month: int) -> int:
    """No argument -> current month. Otherwise expects a single int 1-12."""
    if not args:
        return current_month
    if len(args) > 1:
        raise ParseError("Use /month or /month <1-12>, e.g. /month 9")
    try:
        month = int(args[0])
    except ValueError:
        raise ParseError("Month must be a number from 1 to 12.")
    if not 1 <= month <= 12:
        raise ParseError("Month must be between 1 and 12.")
    return month
