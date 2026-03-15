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

## 2026-03-14 — STT + LLM Activity Extraction

**Goal**: After echo, transcribe the audio (OpenAI STT) and extract the activity name (GPT interpret).

**Changes**:
- Added `handle_transcribe_bytes` in handlers.py — accepts raw audio bytes instead of base64
- Echo endpoint now chains: echo → STT → interpret, returns `{transcript, event_name, category}`
- JS shows extracted activity and transcript in the result area
- `_last_activity` is stored for the Repeat button

**Status**: Full pipeline: record → echo → transcribe → extract activity → display. Uses event_labels from Settings for LLM matching.

## 2026-03-14 — Google Calendar OAuth in Web UI

**Goal**: Authenticate with Google Calendar through the localhost web UI before any features are usable.

**Changes**:
- Rewrote `google_auth.py`: replaced `InstalledAppFlow.run_local_server()` with web-based `Flow` that integrates with Flask routes
- Added `/auth/start` (redirects to Google consent), `/auth/callback` (exchanges code for token), `/api/auth/status` (returns auth state)
- Auth banner at top of page: shows Authenticated (green) or Not Authenticated (red) with an Authenticate button
- All features locked (`pointer-events: none`, grayed out) until Google OAuth is complete
- `credentials.json` from Google Cloud Console required in server/ directory

**Status**: Auth-gated UI. User must authenticate via the web page before using record/echo/calendar features.

## 2026-03-14 — Auto Calendar Event Creation

**Goal**: After STT + interpret, automatically create a 30-min Google Calendar event starting at the recording timestamp.

**Changes**:
- JS captures `new Date().toISOString()` when recording starts, sends as `start_time` form field
- `handle_create_event` accepts optional `start` datetime (uses it instead of server "now")
- Echo endpoint chains: echo → STT → interpret → create_event, returns `event_id`
- LLM prompt updated: must use existing label if one matches, only invent a name if none fit

**Status**: Full pipeline: record → echo → transcribe → match label → create 30-min calendar event at recording time.

## 2026-03-14 — Repeat, Favorite, and Duration Setting

**Changes**:
- Repeat button creates a new calendar event using the last activity's name/transcript, starting at "now"
- Favorite button creates a calendar event using the favorite name/desc from Settings, starting at "now"
- New "Event duration (minutes)" setting — all events (record, repeat, favorite) use this value
- Duration defaults to 30 min, configurable 5–480 in the UI

**Status**: All three buttons (Record, Repeat, Favorite) create real Google Calendar events with configurable duration.
