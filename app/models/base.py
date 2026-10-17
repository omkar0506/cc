from datetime import datetime, timezone


def utc_now():
    """Return current UTC datetime as a naive datetime object for MySQL DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
