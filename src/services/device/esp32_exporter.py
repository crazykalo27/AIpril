"""
ESP32 schedule export service.

Serializes schedule blocks into a compact format that can be
transmitted to an ESP32 device over serial or another transport.
"""

import json
from typing import Any

from src.config.logging_config import get_logger
from src.config.constants import ESP32_EXPORT_VERSION
from src.domain.models.esp32_schedule_block import ESP32ScheduleBlock

logger = get_logger(__name__)


class ESP32Exporter:
    """Serializes schedule blocks for ESP32 consumption."""

    def to_json(self, blocks: list[ESP32ScheduleBlock]) -> str:
        """Serialize blocks to a JSON string.

        The format is intentionally compact so it fits in limited
        device memory.
        """
        payload: dict[str, Any] = {
            "v": ESP32_EXPORT_VERSION,
            "blocks": [
                {
                    "s": int(b.start.timestamp()),
                    "e": int(b.end.timestamp()),
                    "a": b.ask_user,
                }
                for b in blocks
            ],
        }
        return json.dumps(payload, separators=(",", ":"))

    def send(self, blocks: list[ESP32ScheduleBlock]) -> None:
        """Transmit schedule blocks to the ESP32.

        # TODO: Implement serial write via pyserial.
        """
        data = self.to_json(blocks)
        logger.info("Would send %d bytes to ESP32 (stub)", len(data))
