"""
AIpril — application entrypoint.

Boots the system and launches the interactive CLI menu.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app.bootstrap import bootstrap
from src.interfaces.cli.menu import run_menu


def main() -> None:
    """Application entry point."""
    container = bootstrap()
    run_menu(container)


if __name__ == "__main__":
    main()
