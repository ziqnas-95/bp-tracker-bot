import calendar
from datetime import datetime

from bpbot.config import LOCAL_TZ

CATEGORY_LABELS = {
    "green": ("🟢", "Normal"),
    "yellow": ("🟡", "Elevated"),
    "orange": ("🟠", "High - Stage 1 range"),
    "red": ("🔴", "High - Stage 2 range"),
}

TIME_LABELS = {
    "morning": "🌅 Morning",
    "evening": "🌙 Evening",
}

DISCLAIMER = "<i>This is a tracking tool, not medical advice.</i>"

URGENT_NOTE = (
    "⚠️ <b>This is a very high reading.</b> Rest for a few minutes and measure "
    "again. If it stays this high, or you have chest pain, shortness of breath, "
    "weakness or a severe headache, seek urgent medical care."
)

HELP_TEXT = (
    "<b>BP Tracker</b>\n\n"
    "<b>Commands</b>\n"
    "/join &lt;code&gt; - join with the code shared by your family\n"
    "/log 120/80 72 - save a reading (systolic/diastolic pulse)\n"
    "/recent - show your last 5 readings\n"
    "/del_recent - delete your most recent reading\n"
    "/help - show this message\n\n"
    "<b>Categories</b>\n"
    "🟢 Normal: under 120 and under 80\n"
    "🟡 Elevated: 120-129 and under 80\n"
    "🟠 Stage 1 range: 130-139 or 80-89\n"
    "🔴 Stage 2 range: 140+ or 90+\n"
    "The higher of the two numbers decides the category.\n\n"
    "Morning is before 12:00, evening is 12:00 onward (Kuala Lumpur time).\n\n"
    + DISCLAIMER
)


def local_time_str(iso_timestamp: str) -> str:
    """'2026-09-28T03:14:00+00:00' -> '28/9, 11:14' in local time."""
    dt = datetime.fromisoformat(iso_timestamp).astimezone(LOCAL_TZ)
    return f"{dt.day}/{dt.month}, {dt.strftime('%H:%M')}"


def format_saved(row: dict, urgent: bool) -> str:
    emoji, label = CATEGORY_LABELS[row["category"]]
    parts = [
        "✅ <b>Reading saved</b>",
        f"{emoji} <b>{label}</b>",
        f"BP: {row['systolic']}/{row['diastolic']} mmHg · Pulse: {row['pulse']} bpm",
        f"{TIME_LABELS[row['time_of_day']]} · {local_time_str(row['created_at'])}",
    ]
    if urgent:
        parts += ["", URGENT_NOTE]
    parts += ["", DISCLAIMER]
    return "\n".join(parts)


def format_line(row: dict) -> str:
    emoji, _ = CATEGORY_LABELS[row["category"]]
    return (
        f"{emoji} {row['systolic']}/{row['diastolic']} · {row['pulse']} bpm · "
        f"{local_time_str(row['created_at'])}"
    )


def format_recent(rows: list[dict]) -> str:
    if not rows:
        return "No readings yet. Try: /log 120/80 60"
    return "<b>Recent readings</b> (newest first)\n\n" + "\n".join(
        format_line(r) for r in rows
    )


def format_deleted(row: dict) -> str:
    return "🗑 <b>Deleted</b>\n" + format_line(row)


def format_month(all_rows: list[dict], avg, year: int, month: int) -> str:
    month_name = calendar.month_name[month]

    if avg is None:
        return f"<b>{month_name} {year}</b>\n\nNo readings logged this month."

    header = (
        f"<b>{month_name} {year}</b> · {avg.count} reading{'s' if avg.count != 1 else ''}\n"
        f"Average: {avg.avg_systolic:.0f}/{avg.avg_diastolic:.0f} mmHg · "
        f"{avg.avg_pulse:.0f} bpm"
    )

    shown = all_rows[:20]
    lines = "\n".join(format_line(r) for r in shown)
    footer = (
        f"\n\n<i>Showing latest {len(shown)} of {avg.count}.</i>"
        if avg.count > 20
        else ""
    )

    return f"{header}\n\n{lines}{footer}"
