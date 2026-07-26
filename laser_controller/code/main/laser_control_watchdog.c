#include "laser_control_watchdog.h"

bool laser_control_watchdog_expired(
    bool output_active,
    int64_t sampled_at_us,
    int64_t now_us,
    int64_t maximum_age_us
)
{
    if (!output_active || sampled_at_us < 0 || now_us < sampled_at_us ||
        maximum_age_us <= 0) {
        return false;
    }
    return now_us - sampled_at_us > maximum_age_us;
}
