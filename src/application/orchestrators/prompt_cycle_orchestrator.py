"""
Prompt cycle orchestrator.

Coordinates Flow A: checks the calendar, decides whether to prompt,
and triggers the beep if appropriate.  This is the top-level loop
that runs on a timer.
"""

from src.config.logging_config import get_logger
from src.application.use_cases.determine_prompt_state import DeterminePromptState
from src.services.audio.beep_player import BeepPlayer
from src.domain.enums.prompt_state import PromptState

logger = get_logger(__name__)


class PromptCycleOrchestrator:
    """Runs one prompt-decision cycle."""

    def __init__(
        self,
        determine_prompt: DeterminePromptState,
        beep_player: BeepPlayer,
    ) -> None:
        self._determine_prompt = determine_prompt
        self._beep_player = beep_player

    def run_cycle(self) -> PromptState:
        """Execute a single prompt cycle.

        Returns:
            The resolved PromptState for this cycle.
        """
        state = self._determine_prompt.execute()

        if state == PromptState.SHOULD_PROMPT:
            self._beep_player.play()
            logger.info("Prompt issued to user")
        else:
            logger.info("Prompt suppressed — state: %s", state.value)

        return state
