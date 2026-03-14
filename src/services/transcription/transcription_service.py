"""
Transcription service interface.

Defines the abstract contract for speech-to-text. Concrete
implementations live in infrastructure (e.g. OpenAI Whisper).
"""

from abc import ABC, abstractmethod
from pathlib import Path


class TranscriptionService(ABC):
    """Abstract base for any speech-to-text provider."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file and return the text.

        Args:
            audio_path: Path to the audio file on disk.

        Returns:
            The transcribed text string.
        """
        ...
