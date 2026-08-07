#include <assert.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "ad7606_decode.h"
#include "laser_control_watchdog.h"
#include "laser_safety.h"
#include "laser_test_protocol.h"

static void encode_word(uint8_t raw[AD7606_DOUTA_FRAME_BYTES], size_t channel, int16_t value)
{
    const uint16_t word = (uint16_t)value;
    raw[channel * 2U] = (uint8_t)(word >> 8U);
    raw[channel * 2U + 1U] = (uint8_t)(word & 0xffU);
}

static void test_known_decode_vector(void)
{
    uint8_t raw[AD7606_DOUTA_FRAME_BYTES] = {0};
    const int16_t expected[AD7606_CHANNEL_COUNT] = {3277, 6554, -3277, -6554};
    for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
        encode_word(raw, channel, expected[channel]);
    }

    ad7606_sample_t sample = {0};
    ad7606_decode_douta_frame(raw, &sample);
    for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
        assert(sample.counts[channel] == expected[channel]);
    }
}

static void test_decode_boundaries(void)
{
    uint8_t raw[AD7606_DOUTA_FRAME_BYTES] = {0};
    const int16_t expected[AD7606_CHANNEL_COUNT] = {0, INT16_MAX, INT16_MIN, -1};
    for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
        encode_word(raw, channel, expected[channel]);
    }

    ad7606_sample_t sample = {0};
    ad7606_decode_douta_frame(raw, &sample);
    for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
        assert(sample.counts[channel] == expected[channel]);
    }
    assert(fabs(ad7606_counts_to_volts(0)) < 1e-15);
    assert(fabs(ad7606_counts_to_volts(32767) - 4.999847412109375) < 1e-12);
    assert(fabs(ad7606_counts_to_volts(-32768) + 5.0) < 1e-12);
}

static uint32_t next_random(uint32_t *state)
{
    uint32_t value = *state;
    value ^= value << 13U;
    value ^= value >> 17U;
    value ^= value << 5U;
    *state = value;
    return value;
}

static void test_decode_round_trip_property(void)
{
    uint32_t random_state = 0x5a17c3e1U;
    for (size_t iteration = 0; iteration < 100000U; ++iteration) {
        uint8_t raw[AD7606_DOUTA_FRAME_BYTES] = {0};
        int16_t expected[AD7606_CHANNEL_COUNT] = {0};
        for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
            expected[channel] = (int16_t)(uint16_t)next_random(&random_state);
            encode_word(raw, channel, expected[channel]);
        }

        ad7606_sample_t sample = {0};
        ad7606_decode_douta_frame(raw, &sample);
        for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
            assert(sample.counts[channel] == expected[channel]);
        }
    }
}

static void test_safety_state_machine(void)
{
    laser_safety_t safety;
    laser_safety_init(&safety);
    assert(safety.state == LASER_STATE_BOOT_SAFE);
    assert(!laser_safety_outputs_permitted(&safety));
    assert(!laser_safety_request_arm(&safety, true, true));

    assert(laser_safety_mark_adc_ready(&safety));
    assert(!laser_safety_outputs_permitted(&safety));
    assert(!laser_safety_request_arm(&safety, false, true));
    assert(!laser_safety_request_arm(&safety, true, false));
    assert(laser_safety_request_arm(&safety, true, true));
    assert(laser_safety_outputs_permitted(&safety));
    assert(laser_safety_start_run(&safety));
    assert(laser_safety_outputs_permitted(&safety));

    laser_safety_disarm(&safety);
    assert(safety.state == LASER_STATE_ADC_READY_LASERS_INHIBITED);
    assert(!laser_safety_outputs_permitted(&safety));
}

