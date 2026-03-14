"""
CLI command definitions.

Each public function here maps to a user-invocable command from
the CLI menu.
"""

from src.config.logging_config import get_logger
from src.app.container import ServiceContainer

logger = get_logger(__name__)


def cmd_run_prompt_cycle(container: ServiceContainer) -> None:
    """Manually trigger one prompt cycle."""
    state = container.prompt_cycle_orchestrator.run_cycle()
    print(f"Prompt cycle result: {state.value}")


def cmd_simulate_voice_input(container: ServiceContainer) -> None:
    """Simulate a voice input capture (stub)."""
    from src.domain.enums.input_source import InputSource
    result = container.activity_capture_orchestrator.capture(InputSource.VOICE)
    if result:
        print(f"Captured activity: {result.summary}")
    else:
        print("No activity captured (recording stub returned nothing)")


def cmd_simulate_repeat(container: ServiceContainer) -> None:
    """Simulate pressing the repeat button."""
    from src.domain.enums.input_source import InputSource
    result = container.activity_capture_orchestrator.capture(InputSource.REPEAT_BUTTON)
    if result:
        print(f"Repeated activity: {result.summary}")
    else:
        print("No previous activity to repeat")


def cmd_simulate_favorite(container: ServiceContainer) -> None:
    """Simulate pressing the favorite button."""
    from src.domain.enums.input_source import InputSource
    result = container.activity_capture_orchestrator.capture(InputSource.FAVORITE_BUTTON)
    if result:
        print(f"Favorite activity: {result.summary}")
    else:
        print("No favorites configured")


def cmd_export_esp32(container: ServiceContainer) -> None:
    """Export schedule blocks for the ESP32."""
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    container.esp32_sync_orchestrator.sync(now, now + timedelta(hours=8))
    print("ESP32 export complete (stub)")


def cmd_list_records(container: ServiceContainer) -> None:
    """List all stored voice record IDs."""
    ids = container.metadata_store.list_record_ids()
    if ids:
        for rid in ids:
            print(f"  {rid}")
    else:
        print("No records stored")
