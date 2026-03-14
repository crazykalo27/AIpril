"""
Reclaim tag detection service.

Inspects calendar events to determine whether they carry the
special "reclaim" marker that suppresses user prompts.
"""

from src.config.logging_config import get_logger
from src.domain.models.calendar_event import CalendarEvent

logger = get_logger(__name__)


class ReclaimDetector:
    """Detects whether a calendar event is tagged as reclaim."""

    def __init__(self, reclaim_tag: str = "[reclaim]") -> None:
        self._tag = reclaim_tag.lower()

    def is_reclaim(self, event: CalendarEvent) -> bool:
        """Return True if the event contains the reclaim marker.

        Checks summary and description fields (case-insensitive).
        """
        text = f"{event.summary} {event.description}".lower()
        found = self._tag in text
        if found:
            logger.debug("Reclaim tag found in event %s", event.event_id)
        return found

    def tag_events(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Set ``is_reclaim`` on each event in-place and return the list."""
        for event in events:
            event.is_reclaim = self.is_reclaim(event)
        return events
