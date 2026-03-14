/**
 * OpenAI interpreter implementation.
 *
 * Sends transcript to GPT chat completions with JSON response format.
 */

#include "openai_interpreter.h"
#include "config/config.h"
#include <ArduinoJson.h>

static const char* INTERPRET_PROMPT =
    "You receive a transcript of someone describing what they are doing. "
    "Return ONLY valid JSON: "
    "{\"event_name\": \"<short 3-8 word calendar title>\", "
    "\"category\": \"<work|break|personal|meeting|other>\"}";

OpenAIInterpreter::OpenAIInterpreter(HttpsClient& http) : _http(http) {}

InterpretedActivity OpenAIInterpreter::interpret(const String& transcript) {
    InterpretedActivity result;
    result.transcript = transcript;
    result.source = InputSource::VOICE;

    String auth = String("Bearer ") + OPENAI_API_KEY;

    // Build request JSON
    JsonDocument req;
    req["model"] = OPENAI_CHAT_MODEL;

    JsonObject fmt = req["response_format"].to<JsonObject>();
    fmt["type"] = "json_object";

    JsonArray messages = req["messages"].to<JsonArray>();

    JsonObject sysMsg = messages.add<JsonObject>();
    sysMsg["role"]    = "system";
    sysMsg["content"] = INTERPRET_PROMPT;

    JsonObject userMsg = messages.add<JsonObject>();
    userMsg["role"]    = "user";
    userMsg["content"] = transcript;

    String body;
    serializeJson(req, body);

    HttpResponse res = _http.postJson(OPENAI_HOST, OPENAI_CHAT_PATH,
                                      auth.c_str(), body);

    if (!res.ok()) {
        Serial.printf("[Interpreter] Failed: %d\n", res.statusCode);
        result.eventName = transcript.substring(0, 40);
        return result;
    }

    JsonDocument resDoc;
    deserializeJson(resDoc, res.body);

    String content = resDoc["choices"][0]["message"]["content"] | "";

    // Parse the inner JSON from the model's response
    JsonDocument inner;
    DeserializationError err = deserializeJson(inner, content);
    if (err) {
        Serial.printf("[Interpreter] Inner JSON error: %s\n", err.c_str());
        result.eventName = transcript.substring(0, 40);
        return result;
    }

    result.eventName = inner["event_name"] | "Untitled";
    result.category  = inner["category"]   | "other";

    Serial.printf("[Interpreter] Event: %s (%s)\n",
                  result.eventName.c_str(), result.category.c_str());
    return result;
}
