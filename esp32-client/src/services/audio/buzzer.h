/**
 * Buzzer output for prompt notification and status feedback.
 */

#ifndef BUZZER_H
#define BUZZER_H

#include <Arduino.h>

class Buzzer {
public:
    explicit Buzzer(int pin);

    void begin();

    /// Short beep to prompt user for input.
    void prompt();

    /// Quick double-beep for success.
    void success();

    /// Low tone for error.
    void error();

    /// Custom tone.
    void tone(int freqHz, int durationMs);

private:
    int _pin;
};

#endif