static void test_active_output_watchdog(void)
{
    const int64_t maximum_age_us = 500000;
    assert(!laser_control_watchdog_expired(false, 100, 1000000, maximum_age_us));
    assert(!laser_control_watchdog_expired(true, 100, 500100, maximum_age_us));
    assert(laser_control_watchdog_expired(true, 100, 500101, maximum_age_us));
    assert(!laser_control_watchdog_expired(true, -1, 1000000, maximum_age_us));
    assert(!laser_control_watchdog_expired(true, 1000, 999, maximum_age_us));
    assert(!laser_control_watchdog_expired(true, 100, 1000000, 0));
}

static void test_every_fault_is_latched(void)
{
    const laser_fault_t faults[] = {
        LASER_FAULT_ADC_INIT,
        LASER_FAULT_ADC_BUSY_RISE_TIMEOUT,
        LASER_FAULT_ADC_BUSY_FALL_TIMEOUT,
        LASER_FAULT_ADC_SPI,
        LASER_FAULT_ADC_TIMING_OVERRUN,
        LASER_FAULT_WATCHDOG,
        LASER_FAULT_TELEMETRY_ADC,
        LASER_FAULT_OVERCURRENT,
        LASER_FAULT_PWM_OUTPUT,
        LASER_FAULT_WEB_INIT,
    };
    for (size_t index = 0; index < sizeof(faults) / sizeof(faults[0]); ++index) {
        laser_safety_t safety;
        laser_safety_init(&safety);
        assert(laser_safety_mark_adc_ready(&safety));
        assert(laser_safety_request_arm(&safety, true, true));
        laser_safety_latch_fault(&safety, faults[index]);
        assert(safety.state == LASER_STATE_FAULT_LATCHED);
        assert((safety.fault_mask & faults[index]) != 0U);
        assert(!laser_safety_outputs_permitted(&safety));
        assert(!laser_safety_request_arm(&safety, true, true));
        assert(!laser_safety_start_run(&safety));
        laser_safety_disarm(&safety);
        assert(safety.state == LASER_STATE_FAULT_LATCHED);
    }
}

