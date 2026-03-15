/**
 * HTTP client for communicating with the AIpril server over WiFi.
 *
 * Serial is kept for debug output only. All data goes over HTTP.
 */

#ifndef HTTP_CLIENT_H
#define HTTP_CLIENT_H

#include <Arduino.h>

struct HttpResponse {
    bool ok;
    String transcript;
    String eventName;
    String category;
    String eventId;
    String error;
};

class HttpClient {
public:
    void begin(const char* serverUrl);

    /// Call every loop — re-registers with server if needed.
    void update();

    /// POST raw WAV audio to /api/esp32/record. Server does STT + interpret + calendar.
    HttpResponse postAudio(const uint8_t* data, size_t len);

    /// POST to /api/trigger/repeat (server repeats last activity).
    HttpResponse postRepeat();

    /// POST to /api/trigger/favorite (server logs favorite).
    HttpResponse postFavorite();

    /// Tell server to start/stop recording from the computer mic.
    bool postRemoteRecord(bool start);

    bool isRegistered() const { return _registered; }

private:
    String _serverUrl;
    bool _registered = false;
    unsigned long _lastRegisterAttempt = 0;
    static const unsigned long REGISTER_INTERVAL_MS = 10000;

    bool tryRegister();
    HttpResponse parseJson(const String& body);
};

#endif
