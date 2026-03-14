"""
Audio recording abstraction.

Provides a high-level interface for capturing microphone audio.
The actual hardware/driver interaction is stubbed for now.
"""

from pathlib import Path
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class AudioRecorder:
    """Records audio from a microphone source."""

    def __init__(self, sample_rate: int = 16_000, channels: int = 1) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._is_recording = False

    def start(self) -> None:
        """Begin capturing audio.

        # TODO: Implement actual PyAudio stream capture.
        """
        logger.info("Audio recording started (stub)")
        self._is_recording = True

    def stop(self) -> Optional[bytes]:
        """Stop capturing and return raw audio bytes.

        Returns:
            Raw audio data, or None if nothing was captured.

        # TODO: Return real captured audio data.
        """
        logger.info("Audio recording stopped (stub)")
        self._is_recording = False
        return None

    @property
    def is_recording(self) -> bool:
        return self._is_recording
