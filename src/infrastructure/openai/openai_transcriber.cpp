/**
 * OpenAI transcription implementation.
 *
 * Posts multipart WAV to /v1/audio/transcriptions — no base64 overhead.
 */

#include "openai_transcriber.h"
#include "config/config.h"
#include <ArduinoJson.h>

OpenAITranscriber::OpenAITranscriber(HttpsClient& http) : _http(http) {}

String OpenAITranscriber::transcribe(const uint8_t* wavData, size_t wavLen) {
    String auth = String("Bearer ") + OPENAI_API_KEY;

    HttpResponse res = _http.postMultipartAudio(
        OPENAI_HOST, OPENAI_TRANSCRIBE_PATH,
        auth.c_str(),
        "file", "recording.wav",
        wavData, wavLen,
        OPENAI_TRANSCRIBE_MODEL
    );

    if (!res.ok()) {
        Serial.printf("[Transcriber] Failed: %d\n", res.statusCode);
        Serial.println(res.body);
        return "";
    }

    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, res.body);
    if (err) {
        Serial.printf("[Transcriber] JSON error: %s\n", err.c_str());
        return "";
    }

    String text = doc["text"] | "";
    Serial.printf("[Transcriber] Transcript: %s\n", text.c_str());
    return text;
}
