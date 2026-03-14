/**
 * Google Calendar API client.
 *
 * Create events, list events, check for reclaim tags.
 * All HTTP is delegated to HttpsClient; auth to GoogleAuth.
 */

#ifndef GOOGLE_CALENDAR_H
#define GOOGLE_CALENDAR_H

#include <Arduino.h>
#include <vector>
#include "domain/models.h"
#include "infrastructure/google/google_auth.h"
#include "infrastructure/network/https_client.h"

class GoogleCalendar {
public:
    GoogleCalendar(GoogleAuth& auth, HttpsClient& http);

    /// Create a calendar event. Returns the event ID or empty on failure.
    String createEvent(const String& summary, const String& description,
                       time_t start, time_t end);

    /// List events in a time range.
    std::vector<CalendarEvent> listEvents(time_t timeMin, time_t timeMax);

private:
    String buildAuthHeader();

    GoogleAuth&  _auth;
    HttpsClient& _http;
};

#endif
