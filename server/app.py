"""
AIpril server — web UI + serial bridge.

Web UI at http://localhost:5000 for settings and audio echo testing.
Serial listener runs in background for ESP32 (use --no-serial to skip).

Echo pipeline: browser records → server sends bytes to ESP32 → ESP32 echoes
back → server stores audio → browser plays /api/audio/last.
"""

import base64
import json
import sys
import threading
import time

import serial
from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for

from config import SERIAL_PORT, SERIAL_BAUD
from handlers import (
    handle_transcribe,
    handle_interpret,
    handle_create_event,
    handle_create_favorite,
    handle_list_events,
)
from settings import load, save, get_interpret_prompt, DEFAULTS
from debug_handlers import debug_transcribe_from_file, debug_full_flow

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Shared state (accessed from HTTP handler threads + serial loop thread)
# ---------------------------------------------------------------------------

_ser: serial.Serial | None = None
_ser_lock = threading.Lock()

_last_activity: dict | None = None

# Echo pipeline state
_expecting_echo = False
_echo_audio: bytes = b""
_echo_mime: str = "audio/webm"
_echo_event = threading.Event()

# Ping state
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
    with _ser_lock:
        if not _ser or not _ser.is_open:
            return False
        header = f"AUDIO_PLAYBACK {len(audio_bytes)}\n"
        _ser.write(header.encode("utf-8"))
        _ser.write(audio_bytes)
        _ser.flush()
        print(f"[Echo] Sent AUDIO_PLAYBACK ({len(audio_bytes)} bytes) to ESP32")
    return True


# ---------------------------------------------------------------------------
# Serial protocol handlers
# ---------------------------------------------------------------------------


def send_response(ser: serial.Serial, obj: dict) -> None:
    ser.write((json.dumps(obj) + "\n").encode("utf-8"))