static void test_laser_test_protocol(void)
{
    laser_test_command_t command = {0};
    assert(!laser_test_can_reconfigure_latched_output(true, true, NULL));
    assert(laser_test_parse_command("STATUS", &command));
    assert(command.type == LASER_TEST_COMMAND_STATUS);
    assert(!laser_test_can_reconfigure_latched_output(true, true, &command));
    assert(laser_test_parse_command(" OFF \r\n", &command));
    assert(command.type == LASER_TEST_COMMAND_OFF);
    assert(laser_test_parse_command("SENSETEST", &command));
    assert(command.type == LASER_TEST_COMMAND_SENSETEST);
    assert(laser_test_parse_command("SNAPSHOT", &command));
    assert(command.type == LASER_TEST_COMMAND_SNAPSHOT);
    assert(laser_test_parse_command("STREAM 25", &command));
    assert(command.type == LASER_TEST_COMMAND_STREAM);
    assert(command.stream_hz == 25);
    assert(laser_test_parse_command("STREAM 0", &command));
    assert(command.stream_hz == 0);
    assert(!laser_test_parse_command("STREAM 3", &command));
    assert(!laser_test_parse_command("STREAM 51", &command));

    assert(laser_test_parse_command("LEVELS 125 250 0 1000", &command));
    assert(command.type == LASER_TEST_COMMAND_ON);
    assert(laser_test_can_reconfigure_latched_output(true, true, &command));
    assert(!laser_test_can_reconfigure_latched_output(false, true, &command));
    assert(!laser_test_can_reconfigure_latched_output(true, false, &command));
    assert(command.channel_mask == ((1U << 0) | (1U << 1) | (1U << 3)));
    assert(command.duty_permille == 1000);
    assert(laser_test_command_channel_duty(&command, 0) == 125);
    assert(laser_test_command_channel_duty(&command, 1) == 250);
    assert(laser_test_command_channel_duty(&command, 2) == 0);
    assert(laser_test_command_channel_duty(&command, 3) == 1000);
    assert(laser_test_parse_command("LEVELS 0 0 0 0", &command));
    assert(command.type == LASER_TEST_COMMAND_OFF);
    assert(!laser_test_can_reconfigure_latched_output(true, true, &command));
    assert(!laser_test_parse_command("LEVELS 0 0 0 1001", &command));

    assert(laser_test_parse_command("ON GREEN 1000", &command));
    assert(command.type == LASER_TEST_COMMAND_ON);
    assert(command.channel_mask == (1U << 2));
    assert(command.duty_permille == 1000);
    assert(laser_test_command_channel_duty(&command, 2) == 1000);
    assert(laser_test_command_channel_duty(&command, 0) == 0);
    assert(command.duration_ms == 0);

    assert(laser_test_parse_command("ON IR_GREEN 1000", &command));
    assert(command.type == LASER_TEST_COMMAND_ON);
    assert(command.channel_mask == ((1U << 0) | (1U << 2)));
    assert(strcmp(laser_test_target_name(command.channel_mask), "IR_GREEN") == 0);

    assert(laser_test_parse_command("ON IR_RED_GREEN_BLUE 750", &command));
    assert(command.channel_mask == 0x0fU);
    for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        assert(laser_test_command_channel_duty(&command, channel) == 750);
    }
    assert(strcmp(laser_test_target_name(command.channel_mask), "IR_RED_GREEN_BLUE") == 0);

    assert(laser_test_parse_command("ON RED_BLUE 321", &command));
    assert(command.channel_mask == ((1U << 1) | (1U << 3)));
    assert(laser_test_command_channel_duty(&command, 1) == 321);
    assert(laser_test_command_channel_duty(&command, 3) == 321);
    assert(laser_test_command_channel_duty(&command, 0) == 0);

    assert(laser_test_parse_command("ON ALL 250", &command));
    assert(command.channel_mask == 0x0fU);

    assert(laser_test_parse_command("PULSE IR 1 20", &command));
    assert(command.type == LASER_TEST_COMMAND_PULSE);
    assert(command.channel_mask == (1U << 0));
    assert(command.duty_permille == 1);
    assert(command.duration_ms == 20);

    assert(laser_test_parse_command("PULSE GREEN 500 300", &command));
    assert(command.channel_mask == (1U << 2));
    assert(command.duty_permille == 500);
    assert(command.duration_ms == 300);
    assert(strcmp(laser_test_target_name(command.channel_mask), "GREEN") == 0);

    assert(laser_test_parse_command("PULSE BLUE 1000 900", &command));
    assert(command.channel_mask == (1U << 3));
    assert(command.duty_permille == 1000);
    assert(command.duration_ms == 900);

    assert(!laser_test_parse_command("PULSE RED 0 100", &command));
    assert(!laser_test_parse_command("PULSE RED 1001 100", &command));
    assert(!laser_test_parse_command("PULSE RED 10 19", &command));
    assert(!laser_test_parse_command("PULSE RED 10 901", &command));
    assert(!laser_test_parse_command("PULSE UV 10 100", &command));
    assert(!laser_test_parse_command("PULSE RED 10 100 EXTRA", &command));
    assert(!laser_test_parse_command("ON RED 0", &command));
    assert(!laser_test_parse_command("ON RED 1001", &command));
    assert(!laser_test_parse_command("ON UV 100", &command));
    assert(!laser_test_parse_command("ON GREEN_IR 100", &command));
    assert(!laser_test_parse_command("ON RED 100 500", &command));
    assert(!laser_test_parse_command("ARM RED", &command));
    assert(!laser_test_parse_command("SENSETEST NOW", &command));
}

int main(void)
{
    test_known_decode_vector();
    test_decode_boundaries();
    test_decode_round_trip_property();
    test_safety_state_machine();
    test_active_output_watchdog();
    test_every_fault_is_latched();
    test_laser_test_protocol();
    puts("PASS laser-controller host tests");
    return 0;
}
