/**
 * Time utilities implementation.
 */

#include "time_utils.h"

String formatRfc3339(time_t t) {
    struct tm tm;
    gmtime_r(&t, &tm);
    char buf[32];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tm);
    return String(buf);
}

time_t parseRfc3339(const char* str) {
    struct tm tm = {};
    // Handles "2026-03-14T12:00:00Z" and "2026-03-14T12:00:00+00:00"
    if (sscanf(str, "%d-%d-%dT%d:%d:%d",
               &tm.tm_year, &tm.tm_mon, &tm.tm_mday,
               &tm.tm_hour, &tm.tm_min, &tm.tm_sec) < 6) {
        return 0;
    }
    tm.tm_year -= 1900;
    tm.tm_mon  -= 1;
    return mktime(&tm);
}

void syncNtp(const char* server, long gmtOffset, int daylightOffset) {
    configTime(gmtOffset, daylightOffset, server);
    Serial.print("[NTP] Syncing...");
    struct tm timeInfo;
    int retries = 0;
    while (!getLocalTime(&timeInfo) && retries < 10) {
        delay(500);
        Serial.print(".");
        retries++;
    }
    if (retries < 10) {
        Serial.println(" OK");
        Serial.println(formatRfc3339(mktime(&timeInfo)));
    } else {
        Serial.println(" FAILED");
    }
}

time_t nowUtc() {
    time_t now;
    time(&now);
    return now;
}
