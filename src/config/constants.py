"""
Application-wide constants.

Values that are fixed at compile time and not user-configurable
belong here. Anything that should be changeable goes in settings.py.
"""

APP_NAME: str = "AIpril"
APP_VERSION: str = "0.1.0"

# Google Calendar API scope required for read/write access
GOOGLE_CALENDAR_SCOPE: str = "https://www.googleapis.com/auth/calendar"

# Default audio format settings
AUDIO_SAMPLE_RATE: int = 16_000
AUDIO_CHANNELS: int = 1
AUDIO_FORMAT_EXTENSION: str = ".wav"

# ESP32 export format version — bump when the schema changes
ESP32_EXPORT_VERSION: int = 1
