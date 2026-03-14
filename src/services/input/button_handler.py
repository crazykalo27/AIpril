"""
Button input handler.

Translates physical or simulated button presses into domain actions.
Buttons: voice, repeat, favorite.
"""

from src.config.logging_config import get_logger
from src.domain.enums.input_source import InputSource

logger = get_logger(__name__)


class ButtonHandler:
    """Interprets button presses and returns the corresponding input source."""

    BUTTON_MAP: dict[str, InputSource] = {
        "voice": InputSource.VOICE,
        "repeat": InputSource.REPEAT_BUTTON,
        "favorite": InputSource.FAVORITE_BUTTON,
    }

    def resolve(self, button_id: str) -> InputSource:
        """Map a button identifier to an InputSource enum.

        Args:
            button_id: Logical name of the button pressed.

        Raises:
            ValueError: If the button_id is not recognised.
        """
        source = self.BUTTON_MAP.get(button_id.lower())
        if source is None:
            raise ValueError(f"Unknown button: {button_id}")
        logger.info("Button resolved: %s -> %s", button_id, source)
        return source
