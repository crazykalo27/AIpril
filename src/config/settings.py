"""
Application settings loaded from environment variables.

Uses pydantic-settings for typed, validated configuration.
All configurable values live here — no magic strings scattered
throughout the codebase.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application configuration."""

    # OpenAI
    openai_api_key: str = ""

    # Google Calendar
    google_credentials_path: Path = Path("credentials.json")
    google_token_path: Path = Path("token.json")

    # Prompt schedule
    prompt_interval_minutes: int = 15

    # Audio
    audio_storage_dir: Path = Path("data/audio")

    # ESP32
    esp32_serial_port: str = "COM3"
    esp32_baud_rate: int = 115200

    # Logging
    log_level: str = "INFO"

    # Reclaim tag marker used inside Google Calendar event descriptions
    reclaim_tag: str = "[reclaim]"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


def load_settings() -> Settings:
    """Factory that returns a validated Settings instance."""
    return Settings()
