#include <inttypes.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "driver/gpio.h"
#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
#include "driver/ledc.h"
#include "driver/usb_serial_jtag.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#endif
#include "driver/spi_master.h"
#include "esp_app_desc.h"
#include "esp_attr.h"
#include "esp_err.h"
#include "esp_idf_version.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "ad7606_decode.h"
#include "laser_safety.h"
#include "laser_test_protocol.h"
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
#include "laser_web.h"
#endif

enum {
    GPIO_PWM_IR = 10,
    GPIO_PWM_RED = 11,
    GPIO_PWM_GREEN = 12,
    GPIO_PWM_BLUE = 16,
    GPIO_ADC_CONVST = 15,
    GPIO_ADC_SCLK = 17,
    GPIO_ADC_CS = 18,
    GPIO_ADC_DOUTA = 21,
    GPIO_ADC_BUSY = 47,
    GPIO_ADC_RESET = 48,
};

static const char *TAG = "laser_controller";
static const uint64_t PWM_PIN_MASK =
    (1ULL << GPIO_PWM_IR) |
    (1ULL << GPIO_PWM_RED) |
    (1ULL << GPIO_PWM_GREEN) |
    (1ULL << GPIO_PWM_BLUE);

static laser_safety_t safety;
static spi_device_handle_t adc_spi;
static uint64_t conversion_count;
static uint64_t timing_overrun_count;
static volatile bool adc_busy_rise_latched;

static void IRAM_ATTR adc_busy_rise_isr(void *argument)
{
    (void)argument;
    adc_busy_rise_latched = true;
}

#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
enum {
    TELEMETRY_CHANNEL_COUNT = 8,
    UART_LINE_CAPACITY = 128,
    LASER_PWM_FREQUENCY_HZ = 10000,
    LASER_PWM_MAX_DUTY = 1023,
};

typedef struct {
    int raw[TELEMETRY_CHANNEL_COUNT];
    int millivolts[TELEMETRY_CHANNEL_COUNT];
} laser_telemetry_t;

typedef struct {
    bool active;
    bool latched;
    uint8_t channel_mask;
    uint16_t channel_duty_permille[LASER_TEST_CHANNEL_COUNT];
    uint16_t duty_permille;
    int64_t deadline_us;
} laser_pulse_t;

static const int LASER_PWM_GPIOS[LASER_TEST_CHANNEL_COUNT] = {
    GPIO_PWM_IR,
    GPIO_PWM_RED,
    GPIO_PWM_GREEN,
    GPIO_PWM_BLUE,
};
static const ledc_channel_t LASER_PWM_CHANNELS[LASER_TEST_CHANNEL_COUNT] = {
    LEDC_CHANNEL_0,
    LEDC_CHANNEL_1,
    LEDC_CHANNEL_2,
    LEDC_CHANNEL_3,
};
static const adc_channel_t TELEMETRY_CHANNELS[TELEMETRY_CHANNEL_COUNT] = {
    ADC_CHANNEL_3, /* GPIO4: ISENSE1 */
    ADC_CHANNEL_4, /* GPIO5: ISENSE2 */
    ADC_CHANNEL_5, /* GPIO6: ISENSE3 */
    ADC_CHANNEL_6, /* GPIO7: ISENSE4 */
    ADC_CHANNEL_1, /* GPIO2: MPD1 */
    ADC_CHANNEL_2, /* GPIO3: MPD2 */
    ADC_CHANNEL_7, /* GPIO8: MPD3 */
    ADC_CHANNEL_8, /* GPIO9: MPD4/spare */
};
static const gpio_num_t TELEMETRY_GPIOS[TELEMETRY_CHANNEL_COUNT] = {
    GPIO_NUM_4, /* ISENSE1 */
    GPIO_NUM_5, /* ISENSE2 */
    GPIO_NUM_6, /* ISENSE3 */
    GPIO_NUM_7, /* ISENSE4 */
    GPIO_NUM_2, /* MPD1 */
    GPIO_NUM_3, /* MPD2 */
    GPIO_NUM_8, /* MPD3 */
    GPIO_NUM_9, /* MPD4/spare */
};
static const char *const TELEMETRY_SIGNAL_NAMES[TELEMETRY_CHANNEL_COUNT] = {
    "ISENSE1",
    "ISENSE2",
    "ISENSE3",
    "ISENSE4",
    "MPD1",
    "MPD2",
    "MPD3",
    "MPD4_SPARE",
};
static const int ISENSE_HARD_CEILING_MV[LASER_TEST_CHANNEL_COUNT] = {
    450,
    300,
    850,
    1150,
};

static bool laser_pwm_initialized;
static uint8_t laser_direct_gpio_mask;
static bool telemetry_initialized;
static adc_oneshot_unit_handle_t telemetry_adc;
static adc_cali_handle_t telemetry_cali[TELEMETRY_CHANNEL_COUNT];
static laser_pulse_t pulse;
static char uart_line[UART_LINE_CAPACITY];
static size_t uart_line_length;
#endif

static void force_all_lasers_off(void)
{
#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
    if (laser_direct_gpio_mask != 0U) {
        for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
            if ((laser_direct_gpio_mask & (1U << channel)) != 0U) {
                gpio_set_level(LASER_PWM_GPIOS[channel], 0);
            }
        }
        laser_direct_gpio_mask = 0U;
    }
    if (laser_pwm_initialized) {
        for (size_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LASER_PWM_CHANNELS[channel], 0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE, LASER_PWM_CHANNELS[channel]);
        }
        return;
    }
