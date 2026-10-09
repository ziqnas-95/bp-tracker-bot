import calendar
from datetime import datetime

from bpbot.config import LOCAL_TZ

CATEGORY_LABELS = {
    "green": ("🟢", "Normal"),
    "yellow": ("🟡", "Elevated"),
    "orange": ("🟠", "High - Stage 1 range"),
    "red": ("🔴", "High - Stage 2 range"),
}

TIME_LABELS = {"morning": "Morning", "evening": "Evening"}

HELP_TEXT = (
    "BP Tracker\n\n"
    "/join CODE - Join the bot\n"
    "/log 120/80 72 - Save a reading\n"
    "/recent - Show the last 5 readings\n"
    "/recent20 - Show the last 20 readings\n"
    "/month [1-12] - Show this month's summary\n"
    "/del_recent - Delete the latest reading\n\n"
    "Readings are for tracking and are not medical advice."
)

URGENT_NOTE = (
    "Very high reading. Rest and measure again. Seek urgent medical care if it "
    "stays this high or you have symptoms."
)


def local_time_str(iso_timestamp: str) -> str:
    dt = datetime.fromisoformat(iso_timestamp).astimezone(LOCAL_TZ)
    return f"{dt.day}/{dt.month} {dt.strftime('%H:%M')}"


def format_saved(row: dict, urgent: bool) -> str:
    category = CATEGORY_LABELS[row["category"]][1]
    time_of_day = TIME_LABELS[row["time_of_day"]]
    message = (
        f"Saved: {row['systolic']}/{row['diastolic']}, pulse {row['pulse']}\n"
        f"{category} - {time_of_day}, {local_time_str(row['created_at'])}"
    )
    if urgent:
        message += f"\n\n{URGENT_NOTE}"
    return message


def format_line(row: dict) -> str:
    return (
        f"{row['systolic']}/{row['diastolic']}, pulse {row['pulse']} - "
        f"{local_time_str(row['created_at'])}"
    )


def format_recent(rows: list[dict]) -> str:
    if not rows:
        return "No readings yet. Try /log 120/80 60."
    return "Recent readings:\n" + "\n".join(format_line(row) for row in rows)


def format_deleted(row: dict) -> str:
    return f"Deleted: {format_line(row)}"


def format_month(all_rows: list[dict], avg, year: int, month: int) -> str:
    month_name = calendar.month_name[month]
    if avg is None:
        return f"{month_name} {year}: no readings."

    count = f"{avg.count} reading" if avg.count == 1 else f"{avg.count} readings"
    lines = [
        f"{month_name} {year} - {count}",
        f"Average: {avg.avg_systolic:.0f}/{avg.avg_diastolic:.0f}",
        f"pulse {avg.avg_pulse:.0f}",
    ]
    shown = all_rows[:20]
    lines.extend(format_line(row) for row in shown)
    if avg.count > len(shown):
        lines.append(f"Showing {len(shown)} of {avg.count} readings.")
    return "\n".join(lines)
