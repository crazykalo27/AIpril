/**
 * Wire client implementation.
 */

#include "wire_client.h"
#include <ArduinoJson.h>

void WireClient::sendLine(const String& line) {
    Serial.println(line);
}

String WireClient::readLine(unsigned long timeoutMs) {
    String buf;
    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
        while (Serial.available()) {
            char c = Serial.read();
            if (c == '\n' || c == '\r') {
                buf.trim();
                if (!buf.isEmpty()) return buf;
                buf = "";
            } else {
                buf += c;
            }
        }
        delay(5);
    }
    return "";
}

WireResponse WireClient::transcribe(const uint8_t* audioData, size_t audioLen) {
    WireResponse r = {false, "", "", "", "", ""};

    Serial.print("AUDIO ");
    Serial.println(audioLen);

    // Send raw bytes in chunks
    const size_t CHUNK = 512;
    for (size_t i = 0; i < audioLen; i += CHUNK) {
        size_t n = min(CHUNK, audioLen - i);
        Serial.write(audioData + i, n);
    }

    String line = readLine();
    if (line.isEmpty()) {
        r.error = "timeout";
        return r;
    }

    JsonDocument doc;
    if (deserializeJson(doc, line)) {
        r.error = "parse";
        return r;
    }
    r.ok = doc["ok"] | false;
    r.transcript = doc["transcript"].as<String>();
    r.error = doc["error"].as<String>();
    return r;
}

WireResponse WireClient::interpret(const String& transcript) {
    WireResponse r = {false, "", "", "", "", ""};

    JsonDocument req;
    req["cmd"] = "interpret";
    req["transcript"] = transcript;
    String body;
    serializeJson(req, body);
    sendLine(body);

    String line = readLine();
    if (line.isEmpty()) {
        r.error = "timeout";
        return r;
    }

    JsonDocument doc;
    if (deserializeJson(doc, line)) {
        r.error = "parse";
        return r;
    }
    r.ok = doc["ok"] | false;
    r.eventName = doc["event_name"].as<String>();
    r.category = doc["category"].as<String>();
    r.error = doc["error"].as<String>();
    return r;
}

WireResponse WireClient::createEvent(const String& name, const String& desc,
                                     int durationMinutes) {
    WireResponse r = {false, "", "", "", "", ""};

    JsonDocument req;
    req["cmd"] = "create_event";
    req["name"] = name;
    req["desc"] = desc;
    req["duration_minutes"] = durationMinutes;
    String body;
    serializeJson(req, body);
    sendLine(body);

    String line = readLine();
    if (line.isEmpty()) {
        r.error = "timeout";
        return r;
    }

    JsonDocument doc;
    if (deserializeJson(doc, line)) {
        r.error = "parse";
        return r;
    }
    r.ok = doc["ok"] | false;
    r.eventId = doc["event_id"].as<String>();
    r.error = doc["error"].as<String>();
    return r;
}

WireResponse WireClient::createFavorite(int durationMinutes) {
    WireResponse r = {false, "", "", "", "", ""};

    JsonDocument req;
    req["cmd"] = "create_favorite";
    req["duration_minutes"] = durationMinutes;
    String body;
    serializeJson(req, body);
    sendLine(body);

    String line = readLine();
    if (line.isEmpty()) {
        r.error = "timeout";
        return r;
    }

    JsonDocument doc;
    if (deserializeJson(doc, line)) {
        r.error = "parse";
        return r;
    }
    r.ok = doc["ok"] | false;
    r.eventId = doc["event_id"].as<String>();
    r.error = doc["error"].as<String>();
    return r;
}
