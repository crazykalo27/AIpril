/**
 * Central application configuration.
 *
 * Compile-time defaults. Runtime overrides stored in NVS.
 */

#ifndef CONFIG_H
#define CONFIG_H

#include "pins.h"

// --- Audio ---
#define AUDIO_SAMPLE_RATE      16000
#define AUDIO_BITS_PER_SAMPLE  16
#define AUDIO_CHANNELS         1
#define AUDIO_RECORD_SECONDS   5

// --- Prompt scheduler ---
#define PROMPT_INTERVAL_MS     (15 * 60 * 1000)  // 15 minutes

// --- Reclaim detection ---
#define RECLAIM_TAG            "[reclaim]"

// --- Buzzer tones ---
#define TONE_PROMPT_HZ         1000
#define TONE_PROMPT_MS         200
#define TONE_SUCCESS_HZ        2000
#define TONE_SUCCESS_MS        100
#define TONE_ERROR_HZ          400
#define TONE_ERROR_MS          500

// --- NVS namespace ---
#define NVS_NAMESPACE          "aipril"

#endif
