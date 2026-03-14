"""
OpenAI GPT activity parsing implementation.

Concrete ActivityInterpreter that uses GPT to classify a
transcript into a structured InterpretedActivity.
"""

from src.config.logging_config import get_logger
from src.domain.models.interpreted_activity import InterpretedActivity
from src.services.interpretation.activity_interpreter import ActivityInterpreter

logger = get_logger(__name__)


class OpenAIActivityParser(ActivityInterpreter):
    """Uses OpenAI GPT to interpret a transcript into an activity."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model = model

    def interpret(self, transcript: str) -> InterpretedActivity:
        """Send transcript to GPT and parse the response.

        # TODO: Implement real API call with structured output parsing.
        """
        logger.info("Interpreting transcript via OpenAI (stub)")
        return InterpretedActivity(
            summary=transcript or "unknown",
            raw_transcript=transcript,
        )
