from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyAverage:
    count: int
    avg_systolic: float
    avg_diastolic: float
    avg_pulse: float


def compute_monthly_average(rows: list[dict]) -> MonthlyAverage | None:
    """None if there are no readings that month."""
    if not rows:
        return None
    n = len(rows)
    return MonthlyAverage(
        count=n,
        avg_systolic=sum(r["systolic"] for r in rows) / n,
        avg_diastolic=sum(r["diastolic"] for r in rows) / n,
        avg_pulse=sum(r["pulse"] for r in rows) / n,
    )
