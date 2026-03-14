/**
 * Application controller — top-level orchestrator.
 *
 * Owns all services. Exposes high-level actions called from main loop.
 * Equivalent to the Python ServiceContainer + orchestrators.
 */

#ifndef APP_CONTROLLER_H
#define APP_CONTROLLER_H

#include "config/config.h"
#include "config/wifi_manager.h"
#include "infrastructure/storage/nvs_store.h"
#include "infrastructure/network/https_client.h"
#include "infrastructure/google/google_auth.h"
#include "infrastructure/google/google_calendar.h"
#include "infrastructure/openai/openai_transcriber.h"
#include "infrastructure/openai/openai_interpreter.h"
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

    /// Process serial commands (e.g. "set_token <refresh_token>").
    void handleSerial();

    // --- High-level actions (callable from loop or serial) ---

    /// MVP: Record audio → transcribe → interpret → create calendar event.
    void handleVoiceCapture();

    /// Repeat button: re-log the last activity.
    void handleRepeat();

    /// Favorite button: log a saved favorite.
    void handleFavorite();

private:
    // Subsystems
    NvsStore          _store;
    HttpsClient       _http;
    WifiManager       _wifi;
    GoogleAuth        _googleAuth;
    GoogleCalendar    _calendar;
    OpenAITranscriber _transcriber;
    OpenAIInterpreter _interpreter;
    I2SRecorder       _recorder;
    Buzzer            _buzzer;
    ButtonHandler     _buttons;
    PromptScheduler   _scheduler;
    ReclaimDetector   _reclaimDetector;
    ScheduleBuilder   _scheduleBuilder;

    // State
    InterpretedActivity _lastActivity;
    bool                _hasLastActivity = false;
};

#endif
