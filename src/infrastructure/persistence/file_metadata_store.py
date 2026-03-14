"""
Metadata store for voice records and interpreted activities.

Persists metadata as JSON files so we have an index of all
captured data without needing a database.
"""

import json
from pathlib import Path
from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.voice_record import VoiceRecord

logger = get_logger(__name__)


class FileMetadataStore:
    """JSON-file-backed metadata storage for voice records."""

    def __init__(self, storage_dir: Path) -> None:
        self._dir = storage_dir / "metadata"
        self._dir.mkdir(parents=True, exist_ok=True)

    def save_record(self, record: VoiceRecord) -> None:
        """Persist a VoiceRecord's metadata as a JSON file."""
        path = self._dir / f"{record.record_id}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Metadata saved: %s", path)

    def load_record(self, record_id: str) -> Optional[VoiceRecord]:
        """Load a VoiceRecord by its ID. Returns None if not found."""
        path = self._dir / f"{record_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return VoiceRecord(**data)

    def delete_record(self, record_id: str) -> bool:
        """Delete metadata for a record. Returns True if removed."""
        path = self._dir / f"{record_id}.json"
        if path.exists():
            path.unlink()
            logger.info("Metadata deleted: %s", path)
            return True
        return False

    def list_record_ids(self) -> list[str]:
        """Return all stored record IDs."""
        return [p.stem for p in self._dir.glob("*.json")]
