/**
 * Reclaim tag detection.
 *
 * Checks calendar event summary/description for the reclaim marker.
 * Events tagged as reclaim suppress user prompts.
 */

#ifndef RECLAIM_DETECTOR_H
#define RECLAIM_DETECTOR_H

#include <Arduino.h>
#include <vector>
#include "domain/models.h"

class ReclaimDetector {
public:
    explicit ReclaimDetector(const char* tag = "[reclaim]");

    /// Check a single event for the reclaim tag (case-insensitive).
    bool isReclaim(const CalendarEvent& event) const;

    /// Set isReclaim flag on every event in the vector.
    void tagEvents(std::vector<CalendarEvent>& events) const;

private:
    String _tag;
};

#endif
