"""
OpenAI Whisper transcription implementation.

Concrete TranscriptionService that calls the OpenAI Whisper API.
"""

from pathlib import Path

from src.config.logging_config import get_logger
from src.services.transcription.transcription_service import TranscriptionService

logger = get_logger(__name__)


class OpenAITranscriber(TranscriptionService):
    """Transcribes audio using the OpenAI Whisper API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def transcribe(self, audio_path: Path) -> str:
        """Send an audio file to OpenAI Whisper and return text.

        # TODO: Implement real API call using the openai library.
        """
        logger.info("Transcribing %s via OpenAI Whisper (stub)", audio_path)
        return ""
