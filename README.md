# AIpril — Productivity Prompt Device

A Python application that periodically prompts the user to log what they are doing,
records their voice response, interprets it with AI, and integrates with Google Calendar.
Designed to work alongside an ESP32 hardware device.

## Architecture Overview

The project follows a **layered service-oriented architecture**:

| Layer | Purpose |
|---|---|
| `domain/` | Pure data models and enums — no external dependencies |
| `services/` | Business logic services (calendar, audio, transcription, etc.) |
| `application/` | Orchestrators and use cases that compose services |
| `infrastructure/` | External API integrations (Google, OpenAI, file storage) |
| `interfaces/` | User-facing entry points (CLI for now) |
| `config/` | Settings, logging, constants |
| `utils/` | Small focused helpers |

### Core Flows

- **Schedule Decision**: Check calendar → detect reclaim blocks → decide whether to prompt
- **User Input Capture**: Prompt → record voice / button press → transcribe → interpret → store
- **ESP32 Sync**: Simplify calendar into timestamp blocks → serialize for device
- **Data Management**: Store/index/delete audio files and metadata

## Directory Structure

```
src/
├── main.py                     # CLI entrypoint
├── app/                        # Bootstrap and DI container
├── config/                     # Settings, logging, constants
├── domain/
│   ├── models/                 # Pydantic data models
│   └── enums/                  # State and type enumerations
├── application/
│   ├── orchestrators/          # High-level flow coordinators
│   └── use_cases/              # Single-responsibility actions
├── services/
│   ├── calendar/               # Reclaim detection, schedule simplification
│   ├── audio/                  # Recording, playback, storage
│   ├── transcription/          # Speech-to-text abstraction
│   ├── interpretation/         # AI activity classification
│   ├── device/                 # ESP32 export
│   ├── input/                  # Button handling
│   ├── favorites/              # Saved favorite activities
│   ├── repeat/                 # Repeat-last-activity logic
│   └── network/                # Connectivity checks
├── infrastructure/
│   ├── google/                 # Google Auth + Calendar API client
│   ├── openai/                 # OpenAI transcription + parsing
│   └── persistence/            # Local file and metadata storage
├── interfaces/
│   └── cli/                    # CLI commands and menus
└── utils/                      # Datetime helpers, ID generation
tests/                          # Unit and integration tests
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your API keys
6. Set up Google Calendar credentials (see Google API Console)
7. Run: `python src/main.py`

## Future Work

- Full Google Calendar OAuth flow
- OpenAI Whisper transcription integration
- ESP32 serial communication
- Hardware button input via serial/BLE
- Web dashboard for reviewing logged activities
- Sleep/focus mode scheduling rules
- Multi-user support
