"""
Use case: determine whether the system should prompt the user now.

Checks current calendar events and reclaim status to produce
a PromptState decision.
"""

from datetime import datetime, timedelta, timezone

from src.config.logging_config import get_logger
from src.domain.enums.prompt_state import PromptState
from src.infrastructure.google.google_calendar_client import GoogleCalendarClient
from src.services.calendar.reclaim_detector import ReclaimDetector

logger = get_logger(__name__)


class DeterminePromptState:
    """Evaluates calendar context and returns a prompt decision."""

    def __init__(
        self,
        calendar_client: GoogleCalendarClient,
        reclaim_detector: ReclaimDetector,
    ) -> None:
        self._calendar = calendar_client
        self._reclaim = reclaim_detector

    def execute(self) -> PromptState:
        """Run the decision logic.

        # TODO: Add more rules (sleep hours, focus mode, meeting types).
        """
        now = datetime.now(timezone.utc)
        events = self._calendar.list_events(
            time_min=now,
            time_max=now + timedelta(minutes=1),
        )

        if not events:
            return PromptState.SHOULD_PROMPT

        self._reclaim.tag_events(events)

        for event in events:
            if event.is_reclaim:
                logger.debug("Suppressed by reclaim event: %s", event.summary)
                return PromptState.SUPPRESSED_RECLAIM

        return PromptState.SUPPRESSED_EVENT
