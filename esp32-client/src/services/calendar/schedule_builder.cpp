/**
 * Schedule builder implementation.
 */

#include "schedule_builder.h"
#include <algorithm>

std::vector<ScheduleBlock> ScheduleBuilder::build(
    const std::vector<CalendarEvent>& events,
    time_t windowStart, time_t windowEnd)
{
    std::vector<ScheduleBlock> blocks;

    // Sort events by start time (copy since input is const)
    std::vector<CalendarEvent> sorted = events;
    std::sort(sorted.begin(), sorted.end(),
              [](const CalendarEvent& a, const CalendarEvent& b) {
                  return a.start < b.start;
              });

    time_t cursor = windowStart;

    for (const auto& ev : sorted) {
        if (ev.start > cursor) {
            ScheduleBlock b;
            b.start = cursor;
            b.end = ev.start;
            b.askUser = true;
            b.label = "free";
            blocks.push_back(b);
        }
        ScheduleBlock b;
        b.start = ev.start;
        b.end = ev.end;
        b.askUser = false;
        b.label = ev.isReclaim ? "reclaim" : "busy";
        blocks.push_back(b);
        if (ev.end > cursor) cursor = ev.end;
    }

    if (cursor < windowEnd) {
        ScheduleBlock b;
        b.start = cursor;
        b.end = windowEnd;
        b.askUser = true;
        b.label = "free";
        blocks.push_back(b);
    }

    return blocks;
}
