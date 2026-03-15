"""API handlers called by the serial bridge."""
import base64
import json
from datetime import datetime, timedelta
from io import BytesIO

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_TRANSCRIBE_MODEL,
    OPENAI_CHAT_MODEL,
)
from google_auth import get_credentials, create_calendar_event, list_calendar_events
from config import CREDENTIALS_FILE, TOKEN_FILE
from settings import load, get_interpret_prompt


def handle_transcribe(audio_b64: str) -> dict:
    """Transcribe base64 WAV via OpenAI Whisper."""
    if not OPENAI_API_KEY:
        return {"ok": False, "error": "OPENAI_API_KEY not set"}

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        return {"ok": False, "error": f"base64 decode: {e}"}

    client = OpenAI(api_key=OPENAI_API_KEY)
    with BytesIO(audio_bytes) as f:
        f.name = "recording.wav"
        transcript = client.audio.transcriptions.create(
            model=OPENAI_TRANSCRIBE_MODEL,
            file=f,
        )
    text = transcript.text if transcript.text else ""
    return {"ok": True, "transcript": text}


def handle_interpret(transcript: str) -> dict:
    """Extract event name from transcript via GPT. Uses event_labels from settings."""
    if not OPENAI_API_KEY:
        return {"ok": False, "error": "OPENAI_API_KEY not set"}

    settings = load()
    prompt = get_interpret_prompt(settings.get("event_labels", []))

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return {
            "ok": True,
            "event_name": data.get("event_name", "Untitled"),
            "category": data.get("category", "other"),
        }
    except json.JSONDecodeError:
        return {"ok": True, "event_name": transcript[:40], "category": "other"}


def handle_create_event(name: str, desc: str, duration_minutes: int = 30) -> dict:
    """Create Google Calendar event. Uses server time."""
    creds = get_credentials(CREDENTIALS_FILE, TOKEN_FILE)
    if not creds:
        return {"ok": False, "error": "Google not authenticated. Run tools/google_auth_setup.py"}

    now = datetime.utcnow()
    start_dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_dt = (now + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    event_id = create_calendar_event(creds, name, desc, start_dt, end_dt)
    if event_id:
        return {"ok": True, "event_id": event_id}
    return {"ok": False, "error": "Calendar API failed"}


def handle_create_favorite(duration_minutes: int = 30) -> dict:
    """Create calendar event using favorite from settings."""
    settings = load()
    name = settings.get("favorite_name", "Focus Work")
    desc = settings.get("favorite_desc", "Deep focus block")
    return handle_create_event(name, desc, duration_minutes)


def handle_list_events(days_ahead: int = 7) -> dict:
    """List upcoming calendar events. Returns events in next N days."""
    creds = get_credentials(CREDENTIALS_FILE, TOKEN_FILE)
    if not creds:
        return {"ok": False, "error": "Google not authenticated. Run tools/google_auth_setup.py"}

    now = datetime.utcnow()
    time_min = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    time_max = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%dT%H:%M:%SZ")

    events = list_calendar_events(creds, time_min, time_max)
    return {"ok": True, "events": events}
