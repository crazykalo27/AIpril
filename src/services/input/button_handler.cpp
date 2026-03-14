/**
 * Button handler implementation with debounce.
 */

#include "button_handler.h"

ButtonHandler::ButtonHandler(int voicePin, int repeatPin, int favoritePin)
    : _voice{voicePin}, _repeat{repeatPin}, _favorite{favoritePin} {}

void ButtonHandler::begin() {
    pinMode(_voice.pin,    INPUT_PULLUP);
    pinMode(_repeat.pin,   INPUT_PULLUP);
    pinMode(_favorite.pin, INPUT_PULLUP);
}

void ButtonHandler::update() {
    readButton(_voice);
    readButton(_repeat);
    readButton(_favorite);
}

bool ButtonHandler::wasVoicePressed() {
    bool p = _voice.pressed;
    _voice.pressed = false;
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
