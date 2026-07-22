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

static uint8_t target_mask(const char *name)
{
    const uint8_t valid_mask = (1U << LASER_TEST_CHANNEL_COUNT) - 1U;
    for (uint8_t mask = 1U; mask <= valid_mask; ++mask) {
        if (strcmp(name, laser_test_target_name(mask)) == 0) {
            return mask;
        }
    }
    return strcmp(name, "ALL") == 0 ? valid_mask : 0U;
}

const char *laser_test_target_name(uint8_t channel_mask)
{
    static const char *const names[1U << LASER_TEST_CHANNEL_COUNT] = {
        "OFF",
        "IR",
        "RED",
        "IR_RED",
        "GREEN",
        "IR_GREEN",
        "RED_GREEN",
        "IR_RED_GREEN",
        "BLUE",
        "IR_BLUE",
        "RED_BLUE",
        "IR_RED_BLUE",
        "GREEN_BLUE",
        "IR_GREEN_BLUE",
        "RED_GREEN_BLUE",
        "IR_RED_GREEN_BLUE",
    };
    return channel_mask < (1U << LASER_TEST_CHANNEL_COUNT) ?
        names[channel_mask] : "INVALID";
}

uint16_t laser_test_command_channel_duty(
    const laser_test_command_t *command,
    uint8_t channel
)
{
    if (command == NULL || channel >= LASER_TEST_CHANNEL_COUNT ||
        (command->channel_mask & (1U << channel)) == 0U) {
        return 0U;
    }
    return command->channel_duty_permille[channel] != 0U ?
        command->channel_duty_permille[channel] : command->duty_permille;
}

static void set_shared_duty(
    laser_test_command_t *command,
    uint8_t channel_mask,
    uint16_t duty_permille
)
{
    command->channel_mask = channel_mask;
    command->duty_permille = duty_permille;
    for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        if ((channel_mask & (1U << channel)) != 0U) {
            command->channel_duty_permille[channel] = duty_permille;
        }
    }
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

    char channel_name[24] = {0};
    unsigned int duty_permille = 0;
    consumed = 0;
    if (sscanf(
            line,
            " ON %23s %u %n",
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
        set_shared_duty(command, channel_mask, (uint16_t)duty_permille);
        return true;
    }

    memset(channel_name, 0, sizeof(channel_name));
    duty_permille = 0;
    unsigned int duration_ms = 0;
    consumed = 0;
    if (sscanf(
            line,
            " PULSE %23s %u %u %n",
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
    set_shared_duty(command, channel_mask, (uint16_t)duty_permille);
    command->duration_ms = (uint16_t)duration_ms;
    return true;
}
