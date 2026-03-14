"""
ESP32 sync orchestrator.

Coordinates Flow C: fetches calendar data, simplifies it into
schedule blocks, and exports them for the ESP32.
"""

from datetime import datetime

from src.config.logging_config import get_logger
from src.application.use_cases.export_schedule_for_device import ExportScheduleForDevice

logger = get_logger(__name__)


class ESP32SyncOrchestrator:
    """Builds and pushes a simplified schedule to the ESP32."""

    def __init__(self, export_use_case: ExportScheduleForDevice) -> None:
        self._export = export_use_case

    def sync(self, window_start: datetime, window_end: datetime) -> None:
        """Run a full sync cycle for the given time window.

        # TODO: Add error handling, retry, and connectivity checks.
        """
        self._export.execute(window_start, window_end)
        logger.info("ESP32 sync complete for %s – %s", window_start, window_end)
