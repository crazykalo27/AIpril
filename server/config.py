"""Server configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Serial
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")  # Windows: COM3, Linux: /dev/ttyUSB0
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200"))

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# Google OAuth
CREDENTIALS_FILE = Path(os.getenv("CREDENTIALS_FILE", "credentials.json"))
TOKEN_FILE = Path(os.getenv("TOKEN_FILE", "token.json"))
