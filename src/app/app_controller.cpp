/**
 * Application controller implementation.
 */

#include "app_controller.h"
#include "utils/time_utils.h"

AppController::AppController()
    : _googleAuth(_store, _http)
    , _calendar(_googleAuth, _http)
    , _transcriber(_http)
    , _interpreter(_http)
    , _buzzer(PIN_BUZZER)
    , _buttons(PIN_BTN_VOICE, PIN_BTN_REPEAT, PIN_BTN_FAVORITE)
    , _scheduler(PROMPT_INTERVAL_MS)
    , _reclaimDetector(RECLAIM_TAG)
{}

void AppController::begin() {
    Serial.println("\n=== AIpril v0 ===");

    // NVS
    _store.begin(NVS_NAMESPACE);

    // WiFi
    _wifi.connect(WIFI_SSID, WIFI_PASSWORD);

    // NTP time sync
    syncNtp(NTP_SERVER, NTP_GMT_OFFSET, NTP_DAYLIGHT_OFFSET);

    // Google auth
    _googleAuth.begin();

    // Hardware
    _recorder.begin(AUDIO_SAMPLE_RATE, PIN_I2S_BCLK, PIN_I2S_LRCK, PIN_I2S_DIN);
    _buzzer.begin();
    _buttons.begin();

    // Status LED
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);

    Serial.println("[App] Ready");
    _buzzer.success();
}

void AppController::update() {
    _buttons.update();

    // Button triggers
    if (_buttons.wasVoicePressed()) {
        handleVoiceCapture();
    }
    if (_buttons.wasRepeatPressed()) {
        handleRepeat();
    }
    if (_buttons.wasFavoritePressed()) {
        handleFavorite();
    }

    // Interval-based prompt
    if (_scheduler.shouldPrompt()) {
        _buzzer.prompt();
        _scheduler.reset();
        // Wait for button press (voice capture handled next loop)
    }

    // Serial commands
    handleSerial();

    delay(50);
}

void AppController::handleSerial() {
    if (!Serial.available()) return;

    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("set_token ")) {
        String token = line.substring(10);
        _googleAuth.setRefreshToken(token);
        Serial.println("OK — refresh token saved");
    }
    else if (line == "status") {
        Serial.printf("WiFi: %s\n", _wifi.isConnected() ? "connected" : "disconnected");
        Serial.printf("Google: %s\n", _googleAuth.isAuthenticated() ? "authenticated" : "no token");
        Serial.printf("Time: %s\n", formatRfc3339(nowUtc()).c_str());
    }
    else if (line == "record") {
        handleVoiceCapture();
    }
    else if (line == "help") {
        Serial.println("Commands: set_token <token>, status, record, help");
    }
}

// ---------------------------------------------------------------------------
// MVP: voice → transcribe → interpret → calendar
// ---------------------------------------------------------------------------
void AppController::handleVoiceCapture() {
    Serial.println("\n--- Voice Capture ---");
    _buzzer.prompt();

    // 1. Record
    size_t len = _recorder.record(AUDIO_RECORD_SECONDS);
    if (len == 0) {
        Serial.println("[App] Recording failed");
        _buzzer.error();
        return;
    }

    // 2. Transcribe (multipart POST — no base64)
    String transcript = _transcriber.transcribe(_recorder.getBuffer(), len);
    _recorder.clear();

    if (transcript.isEmpty()) {
        Serial.println("[App] Transcription returned empty");
        _buzzer.error();
        return;
    }

    // 3. Interpret (get event name from GPT)
    InterpretedActivity activity = _interpreter.interpret(transcript);

    // 4. Create calendar event
    time_t now = nowUtc();
    time_t end = now + 30 * 60;  // 30-minute default duration

    String eventId = _calendar.createEvent(
        activity.eventName, activity.transcript, now, end
    );

    if (eventId.isEmpty()) {
        Serial.println("[App] Calendar event creation failed");
        _buzzer.error();
        return;
    }

    // 5. Cache for repeat
    _lastActivity = activity;
    _hasLastActivity = true;

    Serial.printf("[App] Done: '%s' -> event %s\n",
                  activity.eventName.c_str(), eventId.c_str());
    _buzzer.success();
}

// ---------------------------------------------------------------------------
// Repeat: re-log last activity
// ---------------------------------------------------------------------------
void AppController::handleRepeat() {
    if (!_hasLastActivity) {
        Serial.println("[App] No previous activity to repeat");
        _buzzer.error();
        return;
    }

    time_t now = nowUtc();
    String eventId = _calendar.createEvent(
        _lastActivity.eventName, _lastActivity.transcript,
        now, now + 30 * 60
    );

    if (!eventId.isEmpty()) {
        Serial.printf("[App] Repeated: '%s'\n", _lastActivity.eventName.c_str());
        _buzzer.success();
    } else {
        _buzzer.error();
    }
}

// ---------------------------------------------------------------------------
// Favorite: log a saved activity (TODO: configurable)
// ---------------------------------------------------------------------------
void AppController::handleFavorite() {
    // TODO: Load favorites from NVS. For now use a default.
    String favName = _store.getString("fav_name", "Focus Work");
    String favDesc = _store.getString("fav_desc", "Deep focus block");

    time_t now = nowUtc();
    String eventId = _calendar.createEvent(favName, favDesc, now, now + 30 * 60);

    if (!eventId.isEmpty()) {
        Serial.printf("[App] Favorite: '%s'\n", favName.c_str());
        _buzzer.success();
    } else {
        _buzzer.error();
    }
}
