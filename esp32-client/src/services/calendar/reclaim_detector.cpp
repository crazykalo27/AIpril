/**
 * Reclaim detector implementation.
 */

#include "reclaim_detector.h"

ReclaimDetector::ReclaimDetector(const char* tag) {
    _tag = String(tag);
    _tag.toLowerCase();
}

bool ReclaimDetector::isReclaim(const CalendarEvent& event) const {
    String text = event.summary + " " + event.description;
    text.toLowerCase();
    return text.indexOf(_tag) >= 0;
}

void ReclaimDetector::tagEvents(std::vector<CalendarEvent>& events) const {
    for (auto& ev : events) {
        ev.isReclaim = isReclaim(ev);
    }
}
