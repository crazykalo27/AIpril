# Changelog

## 2026-03-14 — Serial Fix + Retrieve

- **Server**: serial_loop now uses readline() — was consuming binary bytes via decode(), causing echo timeout
- **ESP32**: stores last AUDIO_PLAYBACK in RAM; RETRIEVE_LAST resends it
- **Server**: "Retrieve most recent" button — asks ESP32 to resend stored audio, runs STT flow

## 2026-03-14 — Ping + Debug for Serial

- **Server**: Ping button + `/api/ping` — sends PING, waits for PONG (3s timeout)
- **Server**: serial_loop logs every RX line; handles READY, AUDIO_PLAYBACK_ACK, AUDIO_ECHO_DONE
- **ESP32**: Sends READY on startup; responds PONG to PING
- **ESP32**: Sends AUDIO_PLAYBACK_ACK len immediately on receive; AUDIO_ECHO_DONE after echo

## 2026-03-14 — ESP32 Build Fix

- **Fixed** `esp32` env build: `main.cpp` and `main_test_serial.cpp` both define `setup()`/`loop()` — linker error
- **platformio.ini**: `build_src_filter = +<*> -<main_test_serial.cpp>` for esp32 env so test sketch excluded
- **Upload**: use `pio run -e esp32 -t upload` for main firmware; `pio run -e test -t upload` for minimal serial test

## 2026-03-14 — Server/Client Split (Wire over Serial)

- **Moved** all C/PlatformIO code into `esp32-client/`
- **Created** `server/` — Python serial bridge that runs on host PC
  - Listens on serial port for JSON commands from ESP32
  - Handles OpenAI (transcribe, interpret) and Google Calendar API
  - Protocol: `AUDIO <len>\n` + raw bytes for transcribe; JSON lines for interpret/create_event
- **Removed from ESP32**: HttpsClient, GoogleAuth, GoogleCalendar, OpenAITranscriber, OpenAIInterpreter
- **Added** `WireClient` — serial communication with server (transcribe, interpret, createEvent)
- **ESP32** now only needs WiFi (for NTP); API keys live on server
- **tools/** moved to `server/tools/` — google_auth_setup.py creates token.json for server

## 2026-03-14 — Full C++ Refactor for ESP32

- **Deleted** entire Python codebase (src/, tests/, docs/, requirements.txt, .env.example)
- **Deleted** old Arduino-style esp32/ directory
- **Created** PlatformIO project at root level targeting ESP32
- **Architecture**: Same layered modular design, ported to C++ header/implementation pairs
  - `domain/` — models.h (structs), enums.h
  - `services/` — I2S recorder, buzzer, reclaim detector, schedule builder, button handler, prompt scheduler
  - `infrastructure/` — Wire client (serial), NVS store; API clients removed
  - `app/` — AppController top-level orchestrator
  - `config/` — compile-time config, WiFi manager
  - `utils/` — time formatting, JSON helpers
- **Unit tests**: PlatformIO test with Unity for reclaim detector and scheduler

## 2026-03-14 — Initial Architecture Setup (Python — now deleted)

- Original Python architecture with layered services, domain models, orchestrators
- Flask HTTP server for ESP32 backend
- OpenAI single-call gpt-audio approach (replaced with two-call for ESP32 memory)
