/**
 * Application controller implementation.
 *
 * Uses HttpClient (WiFi) for server communication.
 * Runs a WebServer on port 80 so the server can ping the ESP32.
 * Serial is for debug output and manual commands only.
 */

#include "app_controller.h"
#include "secrets.h"

AppController::AppController()
    : _buzzer(PIN_BUZZER)
    , _buttons(PIN_BTN_VOICE, PIN_BTN_REPEAT, PIN_BTN_FAVORITE)
    , _scheduler(PROMPT_INTERVAL_MS)
    , _reclaimDetector(RECLAIM_TAG)
    , _webServer(80)
{}

#define PING_BEEP_CHANNEL  1
#define PING_BEEP_HZ       2000
#define PING_BEEP_MS       100

void AppController::pingBeep() {
    ledcWriteTone(PING_BEEP_CHANNEL, PING_BEEP_HZ);
    delay(PING_BEEP_MS);
    ledcWriteTone(PING_BEEP_CHANNEL, 0);
}

void AppController::setupWebServer() {
    _webServer.on("/ping", HTTP_GET, [this]() {
        Serial.println("[HTTP] /ping → PONG");
        pingBeep();
        _webServer.send(200, "application/json", "{\"ok\":true,\"message\":\"PONG\"}");
    });

    _webServer.on("/status", HTTP_GET, [this]() {
        String json = "{\"ok\":true,\"wifi\":true,\"ip\":\"" + WiFi.localIP().toString() + "\"}";
        _webServer.send(200, "application/json", json);
    });

    _webServer.begin();
    Serial.printf("[HTTP] ESP32 web server on port 80 (IP: %s)\n", WiFi.localIP().toString().c_str());
}

void AppController::begin() {
    Serial.println("\n=== AIpril v0 (WiFi) ===");

    _store.begin(NVS_NAMESPACE);

    _http.begin(SERVER_URL);
    _recorder.begin(AUDIO_SAMPLE_RATE, PIN_I2S_BCLK, PIN_I2S_LRCK, PIN_I2S_DIN);
    _buzzer.begin();
    _buttons.begin();

    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);
    pinMode(PIN_LED_REPEAT, OUTPUT);
    digitalWrite(PIN_LED_REPEAT, LOW);

    ledcSetup(PING_BEEP_CHANNEL, PING_BEEP_HZ, 8);
    ledcAttachPin(PIN_PING_SPEAKER, PING_BEEP_CHANNEL);
    ledcWrite(PING_BEEP_CHANNEL, 0);

    if (WiFi.status() == WL_CONNECTED) {
        setupWebServer();
    }

    Serial.println("[App] Ready");
    _buzzer.success();
}

void AppController::update() {
    _http.update();
    _webServer.handleClient();
    _buttons.update();

    if (_buttons.wasVoicePressed()) {
        handleVoiceCapture();
    }
    if (_buttons.wasRepeatPressed()) {
        handleRepeat();
    }
    if (_buttons.wasFavoritePressed()) {
        handleFavorite();
    }

    if (_scheduler.shouldPrompt()) {
        _buzzer.prompt();
        _scheduler.reset();
    }

    handleSerial();
    delay(10);
}

void AppController::handleSerial() {
    if (!Serial.available()) return;

    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line == "PING") {
        pingBeep();
        Serial.println("PONG");
    } else if (line == "record") {
        handleVoiceCapture();
    } else if (line == "repeat") {
        handleRepeat();
    } else if (line == "favorite") {
        handleFavorite();
    } else if (line == "status") {
        Serial.printf("WiFi: %s, IP: %s\n",
            WiFi.status() == WL_CONNECTED ? "connected" : "disconnected",
            WiFi.localIP().toString().c_str());
    } else if (line == "help") {
        Serial.println("Commands: record, repeat, favorite, status, help");
    }
}

// ---------------------------------------------------------------------------
// Voice: record → POST audio to server over WiFi
// ---------------------------------------------------------------------------
void AppController::handleVoiceCapture() {
    Serial.println("\n--- Voice Capture ---");
    _buzzer.prompt();

    size_t len = _recorder.record(AUDIO_RECORD_SECONDS);
    if (len == 0) {
        Serial.println("[App] Recording failed");
        _buzzer.error();
        return;
    }

    Serial.printf("[App] Recorded %u bytes, sending to server...\n", (unsigned)len);
    HttpResponse resp = _http.postAudio(_recorder.getBuffer(), len);
    _recorder.clear();

    if (!resp.ok) {
        Serial.printf("[App] Error: %s\n", resp.error.c_str());
        _buzzer.error();
        return;
    }

    Serial.printf("[App] '%s' → %s (event %s)\n",
                  resp.transcript.c_str(),
                  resp.eventName.c_str(),
                  resp.eventId.c_str());

    _lastEventName = resp.eventName;
    _hasLastActivity = true;
    _buzzer.success();
}

// ---------------------------------------------------------------------------
// Repeat: POST to server, flash LED
// ---------------------------------------------------------------------------
void AppController::handleRepeat() {
    Serial.println("[App] Repeat");
    digitalWrite(PIN_LED_REPEAT, HIGH);

    HttpResponse resp = _http.postRepeat();

    if (resp.ok) {
        Serial.printf("[App] Repeated: %s (event %s)\n",
                      resp.eventName.c_str(), resp.eventId.c_str());
        _buzzer.success();
    } else {
        Serial.printf("[App] Repeat error: %s\n", resp.error.c_str());
        _buzzer.error();
    }

    delay(1000);
    digitalWrite(PIN_LED_REPEAT, LOW);
}

// ---------------------------------------------------------------------------
// Favorite: POST to server
// ---------------------------------------------------------------------------
void AppController::handleFavorite() {
    Serial.println("[App] Favorite");

    HttpResponse resp = _http.postFavorite();

    if (resp.ok) {
        Serial.printf("[App] Favorite: %s (event %s)\n",
                      resp.eventName.c_str(), resp.eventId.c_str());
        _buzzer.success();
    } else {
        Serial.printf("[App] Favorite error: %s\n", resp.error.c_str());
        _buzzer.error();
    }
}
