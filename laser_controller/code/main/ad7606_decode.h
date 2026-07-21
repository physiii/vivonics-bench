#ifndef VIVONICS_AD7606_DECODE_H
#define VIVONICS_AD7606_DECODE_H

#include <stddef.h>
#include <stdint.h>

#define AD7606_CHANNEL_COUNT 4U
#define AD7606_DOUTA_FRAME_BYTES 8U
#define AD7606_INPUT_SPAN_VOLTS 10.0
#define AD7606_CODE_COUNT 65536.0
#define AD7606_VOLTS_PER_LSB (AD7606_INPUT_SPAN_VOLTS / AD7606_CODE_COUNT)

typedef struct {
    int16_t counts[AD7606_CHANNEL_COUNT];
} ad7606_sample_t;

void ad7606_decode_douta_frame(
    const uint8_t raw[AD7606_DOUTA_FRAME_BYTES],
    ad7606_sample_t *sample
);

double ad7606_counts_to_volts(int16_t counts);

#endif
