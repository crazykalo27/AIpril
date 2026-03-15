# AIpril — Voice-to-Calendar ESP32 Device

ESP32 firmware that records what you're doing via microphone,
transcribes and interprets it with OpenAI, and creates a Google Calendar event.

## Architecture (Server + ESP32 over Cable)

```
[User speaks] → [I2S mic] → [WAV buffer]
    → [USB Serial: AUDIO len + bytes] → [Server: OpenAI STT]
    → [USB Serial: JSON interpret]     → [Server: LLM interpret]
    → [USB Serial: JSON create_event] → [Server: Google Calendar API]
```

**ESP32** (`esp32-client/`): Records audio, sends over USB cable. No WiFi.
**Server** (`server/`): Runs on your computer, handles OpenAI (STT + LLM) and Google Calendar.

API keys live on the server only.

## Project Structure

```
AIpril/
├── esp32-client/           # PlatformIO ESP32 firmware
│   ├── src/
│   │   ├── main.cpp
│   │   ├── app/            # AppController
│   │   ├── config/         # WiFi, config
│   │   ├── domain/         # models, enums
│   │   ├── services/       # audio, buttons, calendar, prompt
│   │   ├── infrastructure/
│   │   │   ├── wire/       # WireClient (serial ↔ server)
│   │   │   └── storage/    # NVS
│   │   └── utils/
│   ├── include/            # pins.h, secrets.h
│   └── platformio.ini
└── server/                 # Python serial bridge + web UI
    ├── app.py              # Web UI (localhost:5000) + serial
    ├── handlers.py         # transcribe, interpret, create_event
    ├── settings.py         # Favorites, event labels (stored in settings.json)
    ├── google_auth.py      # OAuth + Calendar API (see AUTH.md)
    ├── config.py           # Env config
    └── tools/
        └── google_auth_setup.py   # One-time OAuth → token.json
```

## Setup

### 1. Server (run on your computer)

```bash
cd server
pip install -r requirements.txt
copy .env.example .env
# Edit .env: OPENAI_API_KEY, SERIAL_PORT (e.g. COM3)
python tools/google_auth_setup.py   # One-time: creates token.json for Google Calendar
```

### 2. ESP32

```bash
cd esp32-client
pio run -t upload
```

No WiFi or secrets needed — ESP32 communicates only over USB cable.

### 3. Run

1. Start server: `cd server && python app.py COM3` (use your port)
2. Open **http://localhost:5000** for settings
3. Open **http://localhost:5000/debug** to test STT without ESP32 — record from your computer mic
4. With ESP32: connect via USB, press voice button or send `record` over serial

**No hardware?** Run `python app.py --no-serial` and use `/debug` to record & test STT.

**Google Calendar**: Use OAuth, not an API key. See `server/AUTH.md`.

## Serial Commands (ESP32)

| Command | Description |
|---------|-------------|
| `record` | Manually trigger voice capture |
| `status` | Show WiFi and time |
| `help` | List commands |

## Wiring (INMP441 mic)

| INMP441 | ESP32 |
|---------|-------|
| BCLK    | GPIO 26 |
| LRCK    | GPIO 25 |
| DIN     | GPIO 33 |
| GND     | GND |
| VDD     | 3.3V |

Buzzer → GPIO 27. Buttons → GPIO 0, 32, 35.

## Future Work

- Configurable favorites via serial/NVS
- Reclaim-aware prompt suppression from live calendar
- Sleep/focus mode scheduling rules
- LED status indicators
- OTA firmware updates
