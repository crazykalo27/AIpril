"""
Domain model for an AI-interpreted activity.

After a voice recording is transcribed, the AI interprets the
transcript into a structured activity description.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.utils.id_utils import generate_id
from src.domain.enums.input_source import InputSource


class InterpretedActivity(BaseModel):
    """Structured representation of what the user was doing."""

    activity_id: str = Field(default_factory=generate_id)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    summary: str = Field(..., description="Short human-readable activity label")
    category: Optional[str] = Field(
        default=None, description="Optional activity category (e.g. 'work', 'break')"
    )
    raw_transcript: Optional[str] = None
    voice_record_id: Optional[str] = None
    input_source: InputSource = InputSource.VOICE
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="AI confidence score"
    )
