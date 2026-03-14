/**
 * Time formatting and parsing utilities.
 */

#ifndef TIME_UTILS_H
#define TIME_UTILS_H

#include <Arduino.h>
#include <time.h>

/// Format a time_t as RFC3339 UTC string: "2026-03-14T12:00:00Z"
String formatRfc3339(time_t t);

/// Parse an RFC3339 string back to time_t. Returns 0 on failure.
time_t parseRfc3339(const char* str);

/// Sync system clock via NTP. Call once after WiFi connects.
void syncNtp(const char* server, long gmtOffset, int daylightOffset);

/// Return current time as time_t.
time_t nowUtc();

#endif
