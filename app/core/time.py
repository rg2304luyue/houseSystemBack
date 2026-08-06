"""Time helpers for the project's timezone-naive MySQL DATETIME columns."""

from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    """Return current UTC without tzinfo, preserving existing DATETIME semantics."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
