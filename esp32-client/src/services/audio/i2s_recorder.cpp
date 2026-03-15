/**
 * I2S recorder implementation.
 */

#include "i2s_recorder.h"
#include "config/config.h"
#include <driver/i2s.h>

#define WAV_HEADER_SIZE 44

bool I2SRecorder::begin(int sampleRate, int bclk, int lrck, int din) {
    _sampleRate = sampleRate;

    _bufSize = WAV_HEADER_SIZE + (sampleRate * AUDIO_RECORD_SECONDS * 2);

    // Prefer PSRAM if available
    #if defined(BOARD_HAS_PSRAM) || defined(CONFIG_SPIRAM)
    _buffer = (uint8_t*)ps_malloc(_bufSize);
    #else
    _buffer = (uint8_t*)malloc(_bufSize);
    #endif

    if (!_buffer) {
        Serial.println("[I2S] Buffer allocation failed");
        return false;
    }

    i2s_config_t cfg = {
        .mode             = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate      = (uint32_t)sampleRate,
        .bits_per_sample  = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format   = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = 0,
        .dma_buf_count    = 8,
        .dma_buf_len      = 1024,
        .use_apll         = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk       = 0
    };

    i2s_pin_config_t pins = {
        .bck_io_num   = bclk,
        .ws_io_num    = lrck,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num  = din
    };

    if (i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL) != ESP_OK) {
        Serial.println("[I2S] Driver install failed");
        return false;
    }
    i2s_set_pin(I2S_NUM_0, &pins);
    i2s_zero_dma_buffer(I2S_NUM_0);

    Serial.printf("[I2S] Initialized at %d Hz\n", sampleRate);
    return true;
}

size_t I2SRecorder::record(int seconds) {
    if (!_buffer) return 0;

    size_t toRead = (size_t)_sampleRate * seconds * 2;
    size_t maxData = _bufSize - WAV_HEADER_SIZE;
    if (toRead > maxData) toRead = maxData;

    Serial.printf("[I2S] Recording %d seconds...\n", seconds);
    size_t bytesRead = 0;
    i2s_read(I2S_NUM_0, _buffer + WAV_HEADER_SIZE, toRead, &bytesRead,
             portMAX_DELAY);

    writeWavHeader(bytesRead);
    _totalLen = WAV_HEADER_SIZE + bytesRead;

    Serial.printf("[I2S] Recorded %u bytes\n", _totalLen);
    return _totalLen;
}

void I2SRecorder::clear() {
    _totalLen = 0;
}

void I2SRecorder::writeWavHeader(size_t dataLen) {
    uint32_t fileSize = dataLen + 36;
    uint32_t byteRate = _sampleRate * 2;
    uint8_t* h = _buffer;

    h[0]='R'; h[1]='I'; h[2]='F'; h[3]='F';
    h[4]=fileSize; h[5]=fileSize>>8; h[6]=fileSize>>16; h[7]=fileSize>>24;
    h[8]='W'; h[9]='A'; h[10]='V'; h[11]='E';
    h[12]='f'; h[13]='m'; h[14]='t'; h[15]=' ';
    h[16]=16; h[17]=0; h[18]=0; h[19]=0;
    h[20]=1; h[21]=0;  // PCM
    h[22]=1; h[23]=0;  // Mono
    h[24]=_sampleRate; h[25]=_sampleRate>>8; h[26]=_sampleRate>>16; h[27]=_sampleRate>>24;
    h[28]=byteRate;    h[29]=byteRate>>8;    h[30]=byteRate>>16;    h[31]=byteRate>>24;
    h[32]=2; h[33]=0;  // Block align
    h[34]=16; h[35]=0; // Bits per sample
    h[36]='d'; h[37]='a'; h[38]='t'; h[39]='a';
    h[40]=dataLen; h[41]=dataLen>>8; h[42]=dataLen>>16; h[43]=dataLen>>24;
}
