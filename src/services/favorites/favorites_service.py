"""
Favorites management service.

Stores, retrieves, and selects user-defined favorite activities.
"""

from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.favorite_activity import FavoriteActivity

logger = get_logger(__name__)


class FavoritesService:
    """Manages the user's saved favorite activities."""

    def __init__(self) -> None:
        # TODO: Back this with persistent storage.
        self._favorites: dict[str, FavoriteActivity] = {}

    def add(self, favorite: FavoriteActivity) -> None:
        """Add or update a favorite activity."""
        self._favorites[favorite.favorite_id] = favorite
        logger.info("Favorite saved: %s", favorite.label)

    def remove(self, favorite_id: str) -> bool:
        """Remove a favorite by ID. Returns True if it existed."""
        removed = self._favorites.pop(favorite_id, None)
        return removed is not None

    def get(self, favorite_id: str) -> Optional[FavoriteActivity]:
        """Retrieve a favorite by ID."""
        return self._favorites.get(favorite_id)

    def get_default(self) -> Optional[FavoriteActivity]:
        """Return the first saved favorite, or None.

        # TODO: Support explicit default / ordering.
        """
        if self._favorites:
            return next(iter(self._favorites.values()))
        return None

    def list_all(self) -> list[FavoriteActivity]:
        """Return all saved favorites."""
        return list(self._favorites.values())
