/**
 * Button handler implementation with debounce.
 *
 * Reads actual pin state on begin() so the first update() doesn't
 * see a phantom HIGH→LOW transition (fixes spurious favorite on boot).
 */

#include "button_handler.h"

ButtonHandler::ButtonHandler(int voicePin, int voice2Pin, int repeatPin, int favoritePin)
    : _voice{}, _voice2{}, _repeat{}, _favorite{} {
    _voice.pin = voicePin;
    _voice2.pin = voice2Pin;
    _repeat.pin = repeatPin;
    _favorite.pin = favoritePin;
}

void ButtonHandler::begin() {
    pinMode(_voice.pin,    INPUT_PULLUP);
    pinMode(_voice2.pin,   INPUT_PULLUP);
    pinMode(_repeat.pin,   INPUT_PULLUP);
    pinMode(_favorite.pin, INPUT_PULLUP);

    delay(10);

    _voice.lastState    = digitalRead(_voice.pin);
    _voice2.lastState   = digitalRead(_voice2.pin);
    _repeat.lastState   = digitalRead(_repeat.pin);
    _favorite.lastState = digitalRead(_favorite.pin);

    unsigned long now = millis();
    _voice.lastChange    = now;
    _voice2.lastChange   = now;
    _repeat.lastChange   = now;
    _favorite.lastChange = now;
}

void ButtonHandler::update() {
    readButton(_voice);
    readButton(_voice2);
    readButton(_repeat);
    readButton(_favorite);
}

bool ButtonHandler::wasVoicePressed() {
    bool p = _voice.pressed || _voice2.pressed;
    _voice.pressed = false;
    _voice2.pressed = false;
    return p;
}

bool ButtonHandler::wasRepeatPressed() {
    bool p = _repeat.pressed;
    _repeat.pressed = false;
    return p;
}

bool ButtonHandler::wasFavoritePressed() {
    bool p = _favorite.pressed;
    _favorite.pressed = false;
    return p;
}

void ButtonHandler::readButton(Button& btn) {
    bool state = digitalRead(btn.pin);
    if (state != btn.lastState && (millis() - btn.lastChange) > DEBOUNCE_MS) {
        btn.lastChange = millis();
        btn.lastState = state;
        if (state == LOW) {
            btn.pressed = true;
        }
    }
}
