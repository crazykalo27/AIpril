"""
Service container / dependency wiring.

Constructs all services and orchestrators with their dependencies
injected. Acts as a simple manual DI container.
"""

from pathlib import Path

from src.config.settings import Settings
from src.config.constants import GOOGLE_CALENDAR_SCOPE

from src.infrastructure.google.google_auth import GoogleAuth
from src.infrastructure.google.google_calendar_client import GoogleCalendarClient
from src.infrastructure.openai.openai_transcriber import OpenAITranscriber
from src.infrastructure.openai.openai_activity_parser import OpenAIActivityParser
from src.infrastructure.persistence.file_metadata_store import FileMetadataStore

from src.services.calendar.reclaim_detector import ReclaimDetector
from src.services.calendar.schedule_simplifier import ScheduleSimplifier
from src.services.audio.audio_recorder import AudioRecorder
from src.services.audio.audio_storage_manager import AudioStorageManager
from src.services.audio.beep_player import BeepPlayer
from src.services.device.esp32_exporter import ESP32Exporter
from src.services.favorites.favorites_service import FavoritesService
from src.services.repeat.repeat_activity_service import RepeatActivityService
from src.services.network.connectivity_service import ConnectivityService

from src.application.use_cases.determine_prompt_state import DeterminePromptState
from src.application.use_cases.capture_voice_activity import CaptureVoiceActivity
from src.application.use_cases.handle_repeat_activity import HandleRepeatActivity
from src.application.use_cases.handle_favorite_activity import HandleFavoriteActivity
from src.application.use_cases.export_schedule_for_device import ExportScheduleForDevice
from src.application.use_cases.delete_voice_record import DeleteVoiceRecord

from src.application.orchestrators.prompt_cycle_orchestrator import PromptCycleOrchestrator
from src.application.orchestrators.activity_capture_orchestrator import ActivityCaptureOrchestrator
from src.application.orchestrators.esp32_sync_orchestrator import ESP32SyncOrchestrator


class ServiceContainer:
    """Holds all wired-up service instances for the application."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # --- Infrastructure ---
        self.google_auth = GoogleAuth(
            credentials_path=settings.google_credentials_path,
            token_path=settings.google_token_path,
            scopes=[GOOGLE_CALENDAR_SCOPE],
        )
        self.calendar_client = GoogleCalendarClient(auth=self.google_auth)
        self.transcriber = OpenAITranscriber(api_key=settings.openai_api_key)
        self.activity_parser = OpenAIActivityParser(api_key=settings.openai_api_key)
        self.metadata_store = FileMetadataStore(storage_dir=settings.audio_storage_dir)

        # --- Services ---
        self.reclaim_detector = ReclaimDetector(reclaim_tag=settings.reclaim_tag)
        self.schedule_simplifier = ScheduleSimplifier()
        self.audio_recorder = AudioRecorder()
        self.audio_storage = AudioStorageManager(storage_dir=settings.audio_storage_dir)
        self.beep_player = BeepPlayer()
        self.esp32_exporter = ESP32Exporter()
        self.favorites_service = FavoritesService()
        self.repeat_service = RepeatActivityService()
        self.connectivity_service = ConnectivityService()

        # --- Use Cases ---
        self.determine_prompt = DeterminePromptState(
            calendar_client=self.calendar_client,
            reclaim_detector=self.reclaim_detector,
        )
        self.capture_voice = CaptureVoiceActivity(
            recorder=self.audio_recorder,
            storage=self.audio_storage,
            transcriber=self.transcriber,
            interpreter=self.activity_parser,
            metadata_store=self.metadata_store,
            repeat_service=self.repeat_service,
        )
        self.handle_repeat = HandleRepeatActivity(repeat_service=self.repeat_service)
        self.handle_favorite = HandleFavoriteActivity(
            favorites_service=self.favorites_service,
            repeat_service=self.repeat_service,
        )
        self.export_schedule = ExportScheduleForDevice(
            calendar_client=self.calendar_client,
            reclaim_detector=self.reclaim_detector,
            simplifier=self.schedule_simplifier,
            exporter=self.esp32_exporter,
        )
        self.delete_voice_record = DeleteVoiceRecord(
            audio_storage=self.audio_storage,
            metadata_store=self.metadata_store,
        )

        # --- Orchestrators ---
        self.prompt_cycle_orchestrator = PromptCycleOrchestrator(
            determine_prompt=self.determine_prompt,
            beep_player=self.beep_player,
        )
        self.activity_capture_orchestrator = ActivityCaptureOrchestrator(
            capture_voice=self.capture_voice,
            handle_repeat=self.handle_repeat,
            handle_favorite=self.handle_favorite,
        )
        self.esp32_sync_orchestrator = ESP32SyncOrchestrator(
            export_use_case=self.export_schedule,
        )
