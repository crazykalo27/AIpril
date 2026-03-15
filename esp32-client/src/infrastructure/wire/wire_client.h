/**
 * Wire client — serial communication with host server.
 *
 * ESP32 sends commands over Serial (USB). Server runs on host PC,
 * executes API calls (OpenAI, Google Calendar), returns JSON responses.
 */

#ifndef WIRE_CLIENT_H
#define WIRE_CLIENT_H

#include <Arduino.h>

struct WireResponse {
    bool ok;
    String transcript;
    String eventName;
    String category;
    String eventId;
    String error;
};

class WireClient {
public:
    /// Send raw audio for transcription. Uses "AUDIO len\n" + bytes.
    WireResponse transcribe(const uint8_t* audioData, size_t audioLen);

    /// Send transcript for interpretation (event name extraction).
    WireResponse interpret(const String& transcript);

    /// Request calendar event creation. Server uses its time; duration_minutes defaults to 30.
    WireResponse createEvent(const String& name, const String& desc,
                             int durationMinutes = 30);

    /// Create event using favorite from server settings (configured in web UI).
    WireResponse createFavorite(int durationMinutes = 30);

private:
    void sendLine(const String& line);
    String readLine(unsigned long timeoutMs = 30000);
};

#endif
