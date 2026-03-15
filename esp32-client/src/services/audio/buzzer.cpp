/**
 * Buzzer implementation using ledcWrite (ESP32 PWM).
 */

#include "buzzer.h"
#include "config/config.h"

#define BUZZER_CHANNEL 0

Buzzer::Buzzer(int pin) : _pin(pin) {}

void Buzzer::begin() {
    ledcSetup(BUZZER_CHANNEL, 2000, 8);
    ledcAttachPin(_pin, BUZZER_CHANNEL);
    ledcWrite(BUZZER_CHANNEL, 0);
}

void Buzzer::prompt() {
    tone(TONE_PROMPT_HZ, TONE_PROMPT_MS);
}

void Buzzer::success() {
    tone(TONE_SUCCESS_HZ, TONE_SUCCESS_MS);
    delay(80);
    tone(TONE_SUCCESS_HZ, TONE_SUCCESS_MS);
}

void Buzzer::error() {
    tone(TONE_ERROR_HZ, TONE_ERROR_MS);
}

void Buzzer::tone(int freqHz, int durationMs) {
    ledcWriteTone(BUZZER_CHANNEL, freqHz);
    delay(durationMs);
    ledcWriteTone(BUZZER_CHANNEL, 0);
}
