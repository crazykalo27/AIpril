"""
Domain model for a prompt scheduling window.

Represents a time range and whether the system should prompt
the user during that range.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from src.domain.enums.prompt_state import PromptState


class PromptWindow(BaseModel):
    """A time window with an associated prompt decision."""

    start: datetime
    end: datetime
    state: PromptState = PromptState.WAITING
    reason: str = Field(
        default="", description="Human-readable reason for the state"
    )
