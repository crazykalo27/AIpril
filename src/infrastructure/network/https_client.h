/**
 * Shared HTTPS client wrapper.
 *
 * Provides typed methods for JSON POST, multipart POST, form POST, and GET
 * over TLS. All external API calls go through this.
 */

#ifndef HTTPS_CLIENT_H
#define HTTPS_CLIENT_H

#include <Arduino.h>

struct HttpResponse {
    int    statusCode;
    String body;
    bool   ok() const { return statusCode >= 200 && statusCode < 300; }
};

class HttpsClient {
public:
    /// POST with JSON body. Returns parsed response.
    HttpResponse postJson(const char* host, const char* path,
                          const char* authHeader, const String& jsonBody);

    /// POST multipart/form-data with one binary file field + text fields.
    /// Streams audio data to avoid double-buffering.
    HttpResponse postMultipartAudio(const char* host, const char* path,
                                    const char* authHeader,
                                    const char* fieldName, const char* filename,
                                    const uint8_t* audioData, size_t audioLen,
                                    const char* modelName);

    /// POST application/x-www-form-urlencoded (for OAuth token refresh).
    HttpResponse postForm(const char* host, const char* path,
                          const String& formBody);

    /// GET with auth header.
    HttpResponse get(const char* host, const char* path,
                     const char* authHeader);

private:
    HttpResponse readResponse(WiFiClientSecure& client);
};

#endif
