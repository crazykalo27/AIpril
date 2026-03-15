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

## 2026-03-15 — WiFi Communication (Serial kept for debug)

**Goal**: ESP32 sends audio and commands to server over WiFi HTTP, not serial. Serial kept for debug output.

**ESP32 changes**:
- New `secrets.h` with WIFI_SSID, WIFI_PASSWORD, SERVER_URL
- `main.cpp` connects to WiFi on boot, reconnects if dropped
- New `HttpClient` class (WiFi + HTTPClient) replaces serial-based `WireClient`
- `handleVoiceCapture()` records audio → HTTP POST raw WAV to `/api/esp32/record`
- `handleRepeat()` and `handleFavorite()` POST to existing server endpoints
- Serial still active for debug prints and manual commands (record, repeat, status, help)
- I2S DIN moved to pin 34 (pin 33 used for repeat button)

**Server changes**:
- New `/api/esp32/record` endpoint accepts raw WAV bytes, runs STT → interpret → calendar
- Server binds to `0.0.0.0:5000` so ESP32 can reach it over the local network
- Prints local IP on startup for easy `SERVER_URL` configuration
- Serial thread still runs for debug monitoring and browser echo pipeline

**Status**: Dual communication — WiFi for ESP32 data, serial for debugging. Browser UI unchanged.

## 2026-03-15 — Server Debug Logging

**Goal**: More verbose debug output for each step, visible in the web UI debug log and server console.

**Changes**:
- Added `_debug()` helper and `_debug_log` buffer (last 100 entries)
- All API handlers log step-by-step with source: `browser`, `esp32_wifi`, or `serial`
- Record flow: receive → store → STT → LLM → calendar (each step logged)
- Ping: HTTP GET to ESP32 WiFi, response logged
- Repeat/Favorite: source detected (browser vs esp32_wifi by IP)
- ESP32 register/record: full pipeline logged with `esp32_wifi` source
- Serial: RX lines, PONG, REPEAT, AUDIO, commands logged with `serial` source
- New `/api/debug/log` endpoint returns recent entries
- Debug log panel: when opened, polls server every 2s to show ESP32 activity
- API responses include `debug_log` array; client appends to UI log

## 2026-03-15 — One-Day Calendar View

**Goal**: Replace "What's On Now" with a full-day calendar view.

**Changes**:
- New `handle_today_events()` in handlers.py — fetches all events for current day (UTC)
- New `/api/calendar/day` endpoint
- New "Today" card: shows date, event list (chronological), Refresh button
- Auto-refresh when adding event via Record, Repeat, or Favorite

## 2026-03-15 — Repeat Button Pin 25, Ping Beep on Pin 33

**Goal**: Move repeat button to pin 25; beep speaker on pin 33 when ping received.

**Changes**:
- Repeat button: pin 33 → 25 (I2S LRCK moved to 15 to free 25)
- Pin 33: PWM speaker for ping beep (ledc channel 1)
- Beep on both HTTP /ping and serial PING

## 2026-03-15 — ESP32 Auto-Reconnect to Server

**Goal**: ESP32 re-registers with server when server restarts.

**Changes**:
- `HttpClient::update()` called every loop — retries register every 10s if not connected
- Any HTTP failure sets `_registered = false`, triggering re-register
- WiFi reconnect already existed in `main.cpp`; now server reconnect also handled

## 2026-03-15 — Second Voice Button on GPIO 19

**Changes**:
- GPIO 19: INPUT_PULLUP, second voice/record button (to GND)
- Either GPIO 0 (BOOT) or GPIO 19 triggers `handleVoiceCapture()`
- Browser hold-to-record unchanged and works independently
