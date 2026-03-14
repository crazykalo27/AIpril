/**
 * NVS store implementation using ESP32 Preferences library.
 */

#include "nvs_store.h"
#include <Preferences.h>

static Preferences prefs;

void NvsStore::begin(const char* ns) {
    _namespace = ns;
}

bool NvsStore::putString(const char* key, const String& value) {
    prefs.begin(_namespace, false);
    bool ok = prefs.putString(key, value) > 0;
    prefs.end();
    return ok;
}

String NvsStore::getString(const char* key, const String& defaultValue) {
    prefs.begin(_namespace, true);
    String val = prefs.getString(key, defaultValue);
    prefs.end();
    return val;
}

bool NvsStore::putInt(const char* key, int32_t value) {
    prefs.begin(_namespace, false);
    bool ok = prefs.putInt(key, value) > 0;
    prefs.end();
    return ok;
}

int32_t NvsStore::getInt(const char* key, int32_t defaultValue) {
    prefs.begin(_namespace, true);
    int32_t val = prefs.getInt(key, defaultValue);
    prefs.end();
    return val;
}

bool NvsStore::remove(const char* key) {
    prefs.begin(_namespace, false);
    bool ok = prefs.remove(key);
    prefs.end();
    return ok;
}
