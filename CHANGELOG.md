# Changelog

## 2026-03-14 — Initial Architecture Setup

- Created full project directory structure with layered architecture
- Domain models: CalendarEvent, VoiceRecord, InterpretedActivity, PromptWindow, ESP32ScheduleBlock, FavoriteActivity
- Domain enums: PromptState, InputSource
- Config layer: Settings (pydantic-settings), logging config, constants
- Services: ReclaimDetector, ScheduleSimplifier, AudioRecorder, BeepPlayer, AudioStorageManager, TranscriptionService (abstract), ActivityInterpreter (abstract), ESP32Exporter, ButtonHandler, FavoritesService, RepeatActivityService, ConnectivityService
- Infrastructure: GoogleAuth, GoogleCalendarClient, OpenAITranscriber, OpenAIActivityParser, FileMetadataStore, LocalFileStore
- Application use cases: DeterminePromptState, CaptureVoiceActivity, HandleRepeatActivity, HandleFavoriteActivity, ExportScheduleForDevice, DeleteVoiceRecord
- Application orchestrators: PromptCycleOrchestrator, ActivityCaptureOrchestrator, ESP32SyncOrchestrator
- DI container (ServiceContainer) with manual wiring
- CLI interface with interactive menu
- Starter tests for ReclaimDetector, ScheduleSimplifier, PromptDecision, FavoritesService
- Root files: README, requirements.txt, .env.example, .gitignore
