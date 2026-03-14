/**
 * Google Calendar API implementation.
 */

#include "google_calendar.h"
#include "config/config.h"
#include "utils/time_utils.h"
#include <ArduinoJson.h>

GoogleCalendar::GoogleCalendar(GoogleAuth& auth, HttpsClient& http)
    : _auth(auth), _http(http) {}

String GoogleCalendar::buildAuthHeader() {
    String token = _auth.getAccessToken();
    if (token.isEmpty()) return "";
    return String("Bearer ") + token;
}

String GoogleCalendar::createEvent(const String& summary,
                                   const String& description,
                                   time_t start, time_t end)
{
    String auth = buildAuthHeader();
    if (auth.isEmpty()) {
        Serial.println("[Calendar] Not authenticated");
        return "";
    }

    JsonDocument doc;
    doc["summary"]     = summary;
    doc["description"] = description;

    JsonObject startObj = doc["start"].to<JsonObject>();
    startObj["dateTime"] = formatRfc3339(start);
    startObj["timeZone"] = "UTC";

    JsonObject endObj = doc["end"].to<JsonObject>();
    endObj["dateTime"] = formatRfc3339(end);
    endObj["timeZone"] = "UTC";

    String body;
    serializeJson(doc, body);

    HttpResponse res = _http.postJson(
        GOOGLE_CALENDAR_HOST, GOOGLE_CALENDAR_BASE,
        auth.c_str(), body
    );

    if (!res.ok()) {
        Serial.printf("[Calendar] Create event failed: %d\n", res.statusCode);
        return "";
    }

    JsonDocument resDoc;
    deserializeJson(resDoc, res.body);
    String eventId = resDoc["id"] | "";
    Serial.printf("[Calendar] Created event: %s\n", eventId.c_str());
    return eventId;
}

std::vector<CalendarEvent> GoogleCalendar::listEvents(time_t timeMin,
                                                       time_t timeMax)
{
    std::vector<CalendarEvent> events;
    String auth = buildAuthHeader();
    if (auth.isEmpty()) return events;

    String path = String(GOOGLE_CALENDAR_BASE)
        + "?singleEvents=true&orderBy=startTime"
        + "&timeMin=" + formatRfc3339(timeMin)
        + "&timeMax=" + formatRfc3339(timeMax);

    HttpResponse res = _http.get(GOOGLE_CALENDAR_HOST, path.c_str(), auth.c_str());

    if (!res.ok()) {
        Serial.printf("[Calendar] List events failed: %d\n", res.statusCode);
        return events;
    }

    JsonDocument doc;
    deserializeJson(doc, res.body);
    JsonArray items = doc["items"].as<JsonArray>();

    for (JsonObject item : items) {
        CalendarEvent ev;
        ev.eventId     = item["id"] | "";
        ev.summary     = item["summary"] | "";
        ev.description = item["description"] | "";

        const char* dtStart = item["start"]["dateTime"] | "";
        const char* dtEnd   = item["end"]["dateTime"]   | "";
        ev.start = parseRfc3339(dtStart);
        ev.end   = parseRfc3339(dtEnd);
        ev.isAllDay = item["start"].containsKey("date");

        events.push_back(ev);
    }

    Serial.printf("[Calendar] Listed %d events\n", events.size());
    return events;
}
