"""
Datetime helper utilities.

Thin wrappers for common datetime operations used across the app.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def is_within_range(
    target: datetime,
    start: datetime,
    end: datetime,
) -> bool:
    """Check whether *target* falls within [start, end).

    Args:
        target: The datetime to test.
        start: Inclusive lower bound.
        end: Exclusive upper bound.
    """
    return start <= target < end
