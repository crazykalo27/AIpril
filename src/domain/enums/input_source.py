"""
Enumeration of user input sources.

Tracks how the user provided their activity response.
"""

from enum import Enum


class InputSource(Enum):
    """How the user supplied their activity input."""

    VOICE = "voice"
    REPEAT_BUTTON = "repeat_button"
    FAVORITE_BUTTON = "favorite_button"
