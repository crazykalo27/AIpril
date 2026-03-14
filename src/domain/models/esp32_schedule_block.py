"""
Domain model for a simplified schedule block sent to the ESP32.

These blocks are the compact representation the device uses to
decide whether it should beep and ask the user for input.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ESP32ScheduleBlock(BaseModel):
    """One time-block in the ESP32-consumable schedule."""

    start: datetime
    end: datetime
    ask_user: bool = Field(
        ..., description="True if the device should prompt during this block"
    )
    label: Optional[str] = Field(
        default=None, description="Optional short label for display/debug"
    )
