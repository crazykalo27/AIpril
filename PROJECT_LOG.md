# Project Log

Conceptual notes on changes and project status.

## 2026-03-14 — Cable-Only, No WiFi

**Goal**: ESP32 communicates only over USB cable. No WiFi. Server handles all APIs.

**Changes**:
- Removed WiFi, NTP from ESP32; deleted wifi_manager
- create_event uses server time (duration_minutes); ESP32 sends no timestamps
- Added list_events to server (Calendar API)
- secrets.h no longer required for ESP32

**Status**: Cable-only flow ready. Server: STT → LLM interpret → Calendar create/list.

## 2026-03-14 — Run app.py for voice flow

**Which to run**: `python app.py COM3` — web UI + serial. (main.py removed; app.py is the only server.)
**Flow**: Hold Record (browser) → play on laptop → send to ESP32 → ESP32 echoes back → STT → interpret → create event. Or use `/debug` with `--no-serial` to test without ESP32.
**Fix**: api_record_send_to_esp32 was missing `def` (IndentationError).

## 2026-03-14 — Web UI buttons + ESP32 Favorite pin

**Web UI**: Form had no method/action, causing GET submit and page reload on Save. Added method="POST" action="/api/settings", server accepts form data fallback. Button row: z-index, isolation, pointer-events for clickability.
**ESP32**: GPIO 35 (Favorite) has no internal pull-up — pin floats, erratic reads. Changed to GPIO 14 (has pull-up). Rewire Favorite button to GPIO 14.
**Web UI buttons (retry)**: Switched from inline onclick to addEventListener; init() runs on DOMContentLoaded. Added Cache-Control: no-store so browser doesn't serve stale page.

## 2026-03-14 — Audio Echo Pipeline Fix

**Goal**: Record in browser → send bytes to ESP32 → ESP32 echoes back → play echoed audio in browser.

**Bugs fixed**:
- **Race condition**: `_expecting_echo` was set AFTER sending data to ESP32. Serial thread could process the echo before the flag was set, causing timeout. Now set BEFORE sending.
- **No browser playback**: Echo path ran STT/interpret/calendar instead of returning audio. Replaced with simple byte storage + `/api/audio/last` endpoint for playback.
- **Phantom favorite on boot**: ButtonHandler initialized `lastState=HIGH` but GPIO0 reads LOW on boot, triggering a fake press. Now reads actual pin state in `begin()`.
- **Removed unnecessary local playback step**: JS no longer plays audio on laptop speakers before sending to ESP32.

**Status**: Echo pipeline working. Browser records → ESP32 echoes → browser plays back. Falls back to local storage when no ESP32 connected.
