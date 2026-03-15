/**
 * AIpril — ESP32 firmware entry point.
 *
 * Connects to WiFi and communicates with server over HTTP.
 * Serial is kept for debug output.
 */

#include <Arduino.h>
#include <WiFi.h>
#include "secrets.h"
#include "app/app_controller.h"

AppController app;

void connectWiFi() {
    Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WiFi] Connected — IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WiFi] FAILED to connect. Check SSID/password in secrets.h");
    }
}

void setup() {
    Serial.setRxBufferSize(4096);
    Serial.begin(115200);
    delay(1000);

    connectWiFi();
    app.begin();
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Reconnecting...");
        connectWiFi();
    }
    app.update();
}
