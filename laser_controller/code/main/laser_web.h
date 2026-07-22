#ifndef VIVONICS_LASER_WEB_H
#define VIVONICS_LASER_WEB_H

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#include "laser_safety.h"
#include "laser_test_protocol.h"

enum {
    LASER_WEB_PHOTODIODE_COUNT = 4,
    LASER_WEB_TELEMETRY_COUNT = 8,
};

typedef struct {
    uint64_t sample_index;
    uint64_t timing_overruns;
    int64_t sampled_at_us;
    int16_t photodiode_counts[LASER_WEB_PHOTODIODE_COUNT];
    int telemetry_raw[LASER_WEB_TELEMETRY_COUNT];
    int telemetry_mv[LASER_WEB_TELEMETRY_COUNT];
    laser_state_t safety_state;
    uint32_t fault_mask;
    uint8_t active_mask;
    uint16_t duty_permille;
    uint16_t channel_duty_permille[LASER_TEST_CHANNEL_COUNT];
    bool output_active;
    bool output_latched;
} laser_web_snapshot_t;

esp_err_t laser_web_start(void);
void laser_web_publish_snapshot(const laser_web_snapshot_t *snapshot);
void laser_web_publish_fault(uint32_t fault_mask);
bool laser_web_receive_command(laser_test_command_t *command);
bool laser_web_ota_in_progress(void);
esp_err_t laser_web_save_wifi_credentials(const char *ssid, const char *password);
void laser_web_record_event(const char *message);
bool laser_web_rollback_if_pending(const char *reason);

#endif
