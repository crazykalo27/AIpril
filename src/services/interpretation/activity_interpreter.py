"""
Activity interpretation service interface.

Defines the abstract contract for converting a transcript into a
structured InterpretedActivity. Concrete implementations live in
infrastructure (e.g. OpenAI GPT).
"""

from abc import ABC, abstractmethod

from src.domain.models.interpreted_activity import InterpretedActivity


class ActivityInterpreter(ABC):
    """Abstract base for AI-powered activity classification."""

    @abstractmethod
    def interpret(self, transcript: str) -> InterpretedActivity:
        """Parse a transcript into a structured activity.

        Args:
            transcript: Raw transcription text from the user.

        Returns:
            An InterpretedActivity with summary, category, and confidence.
        """
        ...
