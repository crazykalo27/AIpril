"""
Google Calendar API client.

Wraps the Google Calendar REST API behind a clean interface.
All API-specific data mapping happens here — the rest of the
app only sees domain CalendarEvent objects.
"""

from datetime import datetime
from typing import Any

from src.config.logging_config import get_logger
from src.domain.models.calendar_event import CalendarEvent
from src.infrastructure.google.google_auth import GoogleAuth

logger = get_logger(__name__)


class GoogleCalendarClient:
    """Read and write operations against the Google Calendar API."""

    def __init__(self, auth: GoogleAuth) -> None:
        self._auth = auth
        self._service: Any = None  # Will hold the googleapiclient Resource

    def _get_service(self) -> Any:
        """Lazily build the Calendar API service object.

        # TODO: Build with googleapiclient.discovery.build.
        """
        if self._service is None:
            creds = self._auth.authenticate()
            logger.info("Calendar API service created (stub)")
            # TODO: self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary",
    ) -> list[CalendarEvent]:
        """Fetch events within a time range.

        Args:
            time_min: Inclusive lower bound (UTC).
            time_max: Exclusive upper bound (UTC).
            calendar_id: Calendar to query (default: primary).

        Returns:
            List of domain CalendarEvent instances.

        # TODO: Call the real API and map raw dicts to CalendarEvent.
        """
        logger.info("Listing events from %s to %s (stub)", time_min, time_max)
        return []

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = "",
        calendar_id: str = "primary",
    ) -> CalendarEvent:
        """Create a new calendar event.

        # TODO: POST to the Calendar API and return the created event.
        """
        logger.info("Creating event '%s' (stub)", summary)
        return CalendarEvent(
            event_id="stub-id",
            summary=summary,
            description=description,
            start=start,
            end=end,
        )

    def update_event(
        self,
        event_id: str,
        updates: dict[str, Any],
        calendar_id: str = "primary",
    ) -> CalendarEvent:
        """Update an existing calendar event.

        # TODO: PATCH the Calendar API and return the updated event.
        """
        logger.info("Updating event %s (stub)", event_id)
        return CalendarEvent(
            event_id=event_id,
            summary=updates.get("summary", ""),
            start=updates.get("start", datetime.utcnow()),
            end=updates.get("end", datetime.utcnow()),
        )
