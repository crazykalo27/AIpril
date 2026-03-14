/**
 * I2S microphone recorder (INMP441).
 *
 * Records audio to an internal WAV buffer.
 * 16-bit mono PCM at configurable sample rate.
 */

#ifndef I2S_RECORDER_H
#define I2S_RECORDER_H

#include <Arduino.h>

class I2SRecorder {
public:
    /// Allocate buffer and configure I2S driver.
    bool begin(int sampleRate, int bclk, int lrck, int din);

    /// Record for the given number of seconds.
    /// Returns total bytes (WAV header + PCM data), or 0 on failure.
    size_t record(int seconds);

    /// Pointer to the WAV buffer (header + data).
    uint8_t* getBuffer() const { return _buffer; }

    /// Total length of last recording (header + data).
    size_t getLength() const { return _totalLen; }

    /// Reset recorded data length.
    void clear();

private:
    void writeWavHeader(size_t dataLen);

    uint8_t* _buffer   = nullptr;
    size_t   _bufSize  = 0;
    size_t   _totalLen = 0;
    int      _sampleRate = 16000;
};

#endif
