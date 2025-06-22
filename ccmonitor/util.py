from datetime import datetime


def format_time_duration(total_seconds: float) -> str:
    """Format time duration in hh:mm:ss format.

    Args:
        total_seconds: Total time in seconds

    Returns:
        Formatted time string (e.g., "1:23:45", "0:23:45", "0:00:12")
    """
    total_seconds = int(total_seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def parse_datetime(dt_str: str | None) -> datetime:
    """Parse datetime string safely.

    Args:
        dt_str: ISO format datetime string

    Returns:
        Parsed datetime object, or current time if parsing fails.
    """
    if not dt_str:
        return datetime.now()

    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now()
