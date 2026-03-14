/**
 * OpenAI event-name interpreter.
 *
 * Takes a transcript and asks GPT for a short calendar event name.
 * Second call in the two-call flow (transcribe → interpret).
 */

#ifndef OPENAI_INTERPRETER_H
#define OPENAI_INTERPRETER_H

#include <Arduino.h>
#include "domain/models.h"
#include "infrastructure/network/https_client.h"

class OpenAIInterpreter {
public:
    explicit OpenAIInterpreter(HttpsClient& http);

    /// Extract a structured activity from a transcript.
    InterpretedActivity interpret(const String& transcript);

private:
    HttpsClient& _http;
};

#endif
