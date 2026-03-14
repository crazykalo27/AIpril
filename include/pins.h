/**
 * Hardware pin assignments.
 * Edit for your specific wiring.
 */

#ifndef PINS_H
#define PINS_H

// --- I2S Microphone (INMP441) ---
#define PIN_I2S_BCLK    26
#define PIN_I2S_LRCK    25
#define PIN_I2S_DIN     33

// --- Buzzer ---
#define PIN_BUZZER      27

// --- Buttons ---
#define PIN_BTN_VOICE     0   // BOOT button on most ESP32 boards
#define PIN_BTN_REPEAT   32
#define PIN_BTN_FAVORITE 35

// --- Status LED (optional) ---
#define PIN_LED          2    // Built-in LED on most boards

#endif
