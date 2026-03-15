/**
 * Application controller implementation.
 *
 * Uses WireClient to communicate with host server over serial.
 * Server handles OpenAI (transcribe, interpret) and Google Calendar.
 */

#include "app_controller.h"
#include <string.h>

AppController::AppController()
    : _buzzer(PIN_BUZZER)
    , _buttons(PIN_BTN_VOICE, PIN_BTN_REPEAT, PIN_BTN_FAVORITE)
    , _scheduler(PROMPT_INTERVAL_MS)
    , _reclaimDetector(RECLAIM_TAG)
{}

void AppController::begin() {
    Serial.println("\n=== AIpril v0 ===");

    // NVS
    _store.begin(NVS_NAMESPACE);

    // Hardware (no WiFi — communicates with server over cable)
    _recorder.begin(AUDIO_SAMPLE_RATE, PIN_I2S_BCLK, PIN_I2S_LRCK, PIN_I2S_DIN);
    _buzzer.begin();
    _buttons.begin();

    // Status LED
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);

    Serial.println("[App] Ready");
    Serial.println("READY");  // Server uses this to confirm ESP32 is up
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

    // Triggers from server (web UI buttons)
    if (line == "PING") {
        Serial.println("PONG");
        return;
    }
    if (line == "trigger_record") {
        handleVoiceCapture();
        return;
    }
    if (line == "trigger_repeat") {
        handleRepeat();
        return;
    }
    if (line == "trigger_favorite") {
        handleFavorite();
        return;
    }
    if (line == "RETRIEVE_LAST") {
        handleRetrieveLast();
        return;
    }

    // Audio from server (hold-to-record on laptop) — echo back as if ESP32 recorded it
    if (line.startsWith("AUDIO_PLAYBACK ")) {
        handleAudioPlayback(line);
        return;
    }

    // Manual serial commands
    if (line == "status") {
        Serial.println("Ready (cable mode)");
    }
    else if (line == "record") {
        handleVoiceCapture();
    }
    else if (line == "help") {
        Serial.println("Commands: status, record, help");
    }
}

// ---------------------------------------------------------------------------
// MVP: voice → wire (transcribe) → wire (interpret) → wire (create_event)
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

    // 2. Transcribe via server
    WireResponse tr = _wire.transcribe(_recorder.getBuffer(), len);
    _recorder.clear();

    if (!tr.ok || tr.transcript.isEmpty()) {
        Serial.printf("[App] Transcription failed: %s\n", tr.error.c_str());
        _buzzer.error();
        return;
    }

    // 3. Interpret via server
    WireResponse interp = _wire.interpret(tr.transcript);
    InterpretedActivity activity;
    activity.transcript = tr.transcript;
    activity.eventName = interp.ok ? interp.eventName : tr.transcript.substring(0, 40);
    activity.category = interp.category;
    activity.source = InputSource::VOICE;

    // 4. Create calendar event via server (server uses its time)
    WireResponse cal = _wire.createEvent(activity.eventName, activity.transcript, 30);

    if (!cal.ok || cal.eventId.isEmpty()) {
        Serial.printf("[App] Calendar failed: %s\n", cal.error.c_str());
        _buzzer.error();
        return;
    }

    // 5. Cache for repeat
    _lastActivity = activity;
    _hasLastActivity = true;

    Serial.printf("[App] Done: '%s' -> event %s\n",
                  activity.eventName.c_str(), cal.eventId.c_str());
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

    WireResponse cal = _wire.createEvent(
        _lastActivity.eventName, _lastActivity.transcript, 30
    );

    if (cal.ok && !cal.eventId.isEmpty()) {
        Serial.printf("[App] Repeated: '%s'\n", _lastActivity.eventName.c_str());
        _buzzer.success();
    } else {
        _buzzer.error();
    }
}

// ---------------------------------------------------------------------------
// Audio playback: server sends laptop-recorded audio, we echo back as if we recorded it
// ---------------------------------------------------------------------------
void AppController::handleAudioPlayback(const String& line) {
    // Parse "AUDIO_PLAYBACK <len>"
    int spaceIdx = line.indexOf(' ');
    if (spaceIdx < 0) return;
    size_t len = (size_t)line.substring(spaceIdx + 1).toInt();
    if (len == 0 || len > 500000) return;  // Sanity limit ~500KB

    // Acknowledge receipt immediately so server knows we got the command
    Serial.printf("AUDIO_PLAYBACK_ACK %u\n", (unsigned)len);

    // Read bytes from Serial (server wrote them)
    uint8_t* buf = (uint8_t*)malloc(len);
    if (!buf) return;
    size_t got = 0;
    unsigned long start = millis();
    while (got < len && (millis() - start) < 30000) {
        while (Serial.available() && got < len) {
            buf[got++] = (uint8_t)Serial.read();
        }
        if (got < len) delay(5);
    }
    if (got != len) {
        free(buf);
        Serial.printf("[App] Audio playback: read %d/%d (timeout or incomplete)\n", (int)got, (int)len);
        return;
    }
    Serial.printf("[App] Audio playback: read %d bytes, storing and echoing...\n", (int)len);

    // Store for retrieve (replace previous)
    if (_storedAudio) free(_storedAudio);
    _storedAudio = (uint8_t*)malloc(len);
    if (_storedAudio) {
        memcpy(_storedAudio, buf, len);
        _storedAudioLen = len;
    }

    // Echo back as "AUDIO len\n" + bytes (same format as real recording)
    delay(300);
    Serial.print("AUDIO ");
    Serial.println(len);
    const size_t CHUNK = 512;
    for (size_t i = 0; i < len; i += CHUNK) {
        size_t n = min(CHUNK, len - i);
        Serial.write(buf + i, n);
    }
    free(buf);
    Serial.println("AUDIO_ECHO_DONE");
}

void AppController::handleRetrieveLast() {
    if (!_storedAudio || _storedAudioLen == 0) {
        Serial.println("[App] No stored audio to retrieve");
        return;
    }
    Serial.printf("[App] Retrieving %d bytes\n", (int)_storedAudioLen);
    Serial.print("AUDIO ");
    Serial.println(_storedAudioLen);
    const size_t CHUNK = 512;
    for (size_t i = 0; i < _storedAudioLen; i += CHUNK) {
        size_t n = min(CHUNK, _storedAudioLen - i);
        Serial.write(_storedAudio + i, n);
    }
    Serial.println("AUDIO_ECHO_DONE");
}

// ---------------------------------------------------------------------------
// Favorite: uses server settings (configure in web UI at localhost:5000)
// ---------------------------------------------------------------------------
void AppController::handleFavorite() {
    WireResponse cal = _wire.createFavorite(30);

    if (cal.ok && !cal.eventId.isEmpty()) {
        Serial.println("[App] Favorite logged");
        _buzzer.success();
    } else {
        _buzzer.error();
    }
}
