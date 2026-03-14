/**
 * Domain enumerations.
 */

#ifndef DOMAIN_ENUMS_H
#define DOMAIN_ENUMS_H

/// How the user supplied their activity input.
enum class InputSource {
    VOICE,
    REPEAT_BUTTON,
    FAVORITE_BUTTON
};

/// Whether the system should prompt the user right now.
enum class PromptState {
    SHOULD_PROMPT,
    SUPPRESSED_RECLAIM,
    SUPPRESSED_EVENT,
    WAITING,
    COOLDOWN
};

#endif
