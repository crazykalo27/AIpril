/**
 * Google OAuth2 token manager.
 *
 * Stores a refresh token in NVS. Uses it to obtain short-lived
 * access tokens for Calendar API calls. Handles automatic refresh.
 *
 * Initial refresh token comes from tools/google_auth_setup.py
 * and is stored via serial command or compiled in secrets.h.
 */

#ifndef GOOGLE_AUTH_H
#define GOOGLE_AUTH_H

#include <Arduino.h>
#include "infrastructure/storage/nvs_store.h"
#include "infrastructure/network/https_client.h"

class GoogleAuth {
public:
    GoogleAuth(NvsStore& store, HttpsClient& http);

    /// Load refresh token from NVS (call once in setup).
    void begin();

    /// Returns a valid Bearer access token, refreshing if needed.
    /// Returns empty string on failure.
    String getAccessToken();

    /// Store a new refresh token (from setup script via serial).
    void setRefreshToken(const String& token);

    bool isAuthenticated() const;

private:
    bool refreshAccessToken();

    NvsStore&    _store;
    HttpsClient& _http;
    String       _refreshToken;
    String       _accessToken;
    unsigned long _expiresAt = 0;  // millis() timestamp
};

#endif
