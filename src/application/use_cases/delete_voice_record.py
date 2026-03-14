"""
Use case: delete a voice record and its audio file.

Handles cleanup of both the audio file on disk and the
metadata entry in the store.
"""

from src.config.logging_config import get_logger
from src.services.audio.audio_storage_manager import AudioStorageManager
from src.infrastructure.persistence.file_metadata_store import FileMetadataStore

logger = get_logger(__name__)


class DeleteVoiceRecord:
    """Deletes audio and metadata for a given record ID."""

    def __init__(
        self,
        audio_storage: AudioStorageManager,
        metadata_store: FileMetadataStore,
    ) -> None:
        self._audio = audio_storage
        self._metadata = metadata_store

    def execute(self, record_id: str) -> bool:
        """Delete the audio file and metadata for the given record.

        Returns True if at least one artifact was removed.
        """
        audio_deleted = self._audio.delete(record_id)
        meta_deleted = self._metadata.delete_record(record_id)
        success = audio_deleted or meta_deleted
        if success:
            logger.info("Deleted record %s", record_id)
        else:
            logger.warning("Record %s not found for deletion", record_id)
        return success
