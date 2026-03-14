"""
Enumeration of possible prompt states.

Describes whether the system should prompt, suppress, or is waiting.
"""

from enum import Enum


class PromptState(Enum):
    """Current state of the prompting system."""

    SHOULD_PROMPT = "should_prompt"
    SUPPRESSED_RECLAIM = "suppressed_reclaim"
    SUPPRESSED_EVENT = "suppressed_event"
    WAITING = "waiting"
    COOLDOWN = "cooldown"
