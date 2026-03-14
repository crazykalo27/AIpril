/**
 * HTTPS client implementation.
 */

#include "https_client.h"
#include <WiFiClientSecure.h>

// ---------------------------------------------------------------------------
// POST JSON
// ---------------------------------------------------------------------------
HttpResponse HttpsClient::postJson(const char* host, const char* path,
                                   const char* authHeader,
                                   const String& jsonBody)
{
    WiFiClientSecure client;
    client.setInsecure();  // TODO: add root CA certs for production

    if (!client.connect(host, 443, 10000)) {
        Serial.printf("[HTTPS] connect failed: %s\n", host);
        return {-1, ""};
    }

    client.printf("POST %s HTTP/1.1\r\n", path);
    client.printf("Host: %s\r\n", host);
    client.printf("Authorization: %s\r\n", authHeader);
    client.print ("Content-Type: application/json\r\n");
    client.printf("Content-Length: %d\r\n", jsonBody.length());
    client.print ("Connection: close\r\n\r\n");
    client.print (jsonBody);

    return readResponse(client);
}

// ---------------------------------------------------------------------------
// POST multipart audio — streams binary data without base64
// ---------------------------------------------------------------------------
HttpResponse HttpsClient::postMultipartAudio(
    const char* host, const char* path, const char* authHeader,
    const char* fieldName, const char* filename,
    const uint8_t* audioData, size_t audioLen, const char* modelName)
{
    WiFiClientSecure client;
    client.setInsecure();

    if (!client.connect(host, 443, 10000)) {
        Serial.printf("[HTTPS] connect failed: %s\n", host);
        return {-1, ""};
    }

    const char* boundary = "----AIprilBoundary";

    // Build multipart parts (excluding binary) to calculate total length
    String partFile = String("--") + boundary + "\r\n"
        "Content-Disposition: form-data; name=\"" + fieldName + "\"; "
        "filename=\"" + filename + "\"\r\n"
        "Content-Type: audio/wav\r\n\r\n";

    String partModel = String("\r\n--") + boundary + "\r\n"
        "Content-Disposition: form-data; name=\"model\"\r\n\r\n"
        + modelName + "\r\n";

    String partEnd = String("--") + boundary + "--\r\n";

    size_t totalLen = partFile.length() + audioLen + partModel.length() + partEnd.length();

    client.printf("POST %s HTTP/1.1\r\n", path);
    client.printf("Host: %s\r\n", host);
    client.printf("Authorization: %s\r\n", authHeader);
    client.printf("Content-Type: multipart/form-data; boundary=%s\r\n", boundary);
    client.printf("Content-Length: %d\r\n", totalLen);
    client.print ("Connection: close\r\n\r\n");

    // Stream the parts
    client.print(partFile);

    // Write audio in chunks to avoid watchdog timeout
    const size_t CHUNK = 4096;
    for (size_t offset = 0; offset < audioLen; offset += CHUNK) {
        size_t toWrite = min(CHUNK, audioLen - offset);
        client.write(audioData + offset, toWrite);
    }

    client.print(partModel);
    client.print(partEnd);

    return readResponse(client);
}

// ---------------------------------------------------------------------------
// POST form-urlencoded (OAuth token refresh)
// ---------------------------------------------------------------------------
HttpResponse HttpsClient::postForm(const char* host, const char* path,
                                   const String& formBody)
{
    WiFiClientSecure client;
    client.setInsecure();

    if (!client.connect(host, 443, 10000)) {
        return {-1, ""};
    }

    client.printf("POST %s HTTP/1.1\r\n", path);
    client.printf("Host: %s\r\n", host);
    client.print ("Content-Type: application/x-www-form-urlencoded\r\n");
    client.printf("Content-Length: %d\r\n", formBody.length());
    client.print ("Connection: close\r\n\r\n");
    client.print (formBody);

    return readResponse(client);
}

// ---------------------------------------------------------------------------
// GET
// ---------------------------------------------------------------------------
HttpResponse HttpsClient::get(const char* host, const char* path,
                              const char* authHeader)
{
    WiFiClientSecure client;
    client.setInsecure();

    if (!client.connect(host, 443, 10000)) {
        return {-1, ""};
    }

    client.printf("GET %s HTTP/1.1\r\n", path);
    client.printf("Host: %s\r\n", host);
    client.printf("Authorization: %s\r\n", authHeader);
    client.print ("Connection: close\r\n\r\n");

    return readResponse(client);
}

// ---------------------------------------------------------------------------
// Read HTTP response (status + body, skip headers)
// ---------------------------------------------------------------------------
HttpResponse HttpsClient::readResponse(WiFiClientSecure& client)
{
    unsigned long deadline = millis() + 15000;
    while (client.available() == 0) {
        if (millis() > deadline) {
            client.stop();
            Serial.println("[HTTPS] response timeout");
            return {-1, ""};
        }
        delay(10);
    }

    // Read status line
    String statusLine = client.readStringUntil('\n');
    int code = 0;
    int sp1 = statusLine.indexOf(' ');
    if (sp1 > 0) {
        code = statusLine.substring(sp1 + 1, sp1 + 4).toInt();
    }

    // Skip headers
    while (client.connected()) {
        String line = client.readStringUntil('\n');
        if (line == "\r" || line.length() == 0) break;
    }

    // Read body
    String body;
    while (client.available()) {
        body += (char)client.read();
    }
    client.stop();

    return {code, body};
}
