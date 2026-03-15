/**
 * Schedule builder.
 *
 * Converts calendar events into simplified ScheduleBlock list
 * for the prompt scheduler.
 */

#ifndef SCHEDULE_BUILDER_H
#define SCHEDULE_BUILDER_H

#include <vector>
#include "domain/models.h"

class ScheduleBuilder {
public:
    /// Build schedule blocks for a time window from calendar events.
    /// Gaps between events become askUser=true blocks.
    std::vector<ScheduleBlock> build(const std::vector<CalendarEvent>& events,
                                     time_t windowStart, time_t windowEnd);
};

#endif
