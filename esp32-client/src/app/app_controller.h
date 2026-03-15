/**
 * Application controller — top-level orchestrator.
 *
 * Owns all services. Exposes high-level actions called from main loop.
 * Equivalent to the Python ServiceContainer + orchestrators.
 */

#ifndef APP_CONTROLLER_H
#define APP_CONTROLLER_H

#include "config/config.h"
#include "infrastructure/storage/nvs_store.h"
#include "infrastructure/wire/wire_client.h"
#include "services/audio/i2s_recorder.h"
#include "services/audio/buzzer.h"
#include "services/input/button_handler.h"
#include "services/prompt/prompt_scheduler.h"
#include "services/calendar/reclaim_detector.h"
#include "services/calendar/schedule_builder.h"

class AppController {
public:
    AppController();

    /// Initialize all subsystems. Call once in setup().
    void begin();

    /// Run one loop iteration. Call in loop().
    void update();

    /// Process serial commands.
    void handleSerial();

    // --- High-level actions (callable from loop or serial) ---

    /// MVP: Record audio → transcribe (via server) → interpret (via server) → create calendar event (via server).
    void handleVoiceCapture();

    /// Repeat button: re-log the last activity.
    void handleRepeat();

    /// Favorite button: log a saved favorite.
    void handleFavorite();

    /// Receive audio from server (browser hold-to-record), echo back as if ESP32 recorded it.
    void handleAudioPlayback(const String& line);

    /// Send stored audio back (retrieve most recent).
    void handleRetrieveLast();

private:
    // Subsystems
    NvsStore        _store;
    WireClient      _wire;
    I2SRecorder     _recorder;
    Buzzer          _buzzer;
    ButtonHandler   _buttons;
    PromptScheduler _scheduler;
    ReclaimDetector _reclaimDetector;
    ScheduleBuilder _scheduleBuilder;

    // State
    InterpretedActivity _lastActivity;
    bool                _hasLastActivity = false;

    // Last received audio (from AUDIO_PLAYBACK) for retrieve
    static const size_t  _storedAudioMax = 128 * 1024;  // 128KB
    uint8_t*            _storedAudio = nullptr;
    size_t              _storedAudioLen = 0;
};

#endif
