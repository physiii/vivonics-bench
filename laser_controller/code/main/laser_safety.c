#include "laser_safety.h"

void laser_safety_init(laser_safety_t *safety)
{
    safety->state = LASER_STATE_BOOT_SAFE;
    safety->fault_mask = LASER_FAULT_NONE;
}

bool laser_safety_mark_adc_ready(laser_safety_t *safety)
{
    if (safety->state != LASER_STATE_BOOT_SAFE || safety->fault_mask != 0U) {
        return false;
    }
    safety->state = LASER_STATE_ADC_READY_LASERS_INHIBITED;
    return true;
}

bool laser_safety_request_arm(
    laser_safety_t *safety,
    bool local_arm_asserted,
    bool calibration_valid
)
{
    if (safety->state != LASER_STATE_ADC_READY_LASERS_INHIBITED ||
        safety->fault_mask != 0U || !local_arm_asserted || !calibration_valid) {
        return false;
    }
    safety->state = LASER_STATE_ARMED;
    return true;
}

bool laser_safety_start_run(laser_safety_t *safety)
{
    if (safety->state != LASER_STATE_ARMED || safety->fault_mask != 0U) {
        return false;
    }
    safety->state = LASER_STATE_RUN;
    return true;
}

void laser_safety_disarm(laser_safety_t *safety)
{
    if (safety->fault_mask != 0U || safety->state == LASER_STATE_FAULT_LATCHED) {
        safety->state = LASER_STATE_FAULT_LATCHED;
        return;
    }
    safety->state = LASER_STATE_ADC_READY_LASERS_INHIBITED;
}

void laser_safety_latch_fault(laser_safety_t *safety, laser_fault_t fault)
{
    safety->fault_mask |= (uint32_t)fault;
    safety->state = LASER_STATE_FAULT_LATCHED;
}

bool laser_safety_outputs_permitted(const laser_safety_t *safety)
{
    return safety->fault_mask == 0U &&
        (safety->state == LASER_STATE_ARMED || safety->state == LASER_STATE_RUN);
}
