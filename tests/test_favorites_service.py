"""Tests for the favorites management service."""

from src.domain.models.favorite_activity import FavoriteActivity
from src.services.favorites.favorites_service import FavoritesService


def test_add_and_retrieve() -> None:
    service = FavoritesService()
    fav = FavoriteActivity(label="Coding", summary="Writing code", category="work")
    service.add(fav)
    assert service.get(fav.favorite_id) is not None
    assert service.get(fav.favorite_id).label == "Coding"


def test_remove() -> None:
    service = FavoritesService()
    fav = FavoriteActivity(label="Reading", summary="Reading a book")
    service.add(fav)
    assert service.remove(fav.favorite_id) is True
    assert service.get(fav.favorite_id) is None


def test_get_default_returns_first() -> None:
    service = FavoritesService()
    fav1 = FavoriteActivity(label="A", summary="First")
    fav2 = FavoriteActivity(label="B", summary="Second")
    service.add(fav1)
    service.add(fav2)
    default = service.get_default()
    assert default is not None
    assert default.label == "A"


def test_get_default_empty() -> None:
    service = FavoritesService()
    assert service.get_default() is None


def test_list_all() -> None:
    service = FavoritesService()
    service.add(FavoriteActivity(label="X", summary="x"))
    service.add(FavoriteActivity(label="Y", summary="y"))
    assert len(service.list_all()) == 2
