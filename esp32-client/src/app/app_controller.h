/**
 * Application controller — top-level orchestrator.
 *
 * Uses HttpClient to communicate with server over WiFi.
 * Runs a tiny HTTP server for server→ESP32 commands (ping, etc.).
 * Serial is for debug output only.
 */

#ifndef APP_CONTROLLER_H
#define APP_CONTROLLER_H

#include <WebServer.h>
#include "config/config.h"
#include "infrastructure/storage/nvs_store.h"
#include "infrastructure/wifi/http_client.h"
#include "services/audio/i2s_recorder.h"
#include "services/audio/buzzer.h"
#include "services/input/button_handler.h"
#include "services/prompt/prompt_scheduler.h"
#include "services/calendar/reclaim_detector.h"
#include "services/calendar/schedule_builder.h"

class AppController {
public:
    AppController();

    void begin();
    void update();

    void handleVoiceCapture();
    void handleRepeat();
    void handleFavorite();

private:
    void handleSerial();
    void setupWebServer();
    void pingBeep();

    NvsStore        _store;
    HttpClient      _http;
    I2SRecorder     _recorder;
    Buzzer          _buzzer;
    ButtonHandler   _buttons;
    PromptScheduler _scheduler;
    ReclaimDetector _reclaimDetector;
    ScheduleBuilder _scheduleBuilder;
    WebServer       _webServer;

    String _lastEventName;
    bool   _hasLastActivity = false;

    bool _remoteRecording = false;
    bool _remoteLastState = HIGH;
    unsigned long _remoteLastChange = 0;
    void updateRemoteButton();
};

#endif
