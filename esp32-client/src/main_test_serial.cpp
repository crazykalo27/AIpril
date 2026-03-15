/**
 * Minimal serial test — send "hi", ESP32 replies "hello".
 * Use: pio run -e test -t upload
 */

#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("ESP32 ready — send 'hi' to get 'hello'");
}

void loop() {
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line == "hi") {
            Serial.println("hello");
        }
    }
    delay(10);
}
