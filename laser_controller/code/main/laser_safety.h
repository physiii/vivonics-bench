#ifndef VIVONICS_LASER_SAFETY_H
#define VIVONICS_LASER_SAFETY_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    LASER_STATE_BOOT_SAFE = 0,
    LASER_STATE_ADC_READY_LASERS_INHIBITED,
    LASER_STATE_ARMED,
    LASER_STATE_RUN,
    LASER_STATE_FAULT_LATCHED,
} laser_state_t;

typedef enum {
    LASER_FAULT_NONE = 0,
    LASER_FAULT_ADC_INIT = 1U << 0,
    LASER_FAULT_ADC_BUSY_RISE_TIMEOUT = 1U << 1,
    LASER_FAULT_ADC_BUSY_FALL_TIMEOUT = 1U << 2,
    LASER_FAULT_ADC_SPI = 1U << 3,
    LASER_FAULT_ADC_TIMING_OVERRUN = 1U << 4,
    LASER_FAULT_WATCHDOG = 1U << 5,
    LASER_FAULT_TELEMETRY_ADC = 1U << 6,
    LASER_FAULT_OVERCURRENT = 1U << 7,
    LASER_FAULT_PWM_OUTPUT = 1U << 8,
    LASER_FAULT_WEB_INIT = 1U << 9,
} laser_fault_t;

typedef struct {
    laser_state_t state;
    uint32_t fault_mask;
} laser_safety_t;

void laser_safety_init(laser_safety_t *safety);
bool laser_safety_mark_adc_ready(laser_safety_t *safety);
bool laser_safety_request_arm(
    laser_safety_t *safety,
    bool local_arm_asserted,
    bool calibration_valid
);
bool laser_safety_start_run(laser_safety_t *safety);
void laser_safety_disarm(laser_safety_t *safety);
void laser_safety_latch_fault(laser_safety_t *safety, laser_fault_t fault);
bool laser_safety_outputs_permitted(const laser_safety_t *safety);

#endif
