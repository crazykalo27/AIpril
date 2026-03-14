/**
 * Interval-based prompt scheduler.
 *
 * Tracks elapsed time and decides when to prompt the user.
 * Can be suppressed by calendar events or reclaim blocks.
 */

#ifndef PROMPT_SCHEDULER_H
#define PROMPT_SCHEDULER_H

#include <Arduino.h>
#include "domain/enums.h"

class PromptScheduler {
public:
    explicit PromptScheduler(unsigned long intervalMs);

    /// Check whether a prompt is due. Non-blocking.
    bool shouldPrompt();

    /// Call after a prompt was issued (resets the timer).
    void reset();

    /// Temporarily suppress prompting (e.g. during a reclaim block).
    void suppress();

    /// Resume normal scheduling.
    void resume();

    /// Change the interval at runtime.
    void setInterval(unsigned long ms);

private:
    unsigned long _intervalMs;
    unsigned long _lastPrompt = 0;
    bool          _suppressed = false;
};

#endif
