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

    /// POST raw WAV audio to /api/esp32/record. Server does STT + interpret + calendar.
    HttpResponse postAudio(const uint8_t* data, size_t len);

    /// POST to /api/trigger/repeat (server repeats last activity).
    HttpResponse postRepeat();

    /// POST to /api/trigger/favorite (server logs favorite).
    HttpResponse postFavorite();

private:
    String _serverUrl;
    HttpResponse parseJson(const String& body);
};

#endif
