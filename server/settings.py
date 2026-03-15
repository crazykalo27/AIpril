"""Settings storage (favorites, event labels for LLM)."""
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "settings.json"

DEFAULTS = {
    "favorite_name": "Focus Work",
    "favorite_desc": "Deep focus block",
    "event_labels": [
        "Focus Work",
        "Meeting",
        "Break",
        "Personal",
        "Exercise",
        "Lunch",
    ],
}


def load() -> dict:
    """Load settings from JSON file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
                return {**DEFAULTS, **data}
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULTS.copy()


def save(data: dict) -> None:
    """Save settings to JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_interpret_prompt(labels: list[str]) -> str:
    """Build LLM prompt with event labels for matching."""
    labels_str = ", ".join(f'"{l}"' for l in labels) if labels else "work, break, personal, meeting, other"
    return (
        "You receive a transcript of someone describing what they are doing. "
        f"Match the transcript to one of these event types when possible: {labels_str}. "
        "Return ONLY valid JSON: "
        '{"event_name": "<short 3-8 word calendar title>", '
        '"category": "<work|break|personal|meeting|other>"}'
    )
