"""
Repeat-last-activity service.

Caches the most recent interpreted activity so the user can
re-log it with a single button press.
"""

from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.interpreted_activity import InterpretedActivity

logger = get_logger(__name__)


class RepeatActivityService:
    """Tracks and re-emits the last recorded activity."""

    def __init__(self) -> None:
        self._last_activity: Optional[InterpretedActivity] = None

    def set_last(self, activity: InterpretedActivity) -> None:
        """Store the most recently interpreted activity."""
        self._last_activity = activity
        logger.debug("Last activity cached: %s", activity.summary)

    def get_last(self) -> Optional[InterpretedActivity]:
        """Return the last activity, or None if nothing recorded yet."""
        return self._last_activity

    def has_last(self) -> bool:
        """Check whether a previous activity is available."""
        return self._last_activity is not None
