"""
Generic local file storage abstraction.

Provides basic read/write/delete for arbitrary files, used as a
foundation that other stores can build on.
"""

from pathlib import Path
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class LocalFileStore:
    """Thin wrapper around local filesystem operations."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, filename: str, data: bytes) -> Path:
        """Write raw bytes to a file under the base directory."""
        path = self._base_dir / filename
        path.write_bytes(data)
        return path

    def read(self, filename: str) -> Optional[bytes]:
        """Read raw bytes from a file. Returns None if missing."""
        path = self._base_dir / filename
        if not path.exists():
            return None
        return path.read_bytes()

    def delete(self, filename: str) -> bool:
        """Delete a file. Returns True if it existed and was removed."""
        path = self._base_dir / filename
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, filename: str) -> bool:
        """Check whether a file exists."""
        return (self._base_dir / filename).exists()
