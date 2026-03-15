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

_expecting_echo = False
_echo_audio: bytes = b""
_echo_mime: str = "audio/webm"
_echo_event = threading.Event()

_expecting_pong = False
_pong_event = threading.Event()

# ---------------------------------------------------------------------------
# Serial helpers
# ---------------------------------------------------------------------------


def send_line(text: str) -> bool:
    with _ser_lock:
        if not _ser or not _ser.is_open:
            return False
        _ser.write((text + "\n").encode("utf-8"))
        _ser.flush()
    return True


def send_audio_to_esp32(audio_bytes: bytes) -> bool:
    """Send audio to ESP32 in throttled chunks to avoid RX buffer overflow."""
    with _ser_lock:
        if not _ser or not _ser.is_open:
            return False
        header = f"AUDIO_PLAYBACK {len(audio_bytes)}\n"
        _ser.write(header.encode("utf-8"))
        _ser.flush()
        time.sleep(0.05)
        CHUNK = 1024
        for i in range(0, len(audio_bytes), CHUNK):
            _ser.write(audio_bytes[i:i + CHUNK])
            _ser.flush()
        print(f"[Echo] Sent AUDIO_PLAYBACK ({len(audio_bytes)} bytes) to ESP32")
    return True


# ---------------------------------------------------------------------------
# Serial protocol handlers
# ---------------------------------------------------------------------------


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

            print(f"[Serial] RX: {line[:80]}{'...' if len(line) > 80 else ''}")

            if line == "PONG":
                if _expecting_pong:
                    _expecting_pong = False
                    _pong_event.set()
            elif line == "READY":
                print("[Info] ESP32 is ready")
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

      <div class="log-toggle" onclick="$('log').classList.toggle('open'); this.querySelector('span').textContent = $('log').classList.contains('open') ? '&#9660;' : '&#9654;';">
        <span>&#9654;</span> Debug log
      </div>
      <div id="log">&mdash;</div>
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
      $('status').textContent = d.serial_connected
        ? 'ESP32 connected via serial'
        : 'No ESP32 — audio stored locally (no echo)';
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

    async function sendToEsp32(blob) {
      const fd = new FormData();
      fd.append('audio', blob, 'recording.webm');
      if (recordStartTime) fd.append('start_time', recordStartTime);

      setStatus('Sending to ESP32 for echo + transcription...');
      log('Uploading audio...');

      try {
        const r = await fetch('/api/record/send_to_esp32', { method: 'POST', body: fd });
        const data = await r.json();

        if (data.ok) {
          log(data.local ? 'No ESP32 — processed locally.' : 'ESP32 echo received.');

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
      setStatus('Pinging ESP32...');
      log('Sending PING...');
      try {
        const r = await fetch('/api/ping', { method: 'POST' });
        const d = await r.json();
        setStatus(d.ok ? 'ESP32 responded (PONG).' : 'No response from ESP32.');
        log(d.ok ? 'PONG received!' : (d.error || d.message || 'Timeout'));
      } catch (err) {
        setStatus('Error: ' + err.message);
      }
    }

    /* ---- Repeat / Favorite ---- */

    async function onRepeat() {
      setStatus('Repeating last activity...');
      const r = await fetch('/api/trigger/repeat', { method: 'POST' });
      const d = await r.json();
      if (d.ok) {
        setStatus('Repeated: ' + (d.event_name || '') + (d.event_id ? ' (added to calendar)' : ''));
        log('Repeated "' + (d.event_name || '') + '"' + (d.event_id ? ' → event ' + d.event_id : ''));
      } else {
        setStatus(d.error || 'No previous activity');
        log('Repeat error: ' + (d.error || 'unknown'));
      }
    }

    async function onFavorite() {
      setStatus('Logging favorite...');
      const r = await fetch('/api/trigger/favorite', { method: 'POST' });
      const d = await r.json();
      if (d.ok) {
        setStatus('Favorite: ' + (d.event_name || '') + (d.event_id ? ' (added to calendar)' : ''));
        log('Favorite "' + (d.event_name || '') + '"' + (d.event_id ? ' → event ' + d.event_id : ''));
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
        connected = _ser is not None and _ser.is_open
    return jsonify({
        "serial_connected": connected,
        "last_activity": _last_activity,
    })


@app.route("/api/ping", methods=["POST"])
def api_ping():
    global _expecting_pong
    if not send_line("PING"):
        return jsonify({"ok": False, "error": "No serial connection"})
    _expecting_pong = True
    _pong_event.clear()
    ok = _pong_event.wait(timeout=3.0)
    _expecting_pong = False
    return jsonify({"ok": ok, "message": "PONG received" if ok else "Timeout"})


@app.route("/api/trigger/repeat", methods=["POST"])
def api_trigger_repeat():
    """Re-create the last activity as a new calendar event starting now."""
    if not _last_activity:
        return jsonify({"ok": False, "error": "No previous activity to repeat"})
    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    try:
        result = handle_create_event(
            _last_activity["event_name"],
            _last_activity["transcript"],
            dur,
        )
        return jsonify({"ok": result.get("ok"),
                        "event_name": _last_activity["event_name"],
                        "event_id": result.get("event_id", ""),
                        "error": result.get("error")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/trigger/favorite", methods=["POST"])
def api_trigger_favorite():
    """Create a calendar event using the favorite name/desc from settings."""
    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    name = s.get("favorite_name", "Focus Work")
    desc = s.get("favorite_desc", "")
    try:
        result = handle_create_event(name, desc, dur)
        return jsonify({"ok": result.get("ok"),
                        "event_name": name,
                        "event_id": result.get("event_id", ""),
                        "error": result.get("error")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Echo pipeline
# ---------------------------------------------------------------------------


@app.route("/api/record/send_to_esp32", methods=["POST"])
def api_record_send_to_esp32():
    """Record → echo → transcribe → interpret → create calendar event."""
    global _expecting_echo, _echo_audio, _echo_mime, _last_activity

    from datetime import datetime, timedelta

    f = request.files.get("audio")
    if not f:
        return jsonify({"ok": False, "error": "No audio file"}), 400
    audio_bytes = f.read()
    if not audio_bytes:
        return jsonify({"ok": False, "error": "Empty audio"}), 400

    # Parse the recording start time sent by the browser
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
    local = False

    _echo_audio = b""
    _echo_mime = mime
    _echo_event.clear()
    _expecting_echo = True

    if not send_audio_to_esp32(audio_bytes):
        _expecting_echo = False
        _echo_audio = audio_bytes
        _echo_mime = mime
        local = True
        print(f"[Echo] No ESP32, stored {len(audio_bytes)} bytes locally")
    else:
        if not _echo_event.wait(timeout=30):
            _expecting_echo = False
            return jsonify({"ok": False, "error": "Timeout waiting for ESP32 echo (30s)"})

    # --- STT ---
    audio_for_stt = _echo_audio
    print(f"[STT] Transcribing {len(audio_for_stt)} bytes ({mime})...")
    tr = handle_transcribe_bytes(audio_for_stt, mime)
    if not tr.get("ok"):
        return jsonify({"ok": False, "local": local, "error": tr.get("error", "STT failed"),
                        "transcript": "", "event_name": ""})

    transcript = tr.get("transcript", "")
    if not transcript:
        return jsonify({"ok": True, "local": local, "transcript": "",
                        "event_name": "", "category": "",
                        "message": "No speech detected"})

    # --- LLM interpret ---
    print(f"[LLM] Interpreting: {transcript[:80]}")
    interp = handle_interpret(transcript)
    event_name = interp.get("event_name", transcript[:40])
    category = interp.get("category", "other")

    _last_activity = {"event_name": event_name, "transcript": transcript}

    # --- Create Google Calendar event starting at recording time ---
    s = load()
    dur = s.get("event_duration", DEFAULTS["event_duration"])
    print(f"[Cal] Creating event '{event_name}' at {record_start.isoformat()} ({dur} min)")
    cal = handle_create_event(event_name, transcript, dur, start=record_start)

    result = {
        "ok": True,
        "local": local,
        "transcript": transcript,
        "event_name": event_name,
        "category": category,
    }
    if cal.get("ok"):
        result["event_id"] = cal["event_id"]
        print(f"[Cal] Created event {cal['event_id']}")
    else:
        result["cal_error"] = cal.get("error", "Calendar failed")
        print(f"[Cal] Error: {result['cal_error']}")

    return jsonify(result)


@app.route("/api/audio/last")
def api_audio_last():
    if not _echo_audio:
        return Response("No audio stored", status=404)
    return Response(_echo_audio, mimetype=_echo_mime or "audio/webm",
                    headers={"Cache-Control": "no-store"})


@app.route("/debug")
def debug_redirect():
    return redirect("/")


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

    print(f"[Info] Web UI: http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
