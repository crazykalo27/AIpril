/**
 * NVS (Non-Volatile Storage) wrapper.
 *
 * Persists key-value pairs across reboots. Used for:
 *   - Google OAuth refresh token
 *   - Favorite activities
 *   - Last activity (for repeat)
 *   - Runtime settings overrides
 */

#ifndef NVS_STORE_H
#define NVS_STORE_H

#include <Arduino.h>

class NvsStore {
public:
    void begin(const char* ns);

    bool putString(const char* key, const String& value);
    String getString(const char* key, const String& defaultValue = "");

    bool putInt(const char* key, int32_t value);
    int32_t getInt(const char* key, int32_t defaultValue = 0);

    bool remove(const char* key);

private:
    const char* _namespace = nullptr;
};

#endif
