/**
 * OpenAI transcription client (Whisper / gpt-4o-transcribe).
 *
 * Sends audio as multipart/form-data to /v1/audio/transcriptions.
 * Returns the transcript text.
 */

#ifndef OPENAI_TRANSCRIBER_H
#define OPENAI_TRANSCRIBER_H

#include <Arduino.h>
#include "infrastructure/network/https_client.h"

class OpenAITranscriber {
public:
    explicit OpenAITranscriber(HttpsClient& http);

    /// Transcribe audio data. Returns transcript or empty on failure.
    String transcribe(const uint8_t* wavData, size_t wavLen);

private:
    HttpsClient& _http;
};

#endif
