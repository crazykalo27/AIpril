/**
 * Central application configuration.
 *
 * Compile-time defaults. Runtime overrides stored in NVS.
 */

#ifndef CONFIG_H
#define CONFIG_H

#include "pins.h"
#include "secrets.h"

// --- Audio ---
#define AUDIO_SAMPLE_RATE      16000
#define AUDIO_BITS_PER_SAMPLE  16
#define AUDIO_CHANNELS         1
#define AUDIO_RECORD_SECONDS   5

// --- Prompt scheduler ---
#define PROMPT_INTERVAL_MS     (15 * 60 * 1000)  // 15 minutes

// --- Reclaim detection ---
#define RECLAIM_TAG            "[reclaim]"

// --- API hosts ---
#define OPENAI_HOST            "api.openai.com"
#define OPENAI_TRANSCRIBE_PATH "/v1/audio/transcriptions"
#define OPENAI_CHAT_PATH       "/v1/chat/completions"
#define OPENAI_TRANSCRIBE_MODEL "gpt-4o-transcribe"
#define OPENAI_CHAT_MODEL       "gpt-4o-mini"

#define GOOGLE_TOKEN_HOST      "oauth2.googleapis.com"
#define GOOGLE_TOKEN_PATH      "/token"
#define GOOGLE_CALENDAR_HOST   "www.googleapis.com"
#define GOOGLE_CALENDAR_BASE   "/calendar/v3/calendars/primary/events"

// --- NTP time sync ---
#define NTP_SERVER             "pool.ntp.org"
#define NTP_GMT_OFFSET         0     // UTC
#define NTP_DAYLIGHT_OFFSET    0

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
