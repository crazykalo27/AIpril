"""
AIpril server — web UI + serial bridge.

Web UI at http://localhost:5000 for settings and audio echo testing.
Google Calendar OAuth must be completed before features are usable.
Serial listener runs in background for ESP32 (use --no-serial to skip).
"""

import base64
import json
import sys
import threading
import time

import serial
from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for

from config import SERIAL_PORT, SERIAL_BAUD, CREDENTIALS_FILE, TOKEN_FILE
from handlers import (
    handle_transcribe,
    handle_transcribe_bytes,
    handle_interpret,
    handle_create_event,
    handle_create_favorite,
    handle_list_events,
    handle_current_events,
    handle_today_events,
)
from google_auth import is_authenticated, get_auth_url, handle_auth_callback
from settings import load, save, get_interpret_prompt, DEFAULTS
from debug_handlers import debug_transcribe_from_file, debug_full_flow

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

_ser: serial.Serial | None = None
_ser_lock = threading.Lock()

_last_activity: dict | None = None

# ESP32 WiFi tracking — updated when ESP32 hits /api/esp32/record or /api/esp32/register
_esp32_wifi_ip: str | None = None
_esp32_wifi_last_seen: float = 0

# Browser audio storage (no serial echo needed)
_echo_audio: bytes = b""
_echo_mime: str = "audio/webm"

# Serial ping (legacy, kept for debug)
_expecting_pong = False
_pong_event = threading.Event()
_expecting_echo = False
_echo_event = threading.Event()

# Debug log buffer (last 100 entries) — source: browser|esp32_wifi|serial
_debug_log: list[str] = []
_DEBUG_LOG_MAX = 100


def _debug(msg: str, source: str = "server") -> None:
    """Append to server debug log and print to console."""
    global _debug_log
    entry = f"[{source}] {msg}"
    print(entry)
    _debug_log.append(entry)
    if len(_debug_log) > _DEBUG_LOG_MAX:
        _debug_log.pop(0)


# ---------------------------------------------------------------------------
# Serial helpers (debug only)
# ---------------------------------------------------------------------------


def send_line(text: str) -> bool:
    with _ser_lock:
        if not _ser or not _ser.is_open:
            return False
        _ser.write((text + "\n").encode("utf-8"))
        _ser.flush()
    return True


def _update_esp32_wifi(ip: str) -> None:
    global _esp32_wifi_ip, _esp32_wifi_last_seen
    _esp32_wifi_ip = ip
    _esp32_wifi_last_seen = time.time()


# ---------------------------------------------------------------------------
# Serial protocol handlers
# ---------------------------------------------------------------------------


def handle_esp32_repeat() -> None:
    """ESP32 pressed the repeat button — run server-side repeat logic (serial or WiFi)."""
    if not _last_activity:
        _debug("Repeat (serial): no previous activity", "serial")
        return
    _debug(f"Repeat (serial): re-creating \"{_last_activity['event_name']}\"", "serial")
    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    try:
        result = handle_create_event(
            _last_activity["event_name"],
            _last_activity["transcript"],
            dur,
        )
        if result.get("ok"):
            _debug(f"Repeat (serial): created event {result.get('event_id', '')}", "serial")
        else:
            _debug(f"Repeat (serial): error {result.get('error', '')}", "serial")
    except Exception as e:
        _debug(f"Repeat (serial): exception {e}", "serial")


def send_response(ser: serial.Serial, obj: dict) -> None:
    ser.write((json.dumps(obj) + "\n").encode("utf-8"))


def process_audio_binary(ser: serial.Serial, line: str) -> None:
    global _expecting_echo, _echo_audio, _last_activity

    parts = line.split()
    if len(parts) != 2 or parts[0] != "AUDIO":
        send_response(ser, {"cmd": "transcribe", "ok": False, "error": "bad AUDIO header"})
        return

    try:
        length = int(parts[1])
    except ValueError:
        send_response(ser, {"cmd": "transcribe", "ok": False, "error": "bad length"})
        return

    audio = b""
    while len(audio) < length:
        chunk = ser.read(min(length - len(audio), 4096))
        if not chunk:
            time.sleep(0.01)
            continue
        audio += chunk

    if _expecting_echo:
        _expecting_echo = False
        _echo_audio = audio
        _echo_event.set()
        print(f"[Echo] Received {len(audio)} bytes back from ESP32")
        return

    audio_b64 = base64.b64encode(audio).decode("ascii")
    resp = {**{"cmd": "transcribe"}, **handle_transcribe(audio_b64)}
    send_response(ser, resp)


def process_command(ser: serial.Serial, cmd: dict) -> None:
    c = cmd.get("cmd", "")
    _debug(f"Serial: command {c} (USB)", "serial")
    resp: dict = {"cmd": c, "ok": False}
    try:
        if c == "transcribe":
            audio_b64 = cmd.get("audio_b64", "")
            if not audio_b64:
                resp["error"] = "missing audio_b64"
            else:
                resp = {**resp, **handle_transcribe(audio_b64)}
        elif c == "interpret":
            transcript = cmd.get("transcript", "")
            if not transcript:
                resp["error"] = "missing transcript"
            else:
                resp = {**resp, **handle_interpret(transcript)}
        elif c == "create_event":
            name = cmd.get("name", "")
            if not name:
                resp["error"] = "missing name"
            else:
                desc = cmd.get("desc", "")
                dur = int(cmd.get("duration_minutes", 30))
                resp = {**resp, **handle_create_event(name, desc, dur)}
                if resp.get("ok"):
                    global _last_activity
                    _last_activity = {"event_name": name, "transcript": desc}
        elif c == "list_events":
            resp = {**resp, **handle_list_events()}
        elif c == "create_favorite":
            dur = int(cmd.get("duration_minutes", 30))
            resp = {**resp, **handle_create_favorite(dur)}
        else:
            resp["error"] = f"unknown cmd: {c}"
    except Exception as e:
        resp["error"] = str(e)
    send_response(ser, resp)


