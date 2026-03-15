/**
 * HTTP client implementation using ESP32 WiFi + HTTPClient.
 */

#include "http_client.h"
#include <HTTPClient.h>
#include <ArduinoJson.h>

void HttpClient::begin(const char* serverUrl) {
    _serverUrl = serverUrl;
    if (_serverUrl.endsWith("/")) {
        _serverUrl.remove(_serverUrl.length() - 1);
    }
    Serial.printf("[HTTP] Server: %s\n", _serverUrl.c_str());

    // Register with server so it knows our IP
    HTTPClient http;
    String url = _serverUrl + "/api/esp32/register";
    if (http.begin(url)) {
        http.addHeader("Content-Type", "application/json");
        http.setTimeout(5000);
        int code = http.POST("{}");
        Serial.printf("[HTTP] Register: %d\n", code);
        http.end();
    }
}

HttpResponse HttpClient::postAudio(const uint8_t* data, size_t len) {
    HttpResponse r = {false, "", "", "", "", ""};

    HTTPClient http;
    String url = _serverUrl + "/api/esp32/record";
    Serial.printf("[HTTP] POST %s (%u bytes)\n", url.c_str(), (unsigned)len);

    if (!http.begin(url)) {
        r.error = "HTTP begin failed";
        return r;
    }

    http.addHeader("Content-Type", "audio/wav");
    http.setTimeout(30000);
    int code = http.POST(const_cast<uint8_t*>(data), len);

    if (code <= 0) {
        r.error = "HTTP error: " + String(http.errorToString(code));
        Serial.printf("[HTTP] Error: %s\n", r.error.c_str());
        http.end();
        return r;
    }

    String body = http.getString();
    http.end();
    Serial.printf("[HTTP] %d: %s\n", code, body.substring(0, 120).c_str());

    if (code != 200) {
        r.error = "HTTP " + String(code);
        return r;
    }

    return parseJson(body);
}

HttpResponse HttpClient::postRepeat() {
    HttpResponse r = {false, "", "", "", "", ""};

    HTTPClient http;
    String url = _serverUrl + "/api/trigger/repeat";
    Serial.printf("[HTTP] POST %s\n", url.c_str());

    if (!http.begin(url)) {
        r.error = "HTTP begin failed";
        return r;
    }

    http.addHeader("Content-Type", "application/json");
    http.setTimeout(15000);
    int code = http.POST("{}");

    if (code <= 0) {
        r.error = "HTTP error: " + String(http.errorToString(code));
        http.end();
        return r;
    }

    String body = http.getString();
    http.end();
    Serial.printf("[HTTP] %d: %s\n", code, body.substring(0, 120).c_str());

    return parseJson(body);
}

HttpResponse HttpClient::postFavorite() {
    HttpResponse r = {false, "", "", "", "", ""};

    HTTPClient http;
    String url = _serverUrl + "/api/trigger/favorite";
    Serial.printf("[HTTP] POST %s\n", url.c_str());

    if (!http.begin(url)) {
        r.error = "HTTP begin failed";
        return r;
    }

    http.addHeader("Content-Type", "application/json");
    http.setTimeout(15000);
    int code = http.POST("{}");

    if (code <= 0) {
        r.error = "HTTP error: " + String(http.errorToString(code));
        http.end();
        return r;
    }

    String body = http.getString();
    http.end();
    Serial.printf("[HTTP] %d: %s\n", code, body.substring(0, 120).c_str());

    return parseJson(body);
}

HttpResponse HttpClient::parseJson(const String& body) {
    HttpResponse r = {false, "", "", "", "", ""};

    JsonDocument doc;
    if (deserializeJson(doc, body)) {
        r.error = "JSON parse failed";
        return r;
    }

    r.ok        = doc["ok"] | false;
    r.transcript = doc["transcript"].as<String>();
    r.eventName  = doc["event_name"].as<String>();
    r.category   = doc["category"].as<String>();
    r.eventId    = doc["event_id"].as<String>();
    r.error      = doc["error"].as<String>();
    return r;
}
