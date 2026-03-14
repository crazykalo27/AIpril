"""
Beep / notification sound player.

Plays an audible prompt to signal the user that input is requested.
"""

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class BeepPlayer:
    """Plays a short notification sound to prompt the user."""

    def play(self) -> None:
        """Play the prompt beep.

        # TODO: Implement actual audio playback (winsound, playsound, or hardware).
        """
        logger.info("BEEP — prompting user (stub)")
