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
            blocks.push_back({cursor, ev.start, true, "free"});
        }
        blocks.push_back({
            ev.start, ev.end, false,
            ev.isReclaim ? "reclaim" : "busy"
        });
        if (ev.end > cursor) cursor = ev.end;
    }

    if (cursor < windowEnd) {
        blocks.push_back({cursor, windowEnd, true, "free"});
    }

    return blocks;
}
