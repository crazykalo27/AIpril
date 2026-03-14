# AIpril — Voice-to-Calendar ESP32 Device

ESP32 firmware that records what you're doing via microphone,
transcribes and interprets it with OpenAI, and creates a Google Calendar event.

## MVP Flow

```
[User speaks] → [I2S mic] → [WAV buffer]
    → [POST multipart to OpenAI /v1/audio/transcriptions] → transcript
    → [POST JSON to OpenAI /v1/chat/completions] → event name
    → [POST to Google Calendar API] → event created
```

**Two-call approach** (memory-efficient for ESP32):
1. Multipart POST raw WAV bytes → transcript (no base64 overhead)
2. JSON POST transcript text → structured event name

## Architecture

```
src/
├── main.cpp                              # setup() + loop()
├── app/
│   ├── app_controller.h/cpp              # Top-level orchestrator
├── config/
│   ├── config.h                          # Central compile-time config
│   └── wifi_manager.h/cpp                # WiFi connection
├── domain/
│   ├── models.h                          # CalendarEvent, VoiceRecord, etc.
│   └── enums.h                           # PromptState, InputSource
├── services/
│   ├── audio/
│   │   ├── i2s_recorder.h/cpp            # INMP441 I2S mic → WAV
│   │   └── buzzer.h/cpp                  # Beep/tone feedback
│   ├── calendar/
│   │   ├── reclaim_detector.h/cpp        # [reclaim] tag detection
│   │   └── schedule_builder.h/cpp        # Events → schedule blocks
│   ├── input/
│   │   └── button_handler.h/cpp          # Debounced button input
│   └── prompt/
│       └── prompt_scheduler.h/cpp        # Interval-based prompting
├── infrastructure/
│   ├── network/
│   │   └── https_client.h/cpp            # TLS HTTP client
│   ├── google/
│   │   ├── google_auth.h/cpp             # OAuth2 token refresh
│   │   └── google_calendar.h/cpp         # Calendar API
│   ├── openai/
│   │   ├── openai_transcriber.h/cpp      # Whisper transcription
│   │   └── openai_interpreter.h/cpp      # GPT event extraction
│   └── storage/
│       └── nvs_store.h/cpp               # NVS key-value persistence
└── utils/
    ├── time_utils.h/cpp                  # RFC3339 formatting, NTP
    └── json_helpers.h                    # ArduinoJson wrappers

include/
├── pins.h                                # Hardware pin assignments
└── secrets.h.example                     # API key template

tools/
└── google_auth_setup.py                  # One-time OAuth setup (run on PC)

test/
└── test_main.cpp                         # PlatformIO unit tests
```

## Setup

### 1. Google OAuth (run once on PC)

```bash
pip install google-auth-oauthlib
# Download credentials.json from Google Cloud Console
python tools/google_auth_setup.py
# Copy the refresh token
```

### 2. Configure secrets

```bash
cp include/secrets.h.example include/secrets.h
# Edit: WiFi SSID/password, OpenAI key, Google client ID/secret
# Optionally paste the refresh token as GOOGLE_REFRESH_TOKEN
```

### 3. Wiring (INMP441 mic)

| INMP441 | ESP32 |
|---------|-------|
| BCLK    | GPIO 26 |
| LRCK    | GPIO 25 |
| DIN     | GPIO 33 |
| GND     | GND |
| VDD     | 3.3V |

Buzzer → GPIO 27. Buttons → GPIO 0, 32, 35 (with internal pullups).

### 4. Build & Upload

```bash
# PlatformIO CLI
pio run -t upload
pio device monitor
```

Or open in PlatformIO IDE (VS Code extension).

### 5. Send refresh token via serial (if not in secrets.h)

```
set_token 1//your-refresh-token-here
```

## Serial Commands

| Command | Description |
|---------|-------------|
| `record` | Manually trigger voice capture |
| `status` | Show WiFi, auth, and time status |
| `set_token <token>` | Store Google refresh token in NVS |
| `help` | List commands |

## Future Work

- HTTPS certificate validation (currently uses `setInsecure()`)
- Configurable favorites via serial/NVS
- Reclaim-aware prompt suppression from live calendar
- Sleep/focus mode scheduling rules
- LED status indicators
- OTA firmware updates
