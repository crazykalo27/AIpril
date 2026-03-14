"""
Schedule simplification service.

Converts a list of calendar events into compact schedule blocks
that the ESP32 or the prompt scheduler can consume.
"""

from datetime import datetime
from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.calendar_event import CalendarEvent
from src.domain.models.esp32_schedule_block import ESP32ScheduleBlock

logger = get_logger(__name__)


class ScheduleSimplifier:
    """Transforms calendar events into simplified schedule blocks."""

    def simplify(
        self,
        events: list[CalendarEvent],
        window_start: datetime,
        window_end: datetime,
    ) -> list[ESP32ScheduleBlock]:
        """Build a list of schedule blocks for the given time window.

        Gaps between events produce ``ask_user=True`` blocks.
        Reclaim events produce ``ask_user=False`` blocks.
        Non-reclaim events produce ``ask_user=False`` blocks as well
        (user is presumably busy).

        Args:
            events: Calendar events sorted by start time.
            window_start: Beginning of the window to cover.
            window_end: End of the window to cover.

        Returns:
            Ordered list of ESP32ScheduleBlock instances.
        """
        # TODO: Implement gap-filling algorithm between events
        blocks: list[ESP32ScheduleBlock] = []
        cursor = window_start

        for event in sorted(events, key=lambda e: e.start):
            if event.start > cursor:
                blocks.append(
                    ESP32ScheduleBlock(
                        start=cursor,
                        end=event.start,
                        ask_user=True,
                        label="free",
                    )
                )
            blocks.append(
                ESP32ScheduleBlock(
                    start=event.start,
                    end=event.end,
                    ask_user=False,
                    label="reclaim" if event.is_reclaim else "busy",
                )
            )
            cursor = max(cursor, event.end)

        if cursor < window_end:
            blocks.append(
                ESP32ScheduleBlock(
                    start=cursor,
                    end=window_end,
                    ask_user=True,
                    label="free",
                )
            )

        logger.info("Simplified %d events into %d blocks", len(events), len(blocks))
        return blocks