# ---------------------------------------------------------------------------
# Serial loop (background thread)
# ---------------------------------------------------------------------------


def serial_loop(port: str) -> None:
    global _ser, _expecting_pong
    try:
        _ser = serial.Serial(port, SERIAL_BAUD, timeout=0.1)
        print(f"[Serial] Listening on {port} @ {SERIAL_BAUD}")
    except serial.SerialException as e:
        print(f"[Serial] Cannot open {port}: {e}")
        return

    while _ser and _ser.is_open:
        try:
            raw = _ser.readline()
            if not raw:
                time.sleep(0.01)
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            _debug(f"Serial RX: {line[:80]}{'...' if len(line) > 80 else ''}", "serial")

            if line == "PONG":
                if _expecting_pong:
                    _expecting_pong = False
                    _pong_event.set()
                _debug("Serial: PONG received (ESP32 responded over USB)", "serial")
            elif line == "READY":
                _debug("Serial: ESP32 READY", "serial")
            elif line == "REPEAT":
                _debug("Serial: REPEAT command from ESP32 (button press over USB)", "serial")
                handle_esp32_repeat()
            elif line.startswith("AUDIO_PLAYBACK_ACK"):
                pass
            elif line == "AUDIO_ECHO_DONE":
                pass
            elif line.startswith("AUDIO "):
                process_audio_binary(_ser, line)
            elif line.startswith("{") and '"cmd"' in line:
                try:
                    cmd = json.loads(line)
                    process_command(_ser, cmd)
                except json.JSONDecodeError:
                    send_response(_ser, {"cmd": "?", "ok": False, "error": "bad JSON"})
        except (serial.SerialException, OSError):
            break
        time.sleep(0.01)


# ---------------------------------------------------------------------------
# HTML page
# ---------------------------------------------------------------------------

PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIpril</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #f8f9fc;
      --surface: #ffffff;
      --border: #e8eaef;
      --text: #1a1d26;
      --text2: #5f6577;
      --accent: #6c5ce7;
      --accent-light: #a29bfe;
      --accent-bg: #f0eeff;
      --red: #ff6b6b;
      --red-dark: #ee5a5a;
      --blue: #4facfe;
      --green: #00b894;
      --green-bg: #e6faf5;
      --yellow: #fdcb6e;
      --danger-bg: #fff0f0;
      --danger: #d63031;
      --radius: 12px;
      --radius-sm: 8px;
      --shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
      --shadow-lg: 0 4px 20px rgba(108,92,231,0.10);
    }

    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      min-height: 100vh;
    }

    .container { max-width: 680px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

    /* ---- Header ---- */
    .header {
      text-align: center;
      padding: 2.5rem 0 1.5rem;
    }
    .header h1 {
      font-size: 2rem;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent), var(--blue));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.5px;
    }
    .header p {
      color: var(--text2);
      font-size: 0.9rem;
      margin-top: 0.25rem;
    }

    /* ---- Cards ---- */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      margin-bottom: 1rem;
      box-shadow: var(--shadow);
    }
    .card h2 {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .card h2 .icon {
      width: 20px; height: 20px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
    }

    /* ---- Auth Banner ---- */
    .auth-banner {
      border-radius: var(--radius);
      padding: 0.85rem 1.25rem;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      font-size: 0.875rem;
      font-weight: 500;
      box-shadow: var(--shadow);
    }
    .auth-ok { background: var(--green-bg); color: #0a7c65; border: 1px solid #b2ebe0; }
    .auth-fail { background: var(--danger-bg); color: var(--danger); border: 1px solid #ffd4d4; }
    .auth-checking { background: var(--surface); color: var(--text2); border: 1px solid var(--border); }
    .auth-banner button {
      margin: 0; margin-left: auto;
      background: var(--accent);
      color: white;
      border: none;
      border-radius: var(--radius-sm);
      padding: 0.5rem 1.1rem;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .auth-banner button:hover { background: #5a4bd6; }
    #appContent.locked { opacity: 0.3; pointer-events: none; user-select: none;
                         filter: grayscale(0.5); transition: opacity 0.3s, filter 0.3s; }
    #appContent { transition: opacity 0.3s, filter 0.3s; }

    /* ---- Connection status ---- */
    #status {
      font-size: 0.8rem;
      color: var(--text2);
      background: var(--bg);
      display: inline-block;
      padding: 0.3rem 0.75rem;
      border-radius: 999px;
      border: 1px solid var(--border);
      margin-bottom: 1rem;
    }

    /* ---- Action Buttons ---- */
    .actions { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
    .actions button {
      flex: 1;
      min-width: 110px;
      min-height: 48px;
      border: none;
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.1s, box-shadow 0.15s, opacity 0.15s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
    }
    .actions button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .actions button:active { transform: translateY(0); }
    button:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }

    .btn-record {
      background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
      color: white;
      user-select: none; -webkit-user-select: none;
    }
    .btn-record.recording {
      background: linear-gradient(135deg, #ff8787, #ff6b6b);
      animation: glow 1s ease-in-out infinite alternate;
    }
    @keyframes glow {
      from { box-shadow: 0 0 8px rgba(255,107,107,0.4); }
      to   { box-shadow: 0 0 20px rgba(255,107,107,0.7); }
    }
    .btn-repeat { background: linear-gradient(135deg, var(--blue), #0984e3); color: white; }
    .btn-favorite { background: linear-gradient(135deg, var(--green), #00a884); color: white; }
    .btn-default { background: var(--bg); color: var(--text); border: 1px solid var(--border) !important; }
    .btn-default:hover { background: #eef0f4; }

    /* ---- Result ---- */
    #result {
      padding: 1rem 1.15rem;
      background: var(--accent-bg);
      border: 1px solid #e0daf8;
      border-radius: var(--radius-sm);
      font-size: 0.9rem;
      line-height: 1.5;
      min-height: 44px;
      white-space: pre-wrap;
      color: var(--text);
    }
    #result.empty { color: var(--text2); background: var(--bg); border-color: var(--border); }

    /* ---- Audio Player ---- */
    #audioPlayer {
      margin-top: 0.75rem;
      width: 100%;
      border-radius: var(--radius-sm);
    }

    /* ---- Log ---- */
    .log-toggle {
      margin-top: 0.75rem;
      font-size: 0.75rem;
      color: var(--text2);
      cursor: pointer;
      user-select: none;
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }
    .log-toggle:hover { color: var(--accent); }
    #log {
      margin-top: 0.5rem;
      padding: 0.85rem 1rem;
      background: #1e1f2e;
      color: #c9cde0;
      font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
      font-size: 0.7rem;
      max-height: 160px;
      overflow-y: auto;
      border-radius: var(--radius-sm);
      white-space: pre-wrap;
      line-height: 1.7;
      display: none;
    }
    #log.open { display: block; }

    /* ---- Settings ---- */
    label {
      display: block;
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--text2);
      margin-top: 1rem;
      margin-bottom: 0.25rem;
    }
    input, textarea {
      width: 100%;
      padding: 0.6rem 0.75rem;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 0.875rem;
      color: var(--text);
      background: var(--bg);
      transition: border-color 0.15s, box-shadow 0.15s;
      outline: none;
    }
    input:focus, textarea:focus {
      border-color: var(--accent-light);
      box-shadow: 0 0 0 3px rgba(108,92,231,0.1);
    }
    textarea { min-height: 70px; resize: vertical; }

    .day-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      margin-top: 0.75rem;
    }
    .day-header span { font-size: 0.9rem; color: var(--text2); }
    .day-events {
      margin-top: 0.5rem;
      padding: 0.75rem;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      max-height: 220px;
      overflow-y: auto;
      font-size: 0.85rem;
    }
    .day-event {
      padding: 0.4rem 0;
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .day-event:last-child { border-bottom: none; }
    .day-event-summary { font-weight: 600; color: var(--text); }
    .day-event-time { font-size: 0.75rem; color: var(--text2); }

    .label-list {
      max-height: 180px;
      overflow-y: auto;
      margin-top: 0.25rem;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 0.35rem;
      background: var(--bg);
    }
    .label-row {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      margin: 0.25rem 0;
    }
    .label-row input { flex: 1; margin: 0; padding: 0.45rem 0.6rem; font-size: 0.8rem; }
    .label-row .btn-del {
      min-height: 0; min-width: 0; margin: 0;
      padding: 0.3rem 0.55rem;
      background: transparent;
      color: var(--text2);
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 0.7rem;
      cursor: pointer;
      transition: all 0.15s;
    }
    .label-row .btn-del:hover { background: var(--danger-bg); color: var(--danger); border-color: #ffd4d4; }

    .settings-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    }
    .settings-actions button {
      padding: 0.55rem 1.1rem;
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: background 0.15s, transform 0.1s;
    }
    .settings-actions button:hover { transform: translateY(-1px); }
    .btn-add { background: var(--bg); color: var(--text); border: 1px solid var(--border) !important; }
    .btn-add:hover { background: #eef0f4; }
    .btn-save { background: var(--accent); color: white; }
    .btn-save:hover { background: #5a4bd6; }

    .msg { margin-top: 0.75rem; padding: 0.6rem 0.85rem; border-radius: var(--radius-sm);
           font-size: 0.8rem; font-weight: 500; }
    .msg.ok { background: var(--green-bg); color: #0a7c65; }
    .msg.err { background: var(--danger-bg); color: var(--danger); }

    .dur-input { width: 100px !important; }
  </style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>AIpril</h1>
    <p>Voice-powered calendar assistant</p>
  </div>

  <div id="authBanner" class="auth-banner auth-checking">
    <span id="authText">Checking Google Calendar authentication...</span>
  </div>

  <div id="appContent" class="locked">

    <!-- Record & Actions -->
    <div class="card">
      <h2><span class="icon" style="background:linear-gradient(135deg,#ff6b6b,#ee5a5a);color:#fff;">&#9679;</span> Record</h2>
      <span id="status">{{ conn_status }}</span>

      <div class="actions">
        <button type="button" id="recordBtn" class="btn-record">Hold to Record</button>
        <button type="button" id="repeatBtn" class="btn-repeat">Repeat Last</button>
        <button type="button" id="favoriteBtn" class="btn-favorite">Favorite</button>
        <button type="button" id="pingBtn" class="btn-default">Ping</button>
      </div>

      <div id="result" class="empty">
        Hold the record button, say what you're doing, and release.
      </div>

      <audio id="audioPlayer" controls style="display:none;"></audio>

      <div class="log-toggle" id="logToggle" onclick="toggleDebugLog(this)">
        <span>&#9654;</span> Debug log
      </div>
      <div id="log">&mdash;</div>
    </div>

    <!-- Today's Schedule -->
    <div class="card">
      <h2><span class="icon" style="background:var(--green-bg);color:var(--green);">&#128197;</span> Today</h2>
      <div class="day-header">
        <span id="dayDate">—</span>
        <button type="button" id="refreshDayBtn" class="btn-default">Refresh</button>
      </div>
      <div id="dayEvents" class="day-events">Loading...</div>
    </div>

    <!-- Settings -->
    <div class="card">
      <h2><span class="icon" style="background:var(--accent-bg);color:var(--accent);">&#9881;</span> Settings</h2>
      <form id="form" method="POST" action="/api/settings">

        <label>Favorite event name</label>
        <input name="favorite_name" value="{{ favorite_name }}" placeholder="Focus Work">

        <label>Favorite event description</label>
        <textarea name="favorite_desc" placeholder="Deep focus block">{{ favorite_desc }}</textarea>

        <label>Event duration (minutes)</label>
        <input name="event_duration" type="number" min="5" max="480" step="5"
               value="{{ event_duration }}" class="dur-input">

        <label>Event labels</label>
        <div class="label-list" id="labels">
          {% for l in event_labels %}
          <div class="label-row">
            <input type="text" name="label" value="{{ l }}">
            <button type="button" class="btn-del" onclick="this.parentElement.remove()">&#10005;</button>
          </div>
          {% endfor %}
        </div>

        <div class="settings-actions">
          <button type="button" id="addLabelBtn" class="btn-add">+ Add label</button>
          <button type="submit" class="btn-save">Save settings</button>
        </div>
      </form>
      <div id="msg"></div>
    </div>

  </div>
</div>

  <script>
    let mediaRecorder = null;
    let audioChunks = [];
    let recordStartTime = null;

    const $ = id => document.getElementById(id);
    const log = msg => { $('log').textContent += '\\n' + msg; $('log').scrollTop = $('log').scrollHeight; };
    const setStatus = msg => $('result').textContent = msg;

    /* ---- Auth ---- */

    async function checkAuth() {
      try {
        const r = await fetch('/api/auth/status');
        const d = await r.json();
        const banner = $('authBanner');
        const content = $('appContent');

        if (d.authenticated) {
          banner.className = 'auth-banner auth-ok';
          banner.innerHTML = '<span>Google Calendar: Authenticated</span>';
          content.classList.remove('locked');
        } else {
          banner.className = 'auth-banner auth-fail';
          banner.innerHTML = '<span>' + (d.has_credentials
            ? 'Google Calendar: Not authenticated'
            : 'Google Calendar: Missing credentials.json') + '</span>'
            + (d.has_credentials
              ? '<button onclick="window.location.href=\\'/auth/start\\'">Authenticate with Google</button>'
              : '');
          content.classList.add('locked');
        }
      } catch (err) {
        $('authBanner').className = 'auth-banner auth-fail';
        $('authBanner').innerHTML = '<span>Could not check auth status</span>';
      }
    }

    /* ---- Status ---- */

    async function checkStatus() {
      const r = await fetch('/api/status');
      return await r.json();
    }

    async function refreshConn() {
      const d = await checkStatus();
      const parts = [];
      if (d.wifi_connected) parts.push('WiFi (' + d.esp32_ip + ')');
      if (d.serial_connected) parts.push('Serial');
      $('status').textContent = parts.length
        ? 'ESP32: ' + parts.join(' + ')
        : 'No ESP32 connected';
    }

    /* ---- Hold to Record ---- */

    function startHoldRecord(e) {
      e.preventDefault();
      if (mediaRecorder && mediaRecorder.state === 'recording') return;

      $('log').textContent = '';
      setStatus('Recording...');
      $('recordBtn').classList.add('recording');
      log('Requesting microphone...');

      navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = ev => { if (ev.data.size) audioChunks.push(ev.data); };
        mediaRecorder.onstop = () => {
          stream.getTracks().forEach(t => t.stop());
          $('recordBtn').classList.remove('recording');
          const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
          log('Recording stopped (' + blob.size + ' bytes). Sending to server...');
          sendToEsp32(blob);
        };
        mediaRecorder.start();
        recordStartTime = new Date().toISOString();
        log('Recording from mic (release button to stop)...');
      }).catch(err => {
        $('recordBtn').classList.remove('recording');
        setStatus('Mic error: ' + err.message);
        log('getUserMedia error: ' + err);
      });
    }

    function stopHoldRecord(e) {
      e.preventDefault();
      if (!mediaRecorder || mediaRecorder.state !== 'recording') return;
      mediaRecorder.stop();
    }

    function appendDebugLog(entries) {
      if (Array.isArray(entries)) entries.forEach(log);
    }

    let debugLogPollTimer = null;
    async function fetchServerDebugLog() {
      try {
        const r = await fetch('/api/debug/log?n=100');
        const d = await r.json();
        if (d.entries && d.entries.length) {
          $('log').textContent = d.entries.join('\\n');
          $('log').scrollTop = $('log').scrollHeight;
        }
      } catch (_) {}
    }
    function toggleDebugLog(el) {
      const logEl = $('log');
      logEl.classList.toggle('open');
      el.querySelector('span').textContent = logEl.classList.contains('open') ? '&#9660;' : '&#9654;';
      if (logEl.classList.contains('open')) {
        fetchServerDebugLog();
        debugLogPollTimer = setInterval(fetchServerDebugLog, 2000);
      } else {
        if (debugLogPollTimer) clearInterval(debugLogPollTimer);
        debugLogPollTimer = null;
      }
    }

    async function sendToEsp32(blob) {
      const fd = new FormData();
      fd.append('audio', blob, 'recording.webm');
      if (recordStartTime) fd.append('start_time', recordStartTime);

      setStatus('Sending to server (browser → HTTP)...');
      log('Uploading audio via HTTP (browser → server)...');

      try {
        const r = await fetch('/api/record/send_to_esp32', { method: 'POST', body: fd });
        const data = await r.json();

        if (data.debug_log) appendDebugLog(data.debug_log);

        if (data.ok) {
          log('Processed locally (browser → server HTTP, no ESP32 round-trip).');

          if (data.transcript) {
            log('Transcript: ' + data.transcript);
            log('Activity: ' + (data.event_name || '(none)') + ' (' + (data.category || '?') + ')');
            if (data.event_id) log('Calendar event created: ' + data.event_id);
            else if (data.cal_error) log('Calendar error: ' + data.cal_error);
            setStatus(data.event_name
              ? data.event_name + '  —  "' + data.transcript + '"'
                + (data.event_id ? ' (added to calendar)' : '')
              : data.transcript);
          } else {
            setStatus(data.message || 'No speech detected.');
            log(data.message || 'Empty transcript.');
          }

          playLastAudio();
          refreshDayCalendar();
        } else {
          setStatus('Error: ' + (data.error || 'unknown'));
          log('Error: ' + (data.error || JSON.stringify(data)));
        }
      } catch (err) {
        setStatus('Fetch error: ' + err.message);
        log('Fetch error: ' + err);
      }
    }

    function playLastAudio() {
      const player = $('audioPlayer');
      player.src = '/api/audio/last?t=' + Date.now();
      player.style.display = 'block';
      player.play().then(() => {
        setStatus('Playing echoed audio.');
        log('Audio playback started.');
      }).catch(err => {
        setStatus('Playback error (try the player controls below).');
        log('Auto-play blocked or error: ' + err);
      });
    }

    /* ---- Ping ---- */

    async function onPing() {
      setStatus('Pinging ESP32 (WiFi)...');
      log('Sending PING via HTTP (server → ESP32 WiFi)...');
      try {
        const r = await fetch('/api/ping', { method: 'POST' });
        const d = await r.json();
        if (d.debug_log) appendDebugLog(d.debug_log);
        setStatus(d.ok ? 'ESP32 responded (PONG).' : 'No response from ESP32.');
        log(d.ok ? 'PONG received (WiFi)!' : (d.error || d.message || 'Timeout'));
      } catch (err) {
        setStatus('Error: ' + err.message);
      }
    }

    /* ---- Today's Schedule ---- */

    function formatEventTime(s) {
      if (!s || s.length === 10) return 'All day';
      try {
        const d = new Date(s.replace('Z', '+00:00'));
        return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
      } catch (_) { return s; }
    }

    async function refreshDayCalendar() {
      const el = $('dayEvents');
      const dateEl = $('dayDate');
      try {
        const r = await fetch('/api/calendar/day');
        const d = await r.json();
        if (!d.ok) {
          el.textContent = d.error || 'Error loading calendar';
          dateEl.textContent = '—';
          return;
        }
        dateEl.textContent = d.date ? new Date(d.date + 'T12:00:00Z').toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' }) : '—';
        if (!d.events || d.events.length === 0) {
          el.innerHTML = '<span style="color:var(--text2);">No events today</span>';
          return;
        }
        el.innerHTML = d.events.map(ev => {
          const start = formatEventTime(ev.start);
          const end = formatEventTime(ev.end);
          const timeStr = start === 'All day' ? 'All day' : (start + ' – ' + end);
          const summary = (ev.summary || '(no title)').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
          return '<div class="day-event"><span class="day-event-summary">' + summary + '</span><span class="day-event-time">' + timeStr + '</span></div>';
        }).join('');
      } catch (err) {
        el.textContent = 'Failed to load';
        dateEl.textContent = '—';
      }
    }

    /* ---- Repeat / Favorite ---- */

    async function onRepeat() {
      setStatus('Repeating last activity...');
      const r = await fetch('/api/trigger/repeat', { method: 'POST' });
      const d = await r.json();
      if (d.debug_log) appendDebugLog(d.debug_log);
      if (d.ok) {
        setStatus('Repeated: ' + (d.event_name || '') + (d.event_id ? ' (added to calendar)' : ''));
        log('Repeated "' + (d.event_name || '') + '"' + (d.event_id ? ' → event ' + d.event_id : ''));
        refreshDayCalendar();
      } else {
        setStatus(d.error || 'No previous activity');
        log('Repeat error: ' + (d.error || 'unknown'));
      }
    }

    async function onFavorite() {
      setStatus('Logging favorite...');
      const r = await fetch('/api/trigger/favorite', { method: 'POST' });
      const d = await r.json();
      if (d.debug_log) appendDebugLog(d.debug_log);
      if (d.ok) {
        setStatus('Favorite: ' + (d.event_name || '') + (d.event_id ? ' (added to calendar)' : ''));
        log('Favorite "' + (d.event_name || '') + '"' + (d.event_id ? ' → event ' + d.event_id : ''));
        refreshDayCalendar();
      } else {
        setStatus(d.error || 'Error');
        log('Favorite error: ' + (d.error || 'unknown'));
      }
    }

    /* ---- Settings form ---- */

    function initForm() {
      const form = $('form');
      if (!form) return;
      form.addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const labels = Array.from(fd.getAll('label')).filter(v => v.trim());
        const body = {
          favorite_name: fd.get('favorite_name') || '',
          favorite_desc: fd.get('favorite_desc') || '',
          event_duration: parseInt(fd.get('event_duration')) || 30,
          event_labels: labels.length ? labels : ['Work', 'School']
        };
        const r = await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await r.json();
        $('msg').textContent = data.ok ? 'Settings saved.' : (data.error || 'Error');
        $('msg').className = data.ok ? 'msg ok' : 'msg err';
      });
    }

    /* ---- Init ---- */

    function init() {
      checkAuth();

      initForm();
      $('addLabelBtn')?.addEventListener('click', () => {
        const row = document.createElement('div');
        row.className = 'label-row';
        row.innerHTML = '<input type="text" name="label" placeholder="New label">'
          + '<button type="button" class="btn-del" onclick="this.parentElement.remove()">✕</button>';
        $('labels').appendChild(row);
        row.querySelector('input').focus();
        $('labels').scrollTop = $('labels').scrollHeight;
      });

      $('pingBtn')?.addEventListener('click', onPing);
      $('refreshDayBtn')?.addEventListener('click', refreshDayCalendar);
      refreshDayCalendar();
      $('repeatBtn')?.addEventListener('click', onRepeat);
      $('favoriteBtn')?.addEventListener('click', onFavorite);

      const rec = $('recordBtn');
      if (rec) {
        rec.addEventListener('mousedown',  e => { e.preventDefault(); startHoldRecord(e); });
        rec.addEventListener('mouseup',    e => { e.preventDefault(); stopHoldRecord(e); });
        rec.addEventListener('mouseleave', stopHoldRecord);
        rec.addEventListener('touchstart', e => { e.preventDefault(); startHoldRecord(e); }, { passive: false });
        rec.addEventListener('touchend',   e => { e.preventDefault(); stopHoldRecord(e); }, { passive: false });
      }

      refreshConn();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  </script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Web routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    s = load()
    labels = s.get("event_labels") or DEFAULTS["event_labels"]
    with _ser_lock:
        connected = _ser is not None and _ser.is_open
    conn = "ESP32 connected via serial" if connected else "No ESP32 — audio stored locally (no echo)"
    resp = render_template_string(
        PAGE_HTML,
        favorite_name=s.get("favorite_name", ""),
        favorite_desc=s.get("favorite_desc", ""),
        event_duration=s.get("event_duration", DEFAULTS["event_duration"]),
        event_labels=labels,
        conn_status=conn,
    )
    resp = app.make_response(resp)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------


@app.route("/api/auth/status")
def api_auth_status():
    authed = is_authenticated(TOKEN_FILE)
    has_creds = CREDENTIALS_FILE.exists()
    return jsonify({"authenticated": authed, "has_credentials": has_creds})


@app.route("/auth/start")
def auth_start():
    """Redirect user to Google's OAuth consent page."""
    redirect_uri = request.host_url.rstrip("/") + "/auth/callback"
    url = get_auth_url(CREDENTIALS_FILE, redirect_uri)
    if not url:
        return "Missing credentials.json — download from Google Cloud Console and place in server/", 400
    return redirect(url)


@app.route("/auth/callback")
def auth_callback():
    """Google redirects here with ?code=... after user grants consent."""
    code = request.args.get("code")
    if not code:
        return "Missing authorization code", 400
    if handle_auth_callback(code, TOKEN_FILE):
        print("[Auth] Google Calendar authenticated successfully")
        return redirect("/")
    return "Authentication failed — check server logs", 500


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.route("/api/calendar/now", methods=["POST"])
def api_calendar_now():
    """Return events happening right now, with duplicate detection."""
    try:
        result = handle_current_events()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/calendar/day")
def api_calendar_day():
    """Return all events for the current day (UTC)."""
    try:
        result = handle_today_events()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(load())


@app.route("/api/settings", methods=["POST"])
def post_settings():
    try:
        data = request.get_json()
        if data is None:
            data = {
                "favorite_name": request.form.get("favorite_name", ""),
                "favorite_desc": request.form.get("favorite_desc", ""),
                "event_labels": request.form.getlist("label") or DEFAULTS["event_labels"],
            }
        save({
            "favorite_name": data.get("favorite_name", ""),
            "favorite_desc": data.get("favorite_desc", ""),
            "event_duration": int(data.get("event_duration", DEFAULTS["event_duration"])),
            "event_labels": data.get("event_labels", DEFAULTS["event_labels"]),
        })
        if request.get_json() is not None:
            return jsonify({"ok": True})
        return redirect(url_for("index"))
    except Exception as e:
        if request.get_json() is not None:
            return jsonify({"ok": False, "error": str(e)}), 400
        return redirect(url_for("index"))


@app.route("/api/status")
def api_status():
    with _ser_lock:
        serial_ok = _ser is not None and _ser.is_open
    wifi_ok = _esp32_wifi_ip is not None and (time.time() - _esp32_wifi_last_seen < 300)
    return jsonify({
        "serial_connected": serial_ok,
        "wifi_connected": wifi_ok,
        "esp32_ip": _esp32_wifi_ip if wifi_ok else None,
        "last_activity": _last_activity,
    })


@app.route("/api/ping", methods=["POST"])
def api_ping():
    """Ping ESP32 over WiFi (HTTP GET to ESP32's /ping endpoint)."""
    import requests as req_lib
    log_ = []
    src = "browser"

    if not _esp32_wifi_ip:
        msg = "Ping: ESP32 WiFi IP unknown (register or record first)"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": False, "error": "ESP32 WiFi IP not known yet (record something first)", "debug_log": log_})
    msg = f"Ping: sending HTTP GET to ESP32 at {_esp32_wifi_ip}/ping (WiFi)"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)
    try:
        r = req_lib.get(f"http://{_esp32_wifi_ip}/ping", timeout=3)
        data = r.json()
        msg = f"Ping: ESP32 responded PONG (WiFi, status={r.status_code})"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": data.get("ok", False),
                        "message": data.get("message", "PONG"),
                        "esp32_ip": _esp32_wifi_ip,
                        "debug_log": log_})
    except req_lib.ConnectionError:
        log_.append(f"[{src}] Ping: connection failed to {_esp32_wifi_ip}")
        _debug(log_[-1], src)
        return jsonify({"ok": False, "error": f"Cannot reach ESP32 at {_esp32_wifi_ip}", "debug_log": log_})
    except req_lib.Timeout:
        log_.append(f"[{src}] Ping: timeout waiting for ESP32 at {_esp32_wifi_ip}")
        _debug(log_[-1], src)
        return jsonify({"ok": False, "error": f"Timeout pinging ESP32 at {_esp32_wifi_ip}", "debug_log": log_})


@app.route("/api/trigger/repeat", methods=["POST"])
def api_trigger_repeat():
    """Re-create the last activity as a new calendar event starting now."""
    log_ = []
    src = "esp32_wifi" if _esp32_wifi_ip and request.remote_addr == _esp32_wifi_ip else "browser"

    if not _last_activity:
        msg = "Repeat: no previous activity (HTTP from browser)"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": False, "error": "No previous activity to repeat", "debug_log": log_})
    msg = f"Repeat: re-creating \"{_last_activity['event_name']}\" via HTTP"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)
    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    try:
        result = handle_create_event(
            _last_activity["event_name"],
            _last_activity["transcript"],
            dur,
        )
        if result.get("ok"):
            msg = f"Repeat: created event {result.get('event_id', '')}"
        else:
            msg = f"Repeat: calendar error {result.get('error', '')}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": result.get("ok"),
                        "event_name": _last_activity["event_name"],
                        "event_id": result.get("event_id", ""),
                        "error": result.get("error"),
                        "debug_log": log_})
    except Exception as e:
        msg = f"Repeat: exception {e}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": False, "error": str(e), "debug_log": log_})


