"""
Audio file storage management.

Handles saving, retrieving, and deleting audio files on disk.
Delegates metadata tracking to the persistence layer.
"""

from pathlib import Path
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class AudioStorageManager:
    """Manages audio file lifecycle on the local filesystem."""

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, record_id: str, audio_data: bytes, extension: str = ".wav") -> Path:
        """Write audio bytes to disk and return the file path.

        Args:
            record_id: Unique identifier used as the filename stem.
            audio_data: Raw audio bytes to persist.
            extension: File extension including the dot.
        """
        file_path = self._storage_dir / f"{record_id}{extension}"
        file_path.write_bytes(audio_data)
        logger.info("Saved audio file: %s", file_path)
        return file_path

    def load(self, record_id: str, extension: str = ".wav") -> Optional[bytes]:
        """Read audio bytes back from disk.

        Returns None if the file does not exist.
        """
        file_path = self._storage_dir / f"{record_id}{extension}"
        if not file_path.exists():
            logger.warning("Audio file not found: %s", file_path)
            return None
        return file_path.read_bytes()

    def delete(self, record_id: str, extension: str = ".wav") -> bool:
        """Delete an audio file. Returns True if the file was removed."""
        file_path = self._storage_dir / f"{record_id}{extension}"
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted audio file: %s", file_path)
            return True
        return False
