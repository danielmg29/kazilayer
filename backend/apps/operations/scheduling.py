from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def add_business_minutes(start: datetime, minutes: int, calendar: dict) -> datetime:
    """Deterministically advance through a versioned business calendar."""
    zone = ZoneInfo(calendar.get("timezone", "UTC"))
    cursor = start.astimezone(zone).replace(second=0, microsecond=0)
    workdays = set(calendar.get("workdays", [0, 1, 2, 3, 4]))
    start_hour, start_minute = map(int, calendar.get("start", "08:00").split(":"))
    end_hour, end_minute = map(int, calendar.get("end", "17:00").split(":"))
    holidays = set(calendar.get("holidays", []))
    opening, closing = time(start_hour, start_minute), time(end_hour, end_minute)
    remaining = minutes
    while remaining > 0:
        if cursor.weekday() not in workdays or cursor.date().isoformat() in holidays:
            cursor = (cursor + timedelta(days=1)).replace(
                hour=start_hour, minute=start_minute
            )
            continue
        if cursor.time() < opening:
            cursor = cursor.replace(hour=start_hour, minute=start_minute)
        if cursor.time() >= closing:
            cursor = (cursor + timedelta(days=1)).replace(
                hour=start_hour, minute=start_minute
            )
            continue
        available = int(
            (datetime.combine(cursor.date(), closing, zone) - cursor).total_seconds()
            // 60
        )
        consumed = min(remaining, available)
        cursor += timedelta(minutes=consumed)
        remaining -= consumed
    return cursor.astimezone(ZoneInfo("UTC"))
