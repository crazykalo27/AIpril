"""
Use case: handle the favorite-activity button press.

Creates an InterpretedActivity from the user's default saved
favorite.
"""

from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.interpreted_activity import InterpretedActivity
from src.domain.enums.input_source import InputSource
from src.services.favorites.favorites_service import FavoritesService
from src.services.repeat.repeat_activity_service import RepeatActivityService
from src.utils.datetime_utils import utc_now

logger = get_logger(__name__)


class HandleFavoriteActivity:
    """Logs a favorite activity triggered by button press."""

    def __init__(
        self,
        favorites_service: FavoritesService,
        repeat_service: RepeatActivityService,
    ) -> None:
        self._favorites = favorites_service
        self._repeat = repeat_service

    def execute(self) -> Optional[InterpretedActivity]:
        """Fetch the default favorite and create an activity from it.

        Returns None if no favorites are configured.
        """
        fav = self._favorites.get_default()
        if fav is None:
            logger.warning("Favorite pressed but no favorites configured")
            return None

        activity = InterpretedActivity(
            summary=fav.summary,
            category=fav.category,
            input_source=InputSource.FAVORITE_BUTTON,
            timestamp=utc_now(),
            confidence=1.0,
        )
        self._repeat.set_last(activity)
        logger.info("Favorite activity logged: %s", activity.summary)
        return activity
