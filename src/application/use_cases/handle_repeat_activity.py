"""
Use case: handle the repeat-last-activity button press.

Returns a copy of the most recent interpreted activity with
a fresh timestamp.
"""

from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.interpreted_activity import InterpretedActivity
from src.domain.enums.input_source import InputSource
from src.services.repeat.repeat_activity_service import RepeatActivityService
from src.utils.datetime_utils import utc_now

logger = get_logger(__name__)


class HandleRepeatActivity:
    """Re-emits the last activity with an updated timestamp."""

    def __init__(self, repeat_service: RepeatActivityService) -> None:
        self._repeat = repeat_service

    def execute(self) -> Optional[InterpretedActivity]:
        """Produce a new activity record identical to the last one.

        Returns None if no previous activity exists.
        """
        last = self._repeat.get_last()
        if last is None:
            logger.warning("Repeat pressed but no previous activity found")
            return None

        repeated = last.model_copy(
            update={
                "timestamp": utc_now(),
                "input_source": InputSource.REPEAT_BUTTON,
            }
        )
        logger.info("Repeated activity: %s", repeated.summary)
        return repeated
