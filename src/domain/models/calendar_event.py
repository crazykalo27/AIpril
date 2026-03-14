"""
Domain model for a Google Calendar event.

This is the internal representation — decoupled from the raw
Google API response so that the domain layer stays pure.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """A single calendar event in the domain."""

    event_id: str = Field(..., description="Unique event identifier from Google")
    summary: str = Field(default="", description="Event title / summary")
    description: str = Field(default="", description="Event description body")
    start: datetime = Field(..., description="Event start time (UTC)")
    end: datetime = Field(..., description="Event end time (UTC)")
    is_all_day: bool = Field(default=False)
    is_reclaim: bool = Field(
        default=False,
        description="Whether this event carries the reclaim tag",
    )
