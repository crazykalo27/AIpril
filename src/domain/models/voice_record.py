"""
Domain model for a captured voice recording.

Represents a single audio file captured during a prompt cycle,
along with its metadata.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from src.utils.id_utils import generate_id


class VoiceRecord(BaseModel):
    """Metadata for one voice recording."""

    record_id: str = Field(default_factory=generate_id)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_path: Optional[Path] = Field(
        default=None, description="Path to the stored audio file"
    )
    duration_seconds: Optional[float] = None
    transcript: Optional[str] = None
