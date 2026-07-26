#ifndef VIVONICS_LASER_CONTROL_WATCHDOG_H
#define VIVONICS_LASER_CONTROL_WATCHDOG_H

#include <stdbool.h>
#include <stdint.h>

bool laser_control_watchdog_expired(
    bool output_active,
    int64_t sampled_at_us,
    int64_t now_us,
    int64_t maximum_age_us
);

#endif
