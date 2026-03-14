"""
Use case: capture a voice response, transcribe it, and interpret it.

Orchestrates the full voice-input pipeline: record → store →
transcribe → interpret → persist metadata.
"""

from typing import Optional

from src.config.logging_config import get_logger
from src.domain.models.voice_record import VoiceRecord
from src.domain.models.interpreted_activity import InterpretedActivity
from src.domain.enums.input_source import InputSource
from src.services.audio.audio_recorder import AudioRecorder
from src.services.audio.audio_storage_manager import AudioStorageManager
from src.services.transcription.transcription_service import TranscriptionService
from src.services.interpretation.activity_interpreter import ActivityInterpreter
from src.services.repeat.repeat_activity_service import RepeatActivityService
from src.infrastructure.persistence.file_metadata_store import FileMetadataStore

logger = get_logger(__name__)


class CaptureVoiceActivity:
    """Records voice, transcribes, interprets, and stores the result."""

    def __init__(
        self,
        recorder: AudioRecorder,
        storage: AudioStorageManager,
        transcriber: TranscriptionService,
        interpreter: ActivityInterpreter,
        metadata_store: FileMetadataStore,
        repeat_service: RepeatActivityService,
    ) -> None:
        self._recorder = recorder
        self._storage = storage
        self._transcriber = transcriber
        self._interpreter = interpreter
        self._metadata = metadata_store
        self._repeat = repeat_service

    def execute(self) -> Optional[InterpretedActivity]:
        """Run the full voice capture pipeline.

        Returns:
            The interpreted activity, or None if recording failed.

        # TODO: Wire in real recording and error handling.
        """
        self._recorder.start()
        audio_data = self._recorder.stop()

        if audio_data is None:
            logger.warning("No audio captured")
            return None

        record = VoiceRecord()
        audio_path = self._storage.save(record.record_id, audio_data)
        record.audio_path = audio_path

        transcript = self._transcriber.transcribe(audio_path)
        record.transcript = transcript
        self._metadata.save_record(record)

        activity = self._interpreter.interpret(transcript)
        activity.voice_record_id = record.record_id
        activity.input_source = InputSource.VOICE

        self._repeat.set_last(activity)
        logger.info("Voice activity captured: %s", activity.summary)
        return activity
