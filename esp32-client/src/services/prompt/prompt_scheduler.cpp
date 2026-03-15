/**
 * Prompt scheduler implementation.
 */

#include "prompt_scheduler.h"

PromptScheduler::PromptScheduler(unsigned long intervalMs)
    : _intervalMs(intervalMs), _lastPrompt(millis()) {}

bool PromptScheduler::shouldPrompt() {
    if (_suppressed) return false;
    return (millis() - _lastPrompt) >= _intervalMs;
}

void PromptScheduler::reset() {
    _lastPrompt = millis();
}

void PromptScheduler::suppress() {
    _suppressed = true;
}

void PromptScheduler::resume() {
    _suppressed = false;
    _lastPrompt = millis();
}

void PromptScheduler::setInterval(unsigned long ms) {
    _intervalMs = ms;
}
