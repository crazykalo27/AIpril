"""
Interactive CLI menu.

Presents a simple numbered menu and dispatches to command functions.
"""

from src.config.logging_config import get_logger
from src.app.container import ServiceContainer
from src.interfaces.cli import commands

logger = get_logger(__name__)

MENU_OPTIONS = [
    ("Run prompt cycle", commands.cmd_run_prompt_cycle),
    ("Simulate voice input", commands.cmd_simulate_voice_input),
    ("Simulate repeat button", commands.cmd_simulate_repeat),
    ("Simulate favorite button", commands.cmd_simulate_favorite),
    ("Export schedule to ESP32", commands.cmd_export_esp32),
    ("List stored records", commands.cmd_list_records),
]


def run_menu(container: ServiceContainer) -> None:
    """Display an interactive command menu in a loop."""
    while True:
        print("\n=== AIpril CLI ===")
        for i, (label, _) in enumerate(MENU_OPTIONS, start=1):
            print(f"  {i}. {label}")
        print("  0. Exit")

        choice = input("\nSelect: ").strip()
        if choice == "0":
            print("Goodbye.")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MENU_OPTIONS):
                _, handler = MENU_OPTIONS[idx]
                handler(container)
            else:
                print("Invalid selection")
        except (ValueError, IndexError):
            print("Invalid input")
        except KeyboardInterrupt:
            print("\nExiting.")
            break
