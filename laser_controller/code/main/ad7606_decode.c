#include "ad7606_decode.h"

static int16_t decode_twos_complement(uint16_t word)
{
    const int32_t signed_value = word >= 0x8000U
        ? (int32_t)word - 65536
        : (int32_t)word;
    return (int16_t)signed_value;
}

void ad7606_decode_douta_frame(
    const uint8_t raw[AD7606_DOUTA_FRAME_BYTES],
    ad7606_sample_t *sample
)
{
    for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
        const size_t offset = channel * 2U;
        const uint16_t word = ((uint16_t)raw[offset] << 8U) | raw[offset + 1U];
        sample->counts[channel] = decode_twos_complement(word);
    }
}

double ad7606_counts_to_volts(int16_t counts)
{
    return (double)counts * AD7606_VOLTS_PER_LSB;
}