def process_audio_binary(ser: serial.Serial, line: str) -> None:
    """Handle 'AUDIO <len>' header from ESP32, read binary payload."""
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

    # Normal path: ESP32 recorded from mic, run transcription
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
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIpril</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.1rem; margin-top: 1.5rem; }
    label { display: block; margin-top: 1rem; font-weight: 500; }
    input, textarea { width: 100%; padding: 0.5rem; margin-top: 0.25rem; }
    textarea { min-height: 80px; }
    button { margin-top: 0.5rem; padding: 0.5rem 1rem; cursor: pointer; min-height: 44px;
             touch-action: manipulation; }
    .labels { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.25rem; }
    .labels input { width: auto; flex: 1; min-width: 120px; }
    .msg { margin-top: 0.5rem; padding: 0.5rem; background: #e8f5e9; border-radius: 4px; }
    .err { background: #ffebee; }
    .section { margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid #eee; }
    .section:last-of-type { border-bottom: none; }
    .btn-row { display: flex; gap: 0.5rem; margin: 1rem 0; flex-wrap: wrap; }
    .btn-record { background: #c62828; color: white; border: none; border-radius: 4px;
                  user-select: none; -webkit-user-select: none; }
    .btn-record.recording { background: #ff5252; animation: pulse 0.8s infinite alternate; }
    @keyframes pulse { from { opacity: 1; } to { opacity: 0.6; } }
    .btn-repeat { background: #1565c0; color: white; border: none; border-radius: 4px; }
    .btn-favorite { background: #2e7d32; color: white; border: none; border-radius: 4px; }
    .btn-default { background: #424242; color: white; border: none; border-radius: 4px; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    #status { font-size: 0.9rem; color: #666; margin: 0.25rem 0; }
    #result { margin-top: 0.5rem; padding: 1rem; background: #f5f5f5; border-radius: 4px;
              min-height: 40px; white-space: pre-wrap; }
    #result.empty { color: #999; }
    #log { margin-top: 0.5rem; padding: 1rem; background: #1e1e1e; color: #d4d4d4;
           font-family: monospace; font-size: 11px; max-height: 200px; overflow-y: auto;
           border-radius: 4px; white-space: pre-wrap; }
    #audioPlayer { margin-top: 0.5rem; width: 100%; }
  </style>
</head>
<body>
  <h1>AIpril</h1>

  <div class="section">
    <h2>Audio Echo Test</h2>
    <p id="status">{{ conn_status }}</p>

    <div class="btn-row">
      <button type="button" id="pingBtn" class="btn-default">Ping ESP32</button>
      <button type="button" id="recordBtn" class="btn-record">Hold to Record</button>
      <button type="button" id="repeatBtn" class="btn-repeat">Repeat</button>
      <button type="button" id="favoriteBtn" class="btn-favorite">Favorite</button>
    </div>

    <div id="result" class="empty">
      Record audio, send to ESP32, hear the echo.
    </div>

    <audio id="audioPlayer" controls style="display:none;"></audio>

    <h3>Log</h3>
    <div id="log">&mdash;</div>
  </div>

  <div class="section">
    <h2>Settings</h2>
    <form id="form" method="POST" action="/api/settings">
      <label>Favorite event name</label>
      <input name="favorite_name" value="{{ favorite_name }}" placeholder="Focus Work">
      <label>Favorite event description</label>
      <textarea name="favorite_desc" placeholder="Deep focus block">{{ favorite_desc }}</textarea>
      <label>Event labels (LLM matches transcript to these)</label>
      <div class="labels" id="labels">
        {% for l in event_labels %}
        <input type="text" name="label" value="{{ l }}">
        {% endfor %}
      </div>
      <button type="button" id="addLabelBtn">+ Add label</button>
      <button type="submit">Save</button>
    </form>
    <div id="msg"></div>
  </div>

  <script>
    let mediaRecorder = null;
    let audioChunks = [];

    const $ = id => document.getElementById(id);
    const log = msg => { $('log').textContent += '\\n' + msg; $('log').scrollTop = $('log').scrollHeight; };
    const setStatus = msg => $('result').textContent = msg;

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

      setStatus('Sending to ESP32 for echo...');

      try {
        const r = await fetch('/api/record/send_to_esp32', { method: 'POST', body: fd });
        const data = await r.json();

        if (data.ok) {
          log(data.local ? 'No ESP32 — stored locally.' : 'ESP32 echoed ' + (data.bytes || '?') + ' bytes.');
          setStatus('Playing back echoed audio...');
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
      const r = await fetch('/api/trigger/repeat', { method: 'POST' });
      const d = await r.json();
      setStatus(d.ok ? ('Repeated: ' + (d.event_name || '')) : (d.error || 'No previous activity'));
      log(JSON.stringify(d));
    }

    async function onFavorite() {
      const r = await fetch('/api/trigger/favorite', { method: 'POST' });
      const d = await r.json();
      setStatus(d.ok ? 'Favorite logged.' : (d.error || 'Error'));
      log(JSON.stringify(d));
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
          event_labels: labels.length ? labels : ['Focus Work', 'Meeting', 'Break']
        };
        const r = await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await r.json();
        $('msg').textContent = data.ok ? 'Saved.' : (data.error || 'Error');
        $('msg').className = data.ok ? 'msg' : 'msg err';
      });
    }

    /* ---- Init ---- */

    function init() {
      initForm();
      $('addLabelBtn')?.addEventListener('click', () => {
        const inp = document.createElement('input');
        inp.type = 'text'; inp.name = 'label'; inp.placeholder = 'New label';
        $('labels').appendChild(inp);
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
        event_labels=labels,
        conn_status=conn,
    )
    resp = app.make_response(resp)
    resp.headers["Cache-Control"] = "no-store"
    return resp


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
    sent = send_line("trigger_repeat")
    if sent:
        return jsonify({"sent": True, "ok": True, "message": "Trigger sent to ESP32"})
    if not _last_activity:
        return jsonify({"sent": False, "ok": False, "error": "No previous activity to repeat"})
    try:
        result = handle_create_event(
            _last_activity["event_name"],
            _last_activity["transcript"],
            30,
        )
        return jsonify({"sent": False, "ok": result.get("ok"),
                        "event_name": _last_activity["event_name"],
                        "error": result.get("error")})
    except Exception as e:
        return jsonify({"sent": False, "ok": False, "error": str(e)})


@app.route("/api/trigger/favorite", methods=["POST"])
def api_trigger_favorite():
    sent = send_line("trigger_favorite")
    if sent:
        return jsonify({"sent": True, "ok": True, "message": "Trigger sent to ESP32"})
    try:
        result = handle_create_favorite(30)
        return jsonify({"sent": False, "ok": result.get("ok"), "error": result.get("error")})
    except Exception as e:
        return jsonify({"sent": False, "ok": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Echo pipeline: browser → ESP32 → browser
# ---------------------------------------------------------------------------


@app.route("/api/record/send_to_esp32", methods=["POST"])
def api_record_send_to_esp32():
    """Receive audio from browser. Send to ESP32, wait for echo. Store result for playback."""
    global _expecting_echo, _echo_audio, _echo_mime

    f = request.files.get("audio")
    if not f:
        return jsonify({"ok": False, "error": "No audio file"}), 400
    audio_bytes = f.read()
    if not audio_bytes:
        return jsonify({"ok": False, "error": "Empty audio"}), 400

    mime = f.content_type or "audio/webm"

    # Prepare echo state BEFORE sending so serial thread sees the flag
    _echo_audio = b""
    _echo_mime = mime
    _echo_event.clear()
    _expecting_echo = True

    if not send_audio_to_esp32(audio_bytes):
        # No ESP32 — store the recording directly for local playback
        _expecting_echo = False
        _echo_audio = audio_bytes
        _echo_mime = mime
        print(f"[Echo] No ESP32, stored {len(audio_bytes)} bytes locally")
        return jsonify({"ok": True, "local": True, "bytes": len(audio_bytes)})

    # Wait for ESP32 to echo the audio back
    if not _echo_event.wait(timeout=30):
        _expecting_echo = False
        return jsonify({"ok": False, "error": "Timeout waiting for ESP32 echo (30s)"})

    return jsonify({"ok": True, "local": False, "bytes": len(_echo_audio)})


@app.route("/api/audio/last")
def api_audio_last():
    """Serve the last echoed (or locally stored) audio for browser playback."""
    if not _echo_audio:
        return Response("No audio stored", status=404)
    return Response(_echo_audio, mimetype=_echo_mime or "audio/webm",
                    headers={"Cache-Control": "no-store"})


# Keep /debug redirect for backwards compat
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