#endif
    gpio_set_level(GPIO_PWM_IR, 0);
    gpio_set_level(GPIO_PWM_RED, 0);
    gpio_set_level(GPIO_PWM_GREEN, 0);
    gpio_set_level(GPIO_PWM_BLUE, 0);
}

static esp_err_t configure_safe_gpio(void)
{
    const gpio_config_t pwm_config = {
        .pin_bit_mask = PWM_PIN_MASK,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t error = gpio_config(&pwm_config);
    if (error != ESP_OK) {
        return error;
    }
    force_all_lasers_off();

    const gpio_config_t adc_output_config = {
        .pin_bit_mask = (1ULL << GPIO_ADC_CONVST) | (1ULL << GPIO_ADC_RESET),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    error = gpio_config(&adc_output_config);
    if (error != ESP_OK) {
        return error;
    }
    gpio_set_level(GPIO_ADC_CONVST, 0);
    gpio_set_level(GPIO_ADC_RESET, 0);

    const gpio_config_t busy_config = {
        .pin_bit_mask = 1ULL << GPIO_ADC_BUSY,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_POSEDGE,
    };
    error = gpio_config(&busy_config);
    if (error != ESP_OK) {
        return error;
    }
    error = gpio_install_isr_service(ESP_INTR_FLAG_IRAM);
    if (error != ESP_OK) {
        return error;
    }
    return gpio_isr_handler_add(GPIO_ADC_BUSY, adc_busy_rise_isr, NULL);
}

#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
static esp_err_t configure_laser_pwm_channel(size_t channel)
{
    if (channel >= LASER_TEST_CHANNEL_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    const ledc_channel_config_t channel_config = {
        .gpio_num = LASER_PWM_GPIOS[channel],
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LASER_PWM_CHANNELS[channel],
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0,
        .sleep_mode = LEDC_SLEEP_MODE_NO_ALIVE_NO_PD,
        .flags.output_invert = 0,
    };
    esp_err_t error = ledc_channel_config(&channel_config);
    if (error != ESP_OK) {
        return error;
    }
    return gpio_input_enable((gpio_num_t)LASER_PWM_GPIOS[channel]);
}

static esp_err_t configure_laser_test_pwm(void)
{
    const ledc_timer_config_t timer_config = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = LASER_PWM_FREQUENCY_HZ,
        .clk_cfg = LEDC_AUTO_CLK,
        .deconfigure = false,
    };
    esp_err_t error = ledc_timer_config(&timer_config);
    if (error != ESP_OK) {
        return error;
    }

    for (size_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        error = configure_laser_pwm_channel(channel);
        if (error != ESP_OK) {
            return error;
        }
        ESP_LOGI(
            TAG,
            "PWM_MAP channel=%s gpio=%d ledc_channel=%d",
            laser_test_channel_name(channel),
            LASER_PWM_GPIOS[channel],
            (int)LASER_PWM_CHANNELS[channel]
        );
    }
    const uint32_t configured_frequency =
        ledc_get_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0);
    if (configured_frequency != LASER_PWM_FREQUENCY_HZ) {
        ESP_LOGE(
            TAG,
            "PWM_TIMER_MISMATCH requested_hz=%d configured_hz=%" PRIu32,
            LASER_PWM_FREQUENCY_HZ,
            configured_frequency
        );
        return ESP_FAIL;
    }
    laser_pwm_initialized = true;
    force_all_lasers_off();
    return ESP_OK;
}

static esp_err_t configure_telemetry_adc(void)
{
    const adc_oneshot_unit_init_cfg_t unit_config = {
        .unit_id = ADC_UNIT_1,
        .clk_src = ADC_RTC_CLK_SRC_DEFAULT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    esp_err_t error = adc_oneshot_new_unit(&unit_config, &telemetry_adc);
    if (error != ESP_OK) {
        return error;
    }

    const adc_oneshot_chan_cfg_t channel_config = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    for (size_t index = 0; index < TELEMETRY_CHANNEL_COUNT; ++index) {
        error = adc_oneshot_config_channel(
            telemetry_adc,
            TELEMETRY_CHANNELS[index],
            &channel_config
        );
        if (error != ESP_OK) {
            return error;
        }

        const adc_cali_curve_fitting_config_t calibration_config = {
            .unit_id = ADC_UNIT_1,
            .chan = TELEMETRY_CHANNELS[index],
            .atten = ADC_ATTEN_DB_12,
            .bitwidth = ADC_BITWIDTH_12,
        };
        error = adc_cali_create_scheme_curve_fitting(
            &calibration_config,
            &telemetry_cali[index]
        );
        if (error != ESP_OK) {
            return error;
        }
    }
    telemetry_initialized = true;
    return ESP_OK;
}

static esp_err_t read_telemetry(laser_telemetry_t *telemetry)
{
    if (!telemetry_initialized || telemetry == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    for (size_t index = 0; index < TELEMETRY_CHANNEL_COUNT; ++index) {
        esp_err_t error = adc_oneshot_read(
            telemetry_adc,
            TELEMETRY_CHANNELS[index],
            &telemetry->raw[index]
        );
        if (error != ESP_OK) {
            return error;
        }
        error = adc_cali_raw_to_voltage(
            telemetry_cali[index],
            telemetry->raw[index],
            &telemetry->millivolts[index]
        );
        if (error != ESP_OK) {
            return error;
        }
    }
    return ESP_OK;
}

static esp_err_t read_telemetry_channel_average(
    size_t index,
    int *raw_average,
    int *millivolts
)
{
    enum { SAMPLE_COUNT = 16 };
    if (!telemetry_initialized || index >= TELEMETRY_CHANNEL_COUNT ||
        raw_average == NULL || millivolts == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    int64_t raw_sum = 0;
    for (unsigned sample = 0; sample < SAMPLE_COUNT; ++sample) {
        int raw = 0;
        const esp_err_t error = adc_oneshot_read(
            telemetry_adc,
            TELEMETRY_CHANNELS[index],
            &raw
        );
        if (error != ESP_OK) {
            return error;
        }
        raw_sum += raw;
    }
    *raw_average = (int)(raw_sum / SAMPLE_COUNT);
    return adc_cali_raw_to_voltage(
        telemetry_cali[index],
        *raw_average,
        millivolts
    );
}

static esp_err_t run_sensing_pin_self_test(void)
{
    if (pulse.active || safety.state != LASER_STATE_ADC_READY_LASERS_INHIBITED ||
        safety.fault_mask != 0U) {
        ESP_LOGE(
            TAG,
            "SENSETEST_REJECTED active=%d state=%d faults=0x%08" PRIx32,
            pulse.active,
            (int)safety.state,
            safety.fault_mask
        );
        return ESP_ERR_INVALID_STATE;
    }

    force_all_lasers_off();
    ESP_LOGW(TAG, "SENSETEST_BEGIN outputs=OFF weak_internal_pulls_only");
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
    laser_web_record_event("SENSETEST_BEGIN outputs=OFF weak_internal_pulls_only");
#endif
    for (size_t index = 0; index < TELEMETRY_CHANNEL_COUNT; ++index) {
        int floating_raw = 0;
        int floating_mv = 0;
        int pullup_raw = 0;
        int pullup_mv = 0;
        int pulldown_raw = 0;
        int pulldown_mv = 0;

        esp_err_t error = gpio_set_pull_mode(
            TELEMETRY_GPIOS[index],
            GPIO_FLOATING
        );
        if (error == ESP_OK) {
            vTaskDelay(pdMS_TO_TICKS(2));
            error = read_telemetry_channel_average(
                index,
                &floating_raw,
                &floating_mv
            );
        }
        if (error == ESP_OK) {
            error = gpio_set_pull_mode(
                TELEMETRY_GPIOS[index],
                GPIO_PULLUP_ONLY
            );
        }
        if (error == ESP_OK) {
            vTaskDelay(pdMS_TO_TICKS(5));
            error = read_telemetry_channel_average(index, &pullup_raw, &pullup_mv);
        }
        if (error == ESP_OK) {
            error = gpio_set_pull_mode(
                TELEMETRY_GPIOS[index],
                GPIO_PULLDOWN_ONLY
            );
        }
        if (error == ESP_OK) {
            vTaskDelay(pdMS_TO_TICKS(5));
            error = read_telemetry_channel_average(
                index,
                &pulldown_raw,
                &pulldown_mv
            );
        }

        const esp_err_t restore_error = gpio_set_pull_mode(
            TELEMETRY_GPIOS[index],
            GPIO_FLOATING
        );
        if (error == ESP_OK) {
            error = restore_error;
        }
        if (error != ESP_OK) {
            force_all_lasers_off();
            ESP_LOGE(
                TAG,
                "SENSETEST_FAILED signal=%s gpio=%d error=%s",
                TELEMETRY_SIGNAL_NAMES[index],
                (int)TELEMETRY_GPIOS[index],
                esp_err_to_name(error)
            );
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
            char event[96];
            snprintf(
                event,
                sizeof(event),
                "SENSETEST_FAILED %s G%d %s",
                TELEMETRY_SIGNAL_NAMES[index],
                (int)TELEMETRY_GPIOS[index],
                esp_err_to_name(error)
            );
            laser_web_record_event(event);
#endif
            return error;
        }

        ESP_LOGW(
            TAG,
            "SENSE_PIN signal=%s gpio=%d floating=%d/%dmV "
            "pullup=%d/%dmV pulldown=%d/%dmV",
            TELEMETRY_SIGNAL_NAMES[index],
            (int)TELEMETRY_GPIOS[index],
            floating_raw,
            floating_mv,
            pullup_raw,
            pullup_mv,
            pulldown_raw,
            pulldown_mv
        );
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
        char event[112];
        snprintf(
            event,
            sizeof(event),
            "SENSE_PIN %s G%d F%d/%dmV U%d/%dmV D%d/%dmV",
            TELEMETRY_SIGNAL_NAMES[index],
            (int)TELEMETRY_GPIOS[index],
            floating_raw,
            floating_mv,
            pullup_raw,
            pullup_mv,
            pulldown_raw,
            pulldown_mv
        );
        laser_web_record_event(event);
#endif
    }
    ESP_LOGW(TAG, "SENSETEST_END outputs=OFF");
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
    laser_web_record_event("SENSETEST_END outputs=OFF");
#endif
    return ESP_OK;
}

static esp_err_t configure_test_command_transport(void)
{
    usb_serial_jtag_driver_config_t transport_config =
        USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    return usb_serial_jtag_driver_install(&transport_config);
}

static esp_err_t set_laser_duty(uint8_t channel, uint16_t duty_permille)
{
    if (channel >= LASER_TEST_CHANNEL_COUNT ||
        duty_permille > LASER_TEST_MAX_DUTY_PERMILLE) {
        return ESP_ERR_INVALID_ARG;
    }
    const gpio_num_t gpio = (gpio_num_t)LASER_PWM_GPIOS[channel];
    if (duty_permille == LASER_TEST_MAX_DUTY_PERMILLE) {
        esp_err_t error = gpio_reset_pin(gpio);
        if (error == ESP_OK) {
            error = gpio_set_pull_mode(gpio, GPIO_FLOATING);
        }
        if (error == ESP_OK) {
            error = gpio_set_level(gpio, 0);
        }
        if (error == ESP_OK) {
            error = gpio_set_direction(gpio, GPIO_MODE_INPUT_OUTPUT);
        }
        if (error == ESP_OK) {
            error = gpio_set_level(gpio, 1);
        }
        if (error != ESP_OK) {
            gpio_set_level(gpio, 0);
            return error;
        }
        laser_direct_gpio_mask |= (uint8_t)(1U << channel);

        esp_rom_delay_us(100);
        unsigned pad_high_samples = 0;
        for (unsigned sample = 0; sample < 32U; ++sample) {
            pad_high_samples += (unsigned)gpio_get_level(gpio);
            esp_rom_delay_us(3);
        }
        ESP_LOGI(
            TAG,
            "GPIO_APPLIED channel=%s gpio=%d level=1 pad_high=%u/32",
            laser_test_channel_name(channel),
            (int)gpio,
            pad_high_samples
        );
        if (pad_high_samples < 24U) {
            gpio_set_level(gpio, 0);
            laser_direct_gpio_mask &= (uint8_t)~(1U << channel);
            ESP_LOGE(
                TAG,
                "GPIO_PAD_READBACK_LOW channel=%s gpio=%d high_samples=%u/32",
                laser_test_channel_name(channel),
                (int)gpio,
                pad_high_samples
            );
            return ESP_FAIL;
        }
        return ESP_OK;
    }

    esp_err_t error = configure_laser_pwm_channel(channel);
    if (error != ESP_OK) {
        return error;
    }
    const uint32_t duty =
        ((uint32_t)duty_permille * LASER_PWM_MAX_DUTY) /
        LASER_TEST_MAX_DUTY_PERMILLE;
    error = ledc_set_duty(
        LEDC_LOW_SPEED_MODE,
        LASER_PWM_CHANNELS[channel],
        duty
    );
    if (error != ESP_OK) {
        return error;
    }
    error = ledc_update_duty(LEDC_LOW_SPEED_MODE, LASER_PWM_CHANNELS[channel]);
    if (error != ESP_OK) {
        return error;
    }

    esp_rom_delay_us(100);
    const uint32_t duty_readback = ledc_get_duty(
        LEDC_LOW_SPEED_MODE,
        LASER_PWM_CHANNELS[channel]
    );
    unsigned pad_high_samples = 0;
    for (unsigned sample = 0; sample < 32U; ++sample) {
        pad_high_samples += (unsigned)gpio_get_level(LASER_PWM_GPIOS[channel]);
        esp_rom_delay_us(3);
    }
    ESP_LOGI(
        TAG,
        "PWM_APPLIED channel=%s gpio=%d ledc_channel=%d duty_permille=%u "
        "duty_counts=%" PRIu32 " readback_counts=%" PRIu32 " pad_high=%u/32",
        laser_test_channel_name(channel),
        LASER_PWM_GPIOS[channel],
        (int)LASER_PWM_CHANNELS[channel],
        duty_permille,
        duty,
        duty_readback,
        pad_high_samples
    );
    if (duty_readback != duty) {
        return ESP_FAIL;
    }
    return ESP_OK;
}

static esp_err_t set_laser_targets(const laser_test_command_t *command)
{
    const uint8_t valid_mask = (1U << LASER_TEST_CHANNEL_COUNT) - 1U;
    if (command == NULL || command->channel_mask == 0U ||
        (command->channel_mask & (uint8_t)~valid_mask) != 0U) {
        return ESP_ERR_INVALID_ARG;
    }
    force_all_lasers_off();
    for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        if ((command->channel_mask & (1U << channel)) == 0U) {
            continue;
        }
        const uint16_t duty_permille =
            laser_test_command_channel_duty(command, channel);
        if (duty_permille == 0U ||
            duty_permille > LASER_TEST_MAX_DUTY_PERMILLE) {
            force_all_lasers_off();
            return ESP_ERR_INVALID_ARG;
        }
        const esp_err_t error = set_laser_duty(channel, duty_permille);
        if (error != ESP_OK) {
            force_all_lasers_off();
            return error;
        }
    }
    return ESP_OK;
}

static void stop_output(const char *reason)
{
    force_all_lasers_off();
    pulse.active = false;
    pulse.latched = false;
    pulse.duty_permille = 0;
    memset(pulse.channel_duty_permille, 0, sizeof(pulse.channel_duty_permille));
    laser_safety_disarm(&safety);
    ESP_LOGW(TAG, "OUTPUT_OFF reason=%s state=%d faults=0x%08" PRIx32,
             reason, (int)safety.state, safety.fault_mask);
}

static void log_test_status(void)
{
    ESP_LOGI(
        TAG,
        "TEST_STATUS state=%d faults=0x%08" PRIx32 " active=%d mode=%s "
        "target=%s duty_permille=%u duties=%u,%u,%u,%u",
        (int)safety.state,
        safety.fault_mask,
        pulse.active,
        !pulse.active ? "off" : (pulse.latched ? "latched" : "pulse"),
        laser_test_target_name(pulse.channel_mask),
        pulse.duty_permille,
        pulse.channel_duty_permille[0],
        pulse.channel_duty_permille[1],
        pulse.channel_duty_permille[2],
        pulse.channel_duty_permille[3]
    );
}

static void apply_test_command(const laser_test_command_t *command)
{
    if (command == NULL) {
        return;
    }
    if (command->type == LASER_TEST_COMMAND_SENSETEST) {
        (void)run_sensing_pin_self_test();
        return;
    }
    if (command->type == LASER_TEST_COMMAND_STATUS) {
        log_test_status();
        return;
    }
    if (command->type == LASER_TEST_COMMAND_OFF) {
        stop_output("command");
        return;
    }
    if (pulse.active && command->type == LASER_TEST_COMMAND_ON) {
        stop_output("reconfigure");
    }
    if (pulse.active || safety.state != LASER_STATE_ADC_READY_LASERS_INHIBITED ||
        safety.fault_mask != 0U) {
        ESP_LOGE(
            TAG,
            "OUTPUT_REJECTED active=%d state=%d faults=0x%08" PRIx32,
            pulse.active,
            (int)safety.state,
            safety.fault_mask
        );
        return;
    }
    /* A validated local command is the test-profile arm request. */
    if (!laser_safety_request_arm(&safety, true, true) ||
        !laser_safety_start_run(&safety)) {
        force_all_lasers_off();
        laser_safety_latch_fault(&safety, LASER_FAULT_WATCHDOG);
        ESP_LOGE(TAG, "OUTPUT_REJECTED safety transition failed");
        return;
    }

    pulse.channel_mask = command->channel_mask;
    pulse.duty_permille = command->duty_permille;
    for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        pulse.channel_duty_permille[channel] =
            laser_test_command_channel_duty(command, channel);
    }
    pulse.latched = command->type == LASER_TEST_COMMAND_ON;
    pulse.deadline_us = pulse.latched ? 0 :
        esp_timer_get_time() + (int64_t)command->duration_ms * 1000;
    const esp_err_t pwm_error = set_laser_targets(command);
    if (pwm_error != ESP_OK) {
        force_all_lasers_off();
        pulse.active = false;
        pulse.latched = false;
        pulse.duty_permille = 0;
        memset(pulse.channel_duty_permille, 0, sizeof(pulse.channel_duty_permille));
        laser_safety_latch_fault(&safety, LASER_FAULT_PWM_OUTPUT);
        ESP_LOGE(
            TAG,
            "OUTPUT_REJECTED PWM apply failed: %s",
            esp_err_to_name(pwm_error)
        );
        return;
    }
    pulse.active = true;
    if (pulse.latched) {
        ESP_LOGW(
            TAG,
            "OUTPUT_ON mode=latched target=%s duty_permille=%u "
            "duties=%u,%u,%u,%u",
            laser_test_target_name(command->channel_mask),
            command->duty_permille,
            pulse.channel_duty_permille[0],
            pulse.channel_duty_permille[1],
            pulse.channel_duty_permille[2],
            pulse.channel_duty_permille[3]
        );
    } else {
        ESP_LOGW(
            TAG,
            "OUTPUT_ON mode=pulse target=%s duty_permille=%u "
            "duties=%u,%u,%u,%u duration_ms=%u",
            laser_test_target_name(command->channel_mask),
            command->duty_permille,
            pulse.channel_duty_permille[0],
            pulse.channel_duty_permille[1],
            pulse.channel_duty_permille[2],
            pulse.channel_duty_permille[3],
            command->duration_ms
        );
    }
}

static void handle_test_command(const char *line)
{
    laser_test_command_t command = {0};
    if (!laser_test_parse_command(line, &command)) {
        ESP_LOGE(
            TAG,
            "COMMAND_REJECTED syntax; use STATUS, OFF, SENSETEST, "
            "ON <canonical channel combination|ALL> <1..1000>, or "
            "PULSE <canonical channel combination|ALL> <1..1000> <20..900>"
        );
        return;
    }
    apply_test_command(&command);
}

#if CONFIG_LC_ENABLE_WEB_DASHBOARD
static bool handle_wifi_provision_command(const char *line)
{
    if (line == NULL || strncmp(line, "WIFI ", 5U) != 0) {
        return false;
    }
    char ssid[33] = {0};
    char password[65] = {0};
    if (sscanf(line, "WIFI %32s %64[^\r\n]", ssid, password) != 2) {
        ESP_LOGE(TAG, "WIFI_REJECTED use WIFI <ssid> <password>");
        return true;
    }
    const esp_err_t error = laser_web_save_wifi_credentials(ssid, password);
    if (error == ESP_OK) {
        ESP_LOGI(TAG, "WIFI_ACCEPTED ssid=%s password=********", ssid);
    } else {
        ESP_LOGE(TAG, "WIFI_REJECTED error=%s", esp_err_to_name(error));
    }
    return true;
}
#endif

static bool service_test_commands(void)
{
    bool command_processed = false;
    uint8_t received[32];
    const int count = usb_serial_jtag_read_bytes(received, sizeof(received), 0);
    for (int index = 0; index < count; ++index) {
        const char character = (char)received[index];
        if (character == '\r') {
            continue;
        }
        if (character == '\n') {
            uart_line[uart_line_length] = '\0';
            if (uart_line_length > 0) {
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
                if (!handle_wifi_provision_command(uart_line)) {
                    handle_test_command(uart_line);
                }
#else
                handle_test_command(uart_line);
#endif
                command_processed = true;
            }
            uart_line_length = 0;
            continue;
        }
        if (uart_line_length + 1U >= sizeof(uart_line)) {
            uart_line_length = 0;
            ESP_LOGE(TAG, "COMMAND_REJECTED line too long");
            continue;
        }
        uart_line[uart_line_length++] = character;
    }
    return command_processed;
}

static bool update_pulse(const laser_telemetry_t *telemetry)
{
    if (!pulse.active) {
        return true;
    }
    if (!pulse.latched && esp_timer_get_time() >= pulse.deadline_us) {
        stop_output("deadline");
        return true;
    }
    for (uint8_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        if ((pulse.channel_mask & (1U << channel)) == 0U ||
            telemetry->millivolts[channel] <= ISENSE_HARD_CEILING_MV[channel]) {
            continue;
        }
        force_all_lasers_off();
        pulse.active = false;
        pulse.latched = false;
        pulse.duty_permille = 0;
        memset(pulse.channel_duty_permille, 0, sizeof(pulse.channel_duty_permille));
        laser_safety_latch_fault(&safety, LASER_FAULT_OVERCURRENT);
        ESP_LOGE(
            TAG,
            "OVERCURRENT channel=%s isense_mv=%d ceiling_mv=%d",
            laser_test_channel_name(channel),
            telemetry->millivolts[channel],
            ISENSE_HARD_CEILING_MV[channel]
        );
        return false;
    }
    return true;
}
#endif

static esp_err_t initialize_adc_spi(void)
{
    const spi_bus_config_t bus_config = {
        .mosi_io_num = -1,
        .miso_io_num = GPIO_ADC_DOUTA,
        .sclk_io_num = GPIO_ADC_SCLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = AD7606_DOUTA_FRAME_BYTES,
    };
    esp_err_t error = spi_bus_initialize(SPI2_HOST, &bus_config, SPI_DMA_DISABLED);
    if (error != ESP_OK) {
        return error;
    }

    const spi_device_interface_config_t device_config = {
        .command_bits = 0,
        .address_bits = 0,
        .dummy_bits = 0,
        .mode = 1,
        .clock_speed_hz = CONFIG_LC_AD7606_SCLK_HZ,
        .spics_io_num = GPIO_ADC_CS,
        .queue_size = 1,
        .flags = SPI_DEVICE_HALFDUPLEX | SPI_DEVICE_NO_DUMMY,
    };
    error = spi_bus_add_device(SPI2_HOST, &device_config, &adc_spi);
    if (error != ESP_OK) {
        spi_bus_free(SPI2_HOST);
    }
    return error;
}

static void reset_adc(void)
{
    const int busy_before = gpio_get_level(GPIO_ADC_BUSY);
    gpio_set_level(GPIO_ADC_RESET, 1);
    esp_rom_delay_us(10);
    const int busy_during_reset = gpio_get_level(GPIO_ADC_BUSY);
    gpio_set_level(GPIO_ADC_RESET, 0);
    esp_rom_delay_us(100);
    ESP_LOGI(
        TAG,
        "ADC_RESET_DIAG busy_before=%d busy_during=%d busy_after=%d",
        busy_before,
        busy_during_reset,
        gpio_get_level(GPIO_ADC_BUSY)
    );
}

static bool wait_for_gpio_level(int gpio, int level, uint32_t timeout_us)
{
    if (gpio_get_level(gpio) == level) {
        return true;
    }
    const int64_t deadline = esp_timer_get_time() + timeout_us;
    while (esp_timer_get_time() <= deadline) {
        if (gpio_get_level(gpio) == level) {
            return true;
        }
    }
    return false;
}

static bool wait_for_adc_busy_rise(uint32_t timeout_us)
{
    if (adc_busy_rise_latched || gpio_get_level(GPIO_ADC_BUSY) == 1) {
        return true;
    }
    const int64_t deadline = esp_timer_get_time() + timeout_us;
    while (esp_timer_get_time() <= deadline) {
        if (adc_busy_rise_latched || gpio_get_level(GPIO_ADC_BUSY) == 1) {
            return true;
        }
    }
    return false;
}

static laser_fault_t acquire_sample(ad7606_sample_t *sample)
{
    uint8_t raw[AD7606_DOUTA_FRAME_BYTES] = {0};

    const int busy_before = gpio_get_level(GPIO_ADC_BUSY);
    gpio_set_level(GPIO_ADC_CONVST, 0);
    esp_rom_delay_us(1);
    const int busy_while_convst_low = gpio_get_level(GPIO_ADC_BUSY);
    adc_busy_rise_latched = false;
    gpio_set_level(GPIO_ADC_CONVST, 1);
    const int busy_immediate = gpio_get_level(GPIO_ADC_BUSY);

    const int64_t rise_wait_started_us = esp_timer_get_time();
    if (busy_immediate != 1 &&
        !wait_for_adc_busy_rise(CONFIG_LC_AD7606_BUSY_TIMEOUT_US)) {
        ESP_LOGE(
            TAG,
            "ADC_BUSY_RISE_TIMEOUT busy_before=%d busy_convst_low=%d "
            "busy_immediate=%d busy_latched=%d busy_after=%d elapsed_us=%" PRId64,
            busy_before,
            busy_while_convst_low,
            busy_immediate,
            adc_busy_rise_latched,
            gpio_get_level(GPIO_ADC_BUSY),
            esp_timer_get_time() - rise_wait_started_us
        );
        return LASER_FAULT_ADC_BUSY_RISE_TIMEOUT;
    }
    const int64_t busy_rise_us = esp_timer_get_time() - rise_wait_started_us;
    const int64_t fall_wait_started_us = esp_timer_get_time();
    if (!wait_for_gpio_level(GPIO_ADC_BUSY, 0, CONFIG_LC_AD7606_BUSY_TIMEOUT_US)) {
        ESP_LOGE(
            TAG,
            "ADC_BUSY_FALL_TIMEOUT busy_rise_us=%" PRId64 " busy_after=%d "
            "elapsed_us=%" PRId64,
            busy_rise_us,
            gpio_get_level(GPIO_ADC_BUSY),
            esp_timer_get_time() - fall_wait_started_us
        );
        return LASER_FAULT_ADC_BUSY_FALL_TIMEOUT;
    }

    spi_transaction_t transaction = {
        .flags = 0,
        .length = 0,
        .rxlength = AD7606_DOUTA_FRAME_BYTES * 8U,
        .rx_buffer = raw,
    };
    const esp_err_t error = spi_device_polling_transmit(adc_spi, &transaction);
    if (error != ESP_OK) {
        return LASER_FAULT_ADC_SPI;
    }

    ad7606_decode_douta_frame(raw, sample);
    return LASER_FAULT_NONE;
}

static void latch_fault(laser_fault_t fault)
{
    force_all_lasers_off();
    laser_safety_latch_fault(&safety, fault);
    ESP_LOGE(TAG, "FAULT_LATCHED fault_mask=0x%08" PRIx32, safety.fault_mask);
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
    laser_web_publish_fault(safety.fault_mask);
    laser_web_rollback_if_pending("laser-controller safety fault during OTA validation");
#endif
}

static void log_boot_metadata(void)
{
    const esp_app_desc_t *app = esp_app_get_description();
    static const char HEX_DIGITS[] = "0123456789abcdef";
    char elf_sha256_hex[sizeof(app->app_elf_sha256) * 2U + 1U];
    for (size_t index = 0; index < sizeof(app->app_elf_sha256); ++index) {
        elf_sha256_hex[index * 2U] = HEX_DIGITS[app->app_elf_sha256[index] >> 4U];
        elf_sha256_hex[index * 2U + 1U] =
            HEX_DIGITS[app->app_elf_sha256[index] & 0x0fU];
    }
    elf_sha256_hex[sizeof(elf_sha256_hex) - 1U] = '\0';
    ESP_LOGI(
        TAG,
        "firmware=%s version=%s idf=%s elf_sha256=%s reset_reason=%d",
        app->project_name,
        app->version,
        esp_get_idf_version(),
        elf_sha256_hex,
        (int)esp_reset_reason()
    );
    ESP_LOGI(
        TAG,
        "adc_mode=single_douta channels=4 frame_clocks=64 sclk_hz=%d "
        "sample_rate_hz=%d range=+/-5V oversampling=0 volts_per_lsb=%.12f",
        CONFIG_LC_AD7606_SCLK_HZ,
        CONFIG_LC_AD7606_SAMPLE_RATE_HZ,
        AD7606_VOLTS_PER_LSB
    );
#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
    ESP_LOGW(
        TAG,
        "laser-test profile enabled: local finite PULSE commands; no FACT hold required"
    );
#else
    ESP_LOGW(TAG, "laser outputs are inhibited; this bring-up firmware has no arm path");
#endif
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
    ESP_LOGW(
        TAG,
        "dashboard profile enabled: AP/STA web control, live telemetry, and OTA"
    );
#endif
}

#if CONFIG_LC_ENABLE_WEB_DASHBOARD
static void publish_web_snapshot(
    const ad7606_sample_t *sample,
    const laser_telemetry_t *telemetry
)
{
    laser_web_snapshot_t snapshot = {
        .sample_index = conversion_count,
        .timing_overruns = timing_overrun_count,
        .sampled_at_us = esp_timer_get_time(),
        .safety_state = safety.state,
        .fault_mask = safety.fault_mask,
        .active_mask = pulse.active ? pulse.channel_mask : 0U,
        .duty_permille = pulse.active ? pulse.duty_permille : 0U,
        .output_active = pulse.active,
        .output_latched = pulse.latched,
    };
    for (size_t channel = 0; channel < AD7606_CHANNEL_COUNT; ++channel) {
        snapshot.photodiode_counts[channel] = sample->counts[channel];
    }
    for (size_t channel = 0; channel < TELEMETRY_CHANNEL_COUNT; ++channel) {
        snapshot.telemetry_raw[channel] = telemetry->raw[channel];
        snapshot.telemetry_mv[channel] = telemetry->millivolts[channel];
    }
    for (size_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        snapshot.channel_duty_permille[channel] = pulse.active ?
            pulse.channel_duty_permille[channel] : 0U;
    }
    laser_web_publish_snapshot(&snapshot);
}
#endif

static void remain_fault_latched(void)
{
    for (;;) {
        force_all_lasers_off();
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void)
{
    laser_safety_init(&safety);

    esp_err_t error = configure_safe_gpio();
    if (error != ESP_OK) {
        ESP_LOGE(TAG, "safe GPIO initialization failed: %s", esp_err_to_name(error));
        laser_safety_latch_fault(&safety, LASER_FAULT_ADC_INIT);
        remain_fault_latched();
    }
    force_all_lasers_off();
    log_boot_metadata();

#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
    error = configure_laser_test_pwm();
    if (error == ESP_OK) {
        error = configure_telemetry_adc();
    }
    if (error == ESP_OK) {
        error = configure_test_command_transport();
    }
    if (error != ESP_OK) {
        ESP_LOGE(TAG, "laser-test peripheral initialization failed: %s", esp_err_to_name(error));
        latch_fault(LASER_FAULT_TELEMETRY_ADC);
        remain_fault_latched();
    }
#endif

    if ((1000U % CONFIG_LC_AD7606_SAMPLE_RATE_HZ) != 0U) {
        ESP_LOGE(
            TAG,
            "sample rate %d does not divide the 1000 Hz RTOS tick",
            CONFIG_LC_AD7606_SAMPLE_RATE_HZ
        );
        latch_fault(LASER_FAULT_ADC_INIT);
        remain_fault_latched();
    }

    error = initialize_adc_spi();
    if (error != ESP_OK) {
        ESP_LOGE(TAG, "ADC SPI initialization failed: %s", esp_err_to_name(error));
        latch_fault(LASER_FAULT_ADC_INIT);
        remain_fault_latched();
    }
    reset_adc();

    ad7606_sample_t sample = {0};
    laser_fault_t fault = acquire_sample(&sample);
    if (fault != LASER_FAULT_NONE) {
        latch_fault(fault);
        remain_fault_latched();
    }
    if (!laser_safety_mark_adc_ready(&safety)) {
        latch_fault(LASER_FAULT_ADC_INIT);
        remain_fault_latched();
    }

#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
    laser_telemetry_t telemetry = {0};
    error = read_telemetry(&telemetry);
    if (error != ESP_OK) {
        ESP_LOGE(TAG, "telemetry ADC initial read failed: %s", esp_err_to_name(error));
        latch_fault(LASER_FAULT_TELEMETRY_ADC);
        remain_fault_latched();
    }
    ESP_LOGI(TAG, "laser-test ready; use a bounded local PULSE command");
#endif

#if CONFIG_LC_ENABLE_WEB_DASHBOARD
    error = laser_web_start();
    if (error != ESP_OK) {
        ESP_LOGE(TAG, "dashboard initialization failed: %s", esp_err_to_name(error));
        latch_fault(LASER_FAULT_WEB_INIT);
        remain_fault_latched();
    }
    publish_web_snapshot(&sample, &telemetry);
#endif

    const TickType_t sample_period = pdMS_TO_TICKS(
        1000U / CONFIG_LC_AD7606_SAMPLE_RATE_HZ
    );
    TickType_t last_wake = xTaskGetTickCount();

    for (;;) {
#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
        bool command_processed = false;
#endif
        if (xTaskDelayUntil(&last_wake, sample_period) != pdTRUE) {
            ++timing_overrun_count;
#if CONFIG_LC_STRICT_SAMPLE_DEADLINE
            latch_fault(LASER_FAULT_ADC_TIMING_OVERRUN);
            remain_fault_latched();
#else
            last_wake = xTaskGetTickCount();
#endif
        }

#if CONFIG_LC_ENABLE_WEB_DASHBOARD
        if (laser_web_ota_in_progress() && pulse.active) {
            stop_output("ota");
        }
#endif

        const int64_t started_us = esp_timer_get_time();
        fault = acquire_sample(&sample);
        if (fault != LASER_FAULT_NONE) {
            latch_fault(fault);
            remain_fault_latched();
        }

#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
        error = read_telemetry(&telemetry);
        if (error != ESP_OK) {
            ESP_LOGE(TAG, "telemetry ADC read failed: %s", esp_err_to_name(error));
            latch_fault(LASER_FAULT_TELEMETRY_ADC);
            remain_fault_latched();
        }
        if (!update_pulse(&telemetry)) {
            remain_fault_latched();
        }
        command_processed = service_test_commands();
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
        laser_test_command_t web_command = {0};
        while (laser_web_receive_command(&web_command)) {
            apply_test_command(&web_command);
            command_processed = true;
        }
#endif
#endif

        ++conversion_count;
#if CONFIG_LC_ENABLE_WEB_DASHBOARD
        publish_web_snapshot(&sample, &telemetry);
#endif
#if CONFIG_LC_AD7606_LOG_EVERY_N > 0
        if ((conversion_count % CONFIG_LC_AD7606_LOG_EVERY_N) == 0U) {
            ESP_LOGI(
                TAG,
#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
                "S=%" PRIu64 " AD=%d,%d,%d,%d I=%d,%d,%d,%d "
                "M=%d,%d,%d,%d IRAW=%d,%d,%d,%d MRAW=%d,%d,%d,%d "
                "ST=%d F=%08" PRIx32 " P=%u,%u",
                conversion_count,
                sample.counts[0],
                sample.counts[1],
                sample.counts[2],
                sample.counts[3],
                telemetry.millivolts[0],
                telemetry.millivolts[1],
                telemetry.millivolts[2],
                telemetry.millivolts[3],
                telemetry.millivolts[4],
                telemetry.millivolts[5],
                telemetry.millivolts[6],
                telemetry.millivolts[7],
                telemetry.raw[0],
                telemetry.raw[1],
                telemetry.raw[2],
                telemetry.raw[3],
                telemetry.raw[4],
                telemetry.raw[5],
                telemetry.raw[6],
                telemetry.raw[7],
                (int)safety.state,
                safety.fault_mask,
                pulse.active ? pulse.channel_mask : 0U,
                pulse.duty_permille
#else
                "sample=%" PRIu64 " ch1=%d ch2=%d ch3=%d ch4=%d "
                "overruns=%" PRIu64 " faults=0x%08" PRIx32,
                conversion_count,
                sample.counts[0],
                sample.counts[1],
                sample.counts[2],
                sample.counts[3],
                timing_overrun_count,
                safety.fault_mask
#endif
            );
        }
#endif

        if (!laser_safety_outputs_permitted(&safety)) {
            force_all_lasers_off();
        }
#if CONFIG_LC_ENABLE_LASER_PULSE_TEST
        if (command_processed) {
            /* Command handling can emit multiple synchronous diagnostics and
             * intentionally exceed this one sampling period. Start a fresh
             * strict period after that bounded control-plane work. */
            last_wake = xTaskGetTickCount();
            continue;
        }
#endif
        const int64_t elapsed_us = esp_timer_get_time() - started_us;
        const int64_t period_us = 1000000LL / CONFIG_LC_AD7606_SAMPLE_RATE_HZ;
        if (elapsed_us >= period_us) {
            ++timing_overrun_count;
#if CONFIG_LC_STRICT_SAMPLE_DEADLINE
            latch_fault(LASER_FAULT_ADC_TIMING_OVERRUN);
            remain_fault_latched();
#endif
        }
    }
}
