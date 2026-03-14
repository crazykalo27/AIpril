/**
 * WiFi manager implementation.
 */

#include "wifi_manager.h"
#include <WiFi.h>

bool WifiManager::connect(const char* ssid, const char* password, int timeoutSec) {
    Serial.printf("[WiFi] Connecting to %s", ssid);
    WiFi.begin(ssid, password);

    int elapsed = 0;
    while (WiFi.status() != WL_CONNECTED && elapsed < timeoutSec) {
        delay(1000);
        Serial.print(".");
        elapsed++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WiFi] Connected — IP: %s\n", WiFi.localIP().toString().c_str());
        return true;
    }

    Serial.println("\n[WiFi] Connection failed");
    return false;
}

bool WifiManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED;
}
