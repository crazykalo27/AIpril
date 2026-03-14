/**
 * Google OAuth2 implementation.
 */

#include "google_auth.h"
#include "config/config.h"
#include <ArduinoJson.h>

GoogleAuth::GoogleAuth(NvsStore& store, HttpsClient& http)
    : _store(store), _http(http) {}

void GoogleAuth::begin() {
    _refreshToken = _store.getString("g_refresh_tk");

    #ifdef GOOGLE_REFRESH_TOKEN
    if (_refreshToken.isEmpty()) {
        _refreshToken = GOOGLE_REFRESH_TOKEN;
        _store.putString("g_refresh_tk", _refreshToken);
        Serial.println("[GoogleAuth] Loaded refresh token from secrets.h");
    }
    #endif

    if (_refreshToken.isEmpty()) {
        Serial.println("[GoogleAuth] No refresh token. Run setup script.");
    } else {
        Serial.println("[GoogleAuth] Refresh token loaded from NVS");
    }
}

String GoogleAuth::getAccessToken() {
    if (!_accessToken.isEmpty() && millis() < _expiresAt) {
        return _accessToken;
    }
    if (refreshAccessToken()) {
        return _accessToken;
    }
    return "";
}

void GoogleAuth::setRefreshToken(const String& token) {
    _refreshToken = token;
    _store.putString("g_refresh_tk", token);
    _accessToken = "";
    _expiresAt = 0;
    Serial.println("[GoogleAuth] Refresh token saved to NVS");
}

bool GoogleAuth::isAuthenticated() const {
    return !_refreshToken.isEmpty();
}

bool GoogleAuth::refreshAccessToken() {
    if (_refreshToken.isEmpty()) {
        Serial.println("[GoogleAuth] Cannot refresh — no refresh token");
        return false;
    }

    String body = String("client_id=") + GOOGLE_CLIENT_ID
        + "&client_secret=" + GOOGLE_CLIENT_SECRET
        + "&refresh_token=" + _refreshToken
        + "&grant_type=refresh_token";

    HttpResponse res = _http.postForm(GOOGLE_TOKEN_HOST, GOOGLE_TOKEN_PATH, body);

    if (!res.ok()) {
        Serial.printf("[GoogleAuth] Token refresh failed: %d\n", res.statusCode);
        return false;
    }

    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, res.body);
    if (err) {
        Serial.printf("[GoogleAuth] JSON parse error: %s\n", err.c_str());
        return false;
    }

    _accessToken = doc["access_token"].as<String>();
    int expiresIn = doc["expires_in"] | 3600;

    // Refresh 60 seconds early to avoid edge cases
    _expiresAt = millis() + ((unsigned long)(expiresIn - 60) * 1000UL);

    Serial.printf("[GoogleAuth] Access token refreshed (expires in %ds)\n", expiresIn);
    return true;
}
