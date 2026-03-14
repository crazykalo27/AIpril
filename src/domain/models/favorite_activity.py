"""
Domain model for a user-saved favorite activity.

Favorites are quick-access activities the user can trigger
with a single button press instead of speaking.
"""

from pydantic import BaseModel, Field

from src.utils.id_utils import generate_id


class FavoriteActivity(BaseModel):
    """A saved favorite activity the user can recall instantly."""

    favorite_id: str = Field(default_factory=generate_id)
    label: str = Field(..., description="Short display name")
    summary: str = Field(..., description="Activity summary stored on selection")
    category: str = Field(default="general")
