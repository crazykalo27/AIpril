# Changelog

## 2026-03-14 — Full C++ Refactor for ESP32

- **Deleted** entire Python codebase (src/, tests/, docs/, requirements.txt, .env.example)
- **Deleted** old Arduino-style esp32/ directory
- **Created** PlatformIO project at root level targeting ESP32
- **Architecture**: Same layered modular design, ported to C++ header/implementation pairs
  - `domain/` — models.h (structs), enums.h
  - `services/` — I2S recorder, buzzer, reclaim detector, schedule builder, button handler, prompt scheduler
  - `infrastructure/` — HTTPS client, Google OAuth, Google Calendar API, OpenAI transcriber, OpenAI interpreter, NVS store
  - `app/` — AppController top-level orchestrator
  - `config/` — compile-time config, WiFi manager
  - `utils/` — time formatting, JSON helpers
- **OpenAI: two-call approach** (more memory-efficient for ESP32)
  - Call 1: multipart POST raw WAV to /v1/audio/transcriptions → transcript
  - Call 2: JSON POST to /v1/chat/completions → event name
- **Google OAuth**: refresh token stored in NVS, set via serial or secrets.h
- **Google Calendar**: create_event and list_events fully implemented against REST API
- **tools/google_auth_setup.py**: one-time Python script for OAuth browser flow
- **Unit tests**: PlatformIO test with Unity for reclaim detector and scheduler

## 2026-03-14 — Initial Architecture Setup (Python — now deleted)

- Original Python architecture with layered services, domain models, orchestrators
- Flask HTTP server for ESP32 backend
- OpenAI single-call gpt-audio approach (replaced with two-call for ESP32 memory)
