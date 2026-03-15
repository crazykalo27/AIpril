/**
 * Button handler implementation with debounce.
 *
 * Reads actual pin state on begin() so the first update() doesn't
 * see a phantom HIGH→LOW transition (fixes spurious favorite on boot).
 */

#include "button_handler.h"

ButtonHandler::ButtonHandler(int voicePin, int repeatPin, int favoritePin)
    : _voice{}, _repeat{}, _favorite{} {
    _voice.pin = voicePin;
    _repeat.pin = repeatPin;
    _favorite.pin = favoritePin;
}

void ButtonHandler::begin() {
    pinMode(_voice.pin,    INPUT_PULLUP);
    pinMode(_repeat.pin,   INPUT_PULLUP);
    pinMode(_favorite.pin, INPUT_PULLUP);

    delay(10);

    _voice.lastState    = digitalRead(_voice.pin);
    _repeat.lastState   = digitalRead(_repeat.pin);
    _favorite.lastState = digitalRead(_favorite.pin);

    Serial.printf("[Btn] voice(GPIO%d)=%s repeat(GPIO%d)=%s fav(GPIO%d)=%s\n",
        _voice.pin,    _voice.lastState    ? "HIGH" : "LOW",
        _repeat.pin,   _repeat.lastState   ? "HIGH" : "LOW",
        _favorite.pin, _favorite.lastState ? "HIGH" : "LOW");

    unsigned long now = millis();
    _voice.lastChange    = now;
    _repeat.lastChange   = now;
    _favorite.lastChange = now;
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
            Serial.printf("[Btn] GPIO%d pressed\n", btn.pin);
        } else {
            Serial.printf("[Btn] GPIO%d released\n", btn.pin);
        }
    }
}
