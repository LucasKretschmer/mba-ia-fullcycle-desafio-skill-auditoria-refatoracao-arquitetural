from datetime import datetime, timezone


def utcnow():
    # naive UTC keeps comparisons compatible with the DateTime columns already stored in SQLite
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