@app.route("/api/trigger/favorite", methods=["POST"])
def api_trigger_favorite():
    """Create a calendar event using the favorite name/desc from settings."""
    log_ = []
    src = "esp32_wifi" if _esp32_wifi_ip and request.remote_addr == _esp32_wifi_ip else "browser"

    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    name = s.get("favorite_name", "Focus Work")
    desc = s.get("favorite_desc", "")
    msg = f"Favorite: creating \"{name}\" ({dur} min) via HTTP"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)
    try:
        result = handle_create_event(name, desc, dur)
        if result.get("ok"):
            msg = f"Favorite: created event {result.get('event_id', '')}"
        else:
            msg = f"Favorite: calendar error {result.get('error', '')}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": result.get("ok"),
                        "event_name": name,
                        "event_id": result.get("event_id", ""),
                        "error": result.get("error"),
                        "debug_log": log_})
    except Exception as e:
        msg = f"Favorite: exception {e}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": False, "error": str(e), "debug_log": log_})


# ---------------------------------------------------------------------------
# Echo pipeline
# ---------------------------------------------------------------------------


@app.route("/api/record/send_to_esp32", methods=["POST"])
def api_record_send_to_esp32():
    """Browser record → store audio → transcribe → interpret → calendar.
    No serial echo — audio stays on server for playback."""
    global _echo_audio, _echo_mime, _last_activity

    from datetime import datetime

    log_ = []
    src = "browser"

    f = request.files.get("audio")
    if not f:
        _debug("Record: no audio file in request", src)
        return jsonify({"ok": False, "error": "No audio file", "debug_log": log_}), 400
    audio_bytes = f.read()
    if not audio_bytes:
        _debug("Record: empty audio", src)
        return jsonify({"ok": False, "error": "Empty audio", "debug_log": log_}), 400

    msg = f"Record: received {len(audio_bytes)} bytes from browser (HTTP)"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)

    start_time_str = request.form.get("start_time", "")
    if start_time_str:
        try:
            record_start = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            record_start = record_start.replace(tzinfo=None)
        except ValueError:
            record_start = datetime.utcnow()
    else:
        record_start = datetime.utcnow()

    mime = f.content_type or "audio/webm"

    # Store for browser playback (no serial round-trip)
    _echo_audio = audio_bytes
    _echo_mime = mime
    msg = f"Record: stored {len(audio_bytes)} bytes for playback"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)

    # --- STT ---
    msg = f"STT: transcribing {len(audio_bytes)} bytes ({mime})..."
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)
    tr = handle_transcribe_bytes(audio_bytes, mime)
    if not tr.get("ok"):
        msg = f"STT failed: {tr.get('error', 'unknown')}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": False, "error": tr.get("error", "STT failed"),
                        "transcript": "", "event_name": "", "debug_log": log_})

    transcript = tr.get("transcript", "")
    if not transcript:
        msg = "STT: no speech detected"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
        return jsonify({"ok": True, "transcript": "",
                        "event_name": "", "category": "",
                        "message": "No speech detected", "debug_log": log_})

    msg = f"STT: transcript = \"{transcript[:60]}{'...' if len(transcript) > 60 else ''}\""
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)

    # --- LLM interpret ---
    msg = "LLM: interpreting transcript..."
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)
    interp = handle_interpret(transcript)
    event_name = interp.get("event_name", transcript[:40])
    category = interp.get("category", "other")
    msg = f"LLM: event_name=\"{event_name}\" category={category}"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)

    _last_activity = {"event_name": event_name, "transcript": transcript}

    # --- Create Google Calendar event ---
    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    msg = f"Cal: creating event at {record_start.isoformat()} ({dur} min)"
    log_.append(f"[{src}] {msg}")
    _debug(msg, src)
    cal = handle_create_event(event_name, transcript, dur, start=record_start)

    result = {
        "ok": True,
        "transcript": transcript,
        "event_name": event_name,
        "category": category,
        "debug_log": log_,
    }
    if cal.get("ok"):
        result["event_id"] = cal["event_id"]
        msg = f"Cal: created event {cal['event_id']}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)
    else:
        result["cal_error"] = cal.get("error", "Calendar failed")
        msg = f"Cal: error {result['cal_error']}"
        log_.append(f"[{src}] {msg}")
        _debug(msg, src)

    return jsonify(result)


