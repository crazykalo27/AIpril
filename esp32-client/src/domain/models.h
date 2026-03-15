/**
 * Domain data models.
 *
 * Plain structs for passing data between services.
 * No external dependencies — pure domain layer.
 */

#ifndef DOMAIN_MODELS_H
#define DOMAIN_MODELS_H

#include <Arduino.h>
#include "enums.h"

/// A Google Calendar event (internal representation).
struct CalendarEvent {
    String eventId;
    String summary;
    String description;
    time_t start;
    time_t end;
    bool isAllDay   = false;
    bool isReclaim  = false;
};

/// Metadata for one voice recording.
struct VoiceRecord {
    String  recordId;
    time_t  timestamp = 0;
    String  transcript;
    float   durationSec = 0.0f;
};

/// Result of AI interpretation of a transcript.
struct InterpretedActivity {
    String      eventName;
    String      transcript;
    String      category;
    InputSource source = InputSource::VOICE;
};

/// A compact time block for prompt scheduling.
struct ScheduleBlock {
    time_t start;
    time_t end;
    bool   askUser = true;
    String label;
};

/// A saved favorite activity.
struct FavoriteActivity {
    String id;
    String label;
    String summary;
    String category;
};

#endif
