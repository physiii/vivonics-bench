#include "laser_test_protocol.h"

#include <ctype.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

static bool only_trailing_space(const char *text, int consumed)
{
    for (const char *cursor = text + consumed; *cursor != '\0'; ++cursor) {
        if (!isspace((unsigned char)*cursor)) {
            return false;
        }
    }
    return true;
}

const char *laser_test_channel_name(uint8_t channel)
{
    static const char *const names[LASER_TEST_CHANNEL_COUNT] = {
        "IR",
        "RED",
        "GREEN",
        "BLUE",
    };
    return channel < LASER_TEST_CHANNEL_COUNT ? names[channel] : "INVALID";
}

static int channel_index(const char *name)
{
    for (int channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        if (strcmp(name, laser_test_channel_name((uint8_t)channel)) == 0) {
            return channel;
        }
    }
    return -1;
}

static uint8_t target_mask(const char *name)
{
    if (strcmp(name, "IR_GREEN") == 0) {
        return (1U << 0) | (1U << 2);
    }
    const int channel = channel_index(name);
    return channel < 0 ? 0U : (uint8_t)(1U << channel);
}

const char *laser_test_target_name(uint8_t channel_mask)
{
    if (channel_mask == ((1U << 0) | (1U << 2))) {
        return "IR_GREEN";
    }
    for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        if (channel_mask == (uint8_t)(1U << channel)) {
            return laser_test_channel_name(channel);
        }
    }
    return "INVALID";
}

bool laser_test_parse_command(const char *line, laser_test_command_t *command)
{
    if (line == NULL || command == NULL) {
        return false;
    }

    *command = (laser_test_command_t){0};
    int consumed = 0;
    if (sscanf(line, " STATUS %n", &consumed) == 0 && consumed > 0 &&
        only_trailing_space(line, consumed)) {
        command->type = LASER_TEST_COMMAND_STATUS;
        return true;
    }
    consumed = 0;
    if (sscanf(line, " OFF %n", &consumed) == 0 && consumed > 0 &&
        only_trailing_space(line, consumed)) {
        command->type = LASER_TEST_COMMAND_OFF;
        return true;
    }

    char channel_name[9] = {0};
    unsigned int duty_permille = 0;
    consumed = 0;
    if (sscanf(
            line,
            " ON %8s %u %n",
            channel_name,
            &duty_permille,
            &consumed
        ) == 2 && consumed > 0 && only_trailing_space(line, consumed)) {
        const uint8_t channel_mask = target_mask(channel_name);
        if (channel_mask == 0U || duty_permille == 0 ||
            duty_permille > LASER_TEST_MAX_DUTY_PERMILLE) {
            return false;
        }
        command->type = LASER_TEST_COMMAND_ON;
        command->channel_mask = channel_mask;
        command->duty_permille = (uint16_t)duty_permille;
        return true;
    }

    memset(channel_name, 0, sizeof(channel_name));
    duty_permille = 0;
    unsigned int duration_ms = 0;
    consumed = 0;
    if (sscanf(
            line,
            " PULSE %8s %u %u %n",
            channel_name,
            &duty_permille,
            &duration_ms,
            &consumed
        ) != 3 ||
        consumed <= 0 || !only_trailing_space(line, consumed)) {
        return false;
    }

    const uint8_t channel_mask = target_mask(channel_name);
    if (channel_mask == 0U || duty_permille == 0 ||
        duty_permille > LASER_TEST_MAX_DUTY_PERMILLE ||
        duration_ms < LASER_TEST_MIN_DURATION_MS ||
        duration_ms > LASER_TEST_MAX_DURATION_MS) {
        return false;
    }

    command->type = LASER_TEST_COMMAND_PULSE;
    command->channel_mask = channel_mask;
    command->duty_permille = (uint16_t)duty_permille;
    command->duration_ms = (uint16_t)duration_ms;
    return true;
}