@app.route("/api/audio/last")
def api_audio_last():
    if not _echo_audio:
        return Response("No audio stored", status=404)
    return Response(_echo_audio, mimetype=_echo_mime or "audio/webm",
                    headers={"Cache-Control": "no-store"})


@app.route("/api/debug/log")
def api_debug_log():
    """Return recent server debug log (browser, esp32_wifi, serial activity)."""
    n = min(int(request.args.get("n", 50)), 100)
    return jsonify({"entries": _debug_log[-n:], "total": len(_debug_log)})


@app.route("/debug")
def debug_redirect():
    return redirect("/")


# ---------------------------------------------------------------------------
# ESP32 WiFi endpoints
# ---------------------------------------------------------------------------


@app.route("/api/esp32/register", methods=["POST"])
def api_esp32_register():
    """ESP32 calls this on boot to announce its WiFi IP."""
    src = "esp32_wifi"
    ip = request.remote_addr
    _update_esp32_wifi(ip)
    _debug(f"Register: ESP32 POST from {ip} (WiFi) — stored as ESP32 IP", src)
    return jsonify({"ok": True})


@app.route("/api/esp32/record", methods=["POST"])
def api_esp32_record():
    """ESP32 posts raw WAV audio over WiFi. Server does STT → interpret → calendar."""
    global _last_activity

    from datetime import datetime

    src = "esp32_wifi"
    ip = request.remote_addr

    audio_bytes = request.get_data()
    if not audio_bytes:
        _debug("Record (ESP32): no audio data in POST body", src)
        return jsonify({"ok": False, "error": "No audio data"}), 400

    content_type = request.content_type or "audio/wav"
    record_start = datetime.utcnow()

    _update_esp32_wifi(ip)
    _debug(f"Record (ESP32): received {len(audio_bytes)} bytes from {ip} via WiFi HTTP ({content_type})", src)

    _debug(f"Record (ESP32): STT transcribing {len(audio_bytes)} bytes...", src)
    tr = handle_transcribe_bytes(audio_bytes, content_type)
    if not tr.get("ok"):
        _debug(f"Record (ESP32): STT failed {tr.get('error', '')}", src)
        return jsonify({"ok": False, "error": tr.get("error", "STT failed"),
                        "transcript": "", "event_name": ""})

    transcript = tr.get("transcript", "")
    if not transcript:
        _debug("Record (ESP32): no speech detected", src)
        return jsonify({"ok": True, "transcript": "", "event_name": "",
                        "message": "No speech detected"})

    _debug(f"Record (ESP32): transcript=\"{transcript[:60]}{'...' if len(transcript) > 60 else ''}\"", src)

    _debug("Record (ESP32): LLM interpreting...", src)
    interp = handle_interpret(transcript)
    event_name = interp.get("event_name", transcript[:40])
    category = interp.get("category", "other")
    _debug(f"Record (ESP32): event_name=\"{event_name}\" category={category}", src)

    _last_activity = {"event_name": event_name, "transcript": transcript}

    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    _debug(f"Record (ESP32): creating calendar event ({dur} min)", src)
    cal = handle_create_event(event_name, transcript, dur, start=record_start)

    result = {
        "ok": True,
        "transcript": transcript,
        "event_name": event_name,
        "category": category,
    }
    if cal.get("ok"):
        result["event_id"] = cal["event_id"]
        _debug(f"Record (ESP32): created event {cal['event_id']}", src)
    else:
        result["error"] = cal.get("error", "Calendar failed")
        _debug(f"Record (ESP32): calendar error {result['error']}", src)

    return jsonify(result)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_serial = "--no-serial" in sys.argv
    port = args[0] if args else SERIAL_PORT

    if is_authenticated(TOKEN_FILE):
        print("[Auth] Google Calendar: authenticated")
    else:
        print("[Auth] Google Calendar: NOT authenticated — open http://localhost:5000 to authenticate")

    if not no_serial:
        t = threading.Thread(target=serial_loop, args=(port,), daemon=True)
        t.start()
        print(f"[Info] Serial thread started on {port}")
    else:
        print("[Info] --no-serial: skipping serial connection")

    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"[Info] Web UI: http://localhost:5000")
    print(f"[Info] ESP32 endpoint: http://{local_ip}:5000/api/esp32/record")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
