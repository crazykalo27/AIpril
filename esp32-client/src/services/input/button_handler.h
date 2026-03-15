/**
 * Physical button handler with debounce.
 *
 * Tracks three buttons: voice, repeat, favorite.
 * Call update() in loop(), then check wasXxxPressed().
 */

#ifndef BUTTON_HANDLER_H
#define BUTTON_HANDLER_H

#include <Arduino.h>

class ButtonHandler {
public:
    ButtonHandler(int voicePin, int repeatPin, int favoritePin);

    void begin();

    /// Call every loop iteration. Reads pins and debounces.
    void update();

    /// True once per press (cleared after read).
    bool wasVoicePressed();
    bool wasRepeatPressed();
    bool wasFavoritePressed();

private:
    struct Button {
        int  pin = 0;
        bool lastState     = HIGH;
        bool pressed       = false;
        unsigned long lastChange = 0;
    };

    static const unsigned long DEBOUNCE_MS = 50;

    void readButton(Button& btn);

    Button _voice;
    Button _repeat;
    Button _favorite;
};

#endif
