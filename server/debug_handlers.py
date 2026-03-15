"""
Debug handlers — for testing without ESP32 hardware.

Kept separate from main handlers. Records audio from browser,
simulates ESP32 round-trip, runs STT, returns transcript.
"""

import io
import logging
from datetime import datetime

from config import OPENAI_API_KEY, OPENAI_TRANSCRIBE_MODEL
from openai import OpenAI

# Debug logger — all output prefixed and visible
log = logging.getLogger("aipril.debug")
log.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("[DEBUG] %(message)s"))
log.addHandler(_handler)


def debug_transcribe_from_file(audio_bytes: bytes, content_type: str = "") -> dict:
    """
    Transcribe audio from browser upload. Simulates ESP32 flow for testing.
    Returns {ok, transcript, error, debug_log}.
    """
    debug_log = []

    def d(msg: str) -> None:
        entry = f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} {msg}"
        debug_log.append(entry)
        log.debug(msg)

    d("=== DEBUG TRANSCRIBE START ===")
    d(f"Received audio: {len(audio_bytes)} bytes, content_type={content_type or 'unknown'}")

    if not OPENAI_API_KEY:
        d("ERROR: OPENAI_API_KEY not set")
        return {"ok": False, "error": "OPENAI_API_KEY not set", "debug_log": debug_log}

    # Simulate: send to ESP32
    d(f"Simulate: would send {len(audio_bytes)} bytes to ESP32 over serial")
    d("Simulate: ESP32 would receive and echo back (no hardware connected)")

    # Simulate: receive from ESP32 (we already have the bytes)
    d(f"Simulate: receiving {len(audio_bytes)} bytes from ESP32 (using browser audio directly)")

    # Run STT
    d("Calling OpenAI Whisper API...")
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        with io.BytesIO(audio_bytes) as f:
            f.name = "recording.webm" if "webm" in (content_type or "") else "recording.wav"
            transcript = client.audio.transcriptions.create(
                model=OPENAI_TRANSCRIBE_MODEL,
                file=f,
            )
        text = transcript.text if transcript.text else ""
        d(f"STT result: {repr(text)}")
        d("=== DEBUG TRANSCRIBE END ===")
        return {
            "ok": True,
            "transcript": text,
            "debug_log": debug_log,
        }
    except Exception as e:
        d(f"STT error: {e}")
        d("=== DEBUG TRANSCRIBE END ===")
        return {
            "ok": False,
            "error": str(e),
            "transcript": "",
            "debug_log": debug_log,
        }


def debug_full_flow(audio_bytes: bytes, content_type: str = "") -> dict:
    """
    Full flow: transcribe → interpret → create_event. For browser record when no ESP32.
    Returns {ok, transcript, event_name, event_id, error, debug_log}.
    """
    from handlers import handle_transcribe, handle_interpret, handle_create_event

    result = debug_transcribe_from_file(audio_bytes, content_type)
    if not result.get("ok"):
        return {**result, "event_name": "", "event_id": ""}

    transcript = result.get("transcript", "")
    if not transcript:
        result["debug_log"].append("Transcript empty, skipping interpret/create")
        return {**result, "event_name": "", "event_id": ""}

    interp = handle_interpret(transcript)
    event_name = interp.get("event_name", transcript[:40])
    cal = handle_create_event(event_name, transcript, 30)

    result["event_name"] = event_name
    result["event_id"] = cal.get("event_id", "")
    result["ok"] = result["ok"] and cal.get("ok", False)
    if cal.get("error"):
        result["error"] = cal["error"]
    result["debug_log"].append(f"Interpret: {event_name}")
    result["debug_log"].append(f"Calendar: {'ok' if cal.get('ok') else cal.get('error', '')}")

    return result
