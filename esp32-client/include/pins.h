/**
 * Hardware pin assignments.
 * Edit for your specific wiring.
 */

#ifndef PINS_H
#define PINS_H

// --- I2S Microphone (INMP441) ---
#define PIN_I2S_BCLK    26
#define PIN_I2S_LRCK    15   // Moved from 25 to free it for repeat button
#define PIN_I2S_DIN     34   // Input-only pin, fine for I2S data in

// --- Buzzer ---
#define PIN_BUZZER      27

// --- Ping speaker (PWM beep when server pings) ---
#define PIN_PING_SPEAKER  33

// --- Buttons ---
#define PIN_BTN_VOICE     0  // BOOT button on most ESP32 boards
#define PIN_BTN_REPEAT   25  // Pushbutton to GND (was 33)
#define PIN_BTN_FAVORITE 14

// --- LEDs ---
#define PIN_LED            2 // Built-in LED
#define PIN_LED_REPEAT    32 // Flashes on repeat

#endif
