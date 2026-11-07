from datetime import datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def normalize_datetime(value):
    """Normalize datetimes to naive Asia/Kolkata wall time for SQLite storage.

    Naive values (including HTML date/time fields) are interpreted as India local
    time. Offset-aware CSV/API values are converted to India local time first.
    """
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.strip())
        except (ValueError, AttributeError):
            raise ValueError("Invalid transaction date.")
    if not isinstance(value, datetime):
        raise ValueError("Transaction date must be a datetime.")
    if value.tzinfo is not None:
        value = value.astimezone(APP_TIMEZONE).replace(tzinfo=None)
    return value


def month_bounds(year, month):
    if isinstance(year, bool) or not isinstance(year, int) or year < 1 or year > 9998:
        raise ValueError("Invalid year.")
    if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")
    start = datetime(year, month, 1)
    end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1)
    return start, end
