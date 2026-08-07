#ifndef VIVONICS_LASER_TEST_PROTOCOL_H
#define VIVONICS_LASER_TEST_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

enum {
    LASER_TEST_CHANNEL_COUNT = 4,
    LASER_TEST_MIN_DURATION_MS = 20,
    LASER_TEST_MAX_DURATION_MS = 900,
    LASER_TEST_MAX_DUTY_PERMILLE = 1000,
};

typedef enum {
    LASER_TEST_COMMAND_INVALID = 0,
    LASER_TEST_COMMAND_STATUS,
    LASER_TEST_COMMAND_OFF,
    LASER_TEST_COMMAND_SENSETEST,
    LASER_TEST_COMMAND_STREAM,
    LASER_TEST_COMMAND_SNAPSHOT,
    LASER_TEST_COMMAND_ON,
    LASER_TEST_COMMAND_PULSE,
} laser_test_command_type_t;

typedef struct {
    laser_test_command_type_t type;
    uint8_t channel_mask;
    uint16_t duty_permille;
    uint16_t channel_duty_permille[LASER_TEST_CHANNEL_COUNT];
    uint16_t duration_ms;
    uint8_t stream_hz;
} laser_test_command_t;

bool laser_test_parse_command(const char *line, laser_test_command_t *command);
bool laser_test_can_reconfigure_latched_output(
    bool output_active,
    bool output_latched,
    const laser_test_command_t *command
);
const char *laser_test_channel_name(uint8_t channel);
const char *laser_test_target_name(uint8_t channel_mask);
uint16_t laser_test_command_channel_duty(
    const laser_test_command_t *command,
    uint8_t channel
);

#endif
