/**
 * Lightweight JSON helpers.
 *
 * Thin wrappers over ArduinoJson for common patterns.
 */

#ifndef JSON_HELPERS_H
#define JSON_HELPERS_H

#include <ArduinoJson.h>

/// Quick-serialize a document to a String.
inline String jsonToString(const JsonDocument& doc) {
    String out;
    serializeJson(doc, out);
    return out;
}

#endif
