/**
 * WiFi connection manager.
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>

class WifiManager {
public:
    /// Connect to the configured WiFi network. Blocks until connected or timeout.
    bool connect(const char* ssid, const char* password, int timeoutSec = 15);

    bool isConnected() const;
};

#endif
