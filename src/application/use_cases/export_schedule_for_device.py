"""
Use case: export a simplified schedule to the ESP32 device.

Fetches calendar events, simplifies them into blocks, and
sends them via the ESP32 exporter.
"""

from datetime import datetime

from src.config.logging_config import get_logger
from src.infrastructure.google.google_calendar_client import GoogleCalendarClient
from src.services.calendar.reclaim_detector import ReclaimDetector
from src.services.calendar.schedule_simplifier import ScheduleSimplifier
from src.services.device.esp32_exporter import ESP32Exporter

logger = get_logger(__name__)


class ExportScheduleForDevice:
    """Builds and transmits schedule blocks for the ESP32."""

    def __init__(
        self,
        calendar_client: GoogleCalendarClient,
        reclaim_detector: ReclaimDetector,
        simplifier: ScheduleSimplifier,
        exporter: ESP32Exporter,
    ) -> None:
        self._calendar = calendar_client
        self._reclaim = reclaim_detector
        self._simplifier = simplifier
        self._exporter = exporter

    def execute(self, window_start: datetime, window_end: datetime) -> None:
        """Run the full export pipeline.

        # TODO: Add error handling and connectivity checks.
        """
        events = self._calendar.list_events(window_start, window_end)
        self._reclaim.tag_events(events)
        blocks = self._simplifier.simplify(events, window_start, window_end)
        self._exporter.send(blocks)
        logger.info("Exported %d blocks to ESP32", len(blocks))
