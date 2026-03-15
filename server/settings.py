"""Settings storage (favorites, event labels for LLM)."""
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "settings.json"

DEFAULTS = {
    "favorite_name": "Focus Work",
    "favorite_desc": "Deep focus block",
    "event_duration": 30,
    "event_labels": [
        "Work",
        "School",
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
    labels_str = ", ".join(f'"{l}"' for l in labels) if labels else "work, school"
    return (
        "You receive a transcript of someone describing what they are doing. "
        f"You MUST use one of these labels if the transcript matches: {labels_str}. "
        "Only invent a new short name if NONE of those labels fit at all. "
        "Return ONLY valid JSON: "
        '{"event_name": "<label or short name>", '
        '"category": "<work|break|personal|meeting|other>"}'
    )
