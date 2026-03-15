/**
 * AIpril — ESP32 firmware entry point.
 *
 * Records voice, transcribes via OpenAI, creates Google Calendar events.
 */

#include <Arduino.h>
#include "app/app_controller.h"

AppController app;

void setup() {
    Serial.setRxBufferSize(4096);
    Serial.begin(115200);
    delay(1000);
    app.begin();
}

void loop() {
    app.update();
}
