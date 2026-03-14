"""
Activity capture orchestrator.

Coordinates Flow B: captures user input (voice / button),
transcribes, interprets, and stores the result.
"""

from typing import Optional

from src.config.logging_config import get_logger
from src.domain.enums.input_source import InputSource
from src.domain.models.interpreted_activity import InterpretedActivity
from src.application.use_cases.capture_voice_activity import CaptureVoiceActivity
from src.application.use_cases.handle_repeat_activity import HandleRepeatActivity
from src.application.use_cases.handle_favorite_activity import HandleFavoriteActivity

logger = get_logger(__name__)


class ActivityCaptureOrchestrator:
    """Routes user input to the correct capture use case."""

    def __init__(
        self,
        capture_voice: CaptureVoiceActivity,
        handle_repeat: HandleRepeatActivity,
        handle_favorite: HandleFavoriteActivity,
    ) -> None:
        self._capture_voice = capture_voice
        self._handle_repeat = handle_repeat
        self._handle_favorite = handle_favorite

    def capture(self, source: InputSource) -> Optional[InterpretedActivity]:
        """Dispatch to the right handler based on input source.

        Returns:
            The resulting InterpretedActivity, or None on failure.
        """
        if source == InputSource.VOICE:
            return self._capture_voice.execute()
        elif source == InputSource.REPEAT_BUTTON:
            return self._handle_repeat.execute()
        elif source == InputSource.FAVORITE_BUTTON:
            return self._handle_favorite.execute()
        else:
            logger.error("Unhandled input source: %s", source)
            return None
