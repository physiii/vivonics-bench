#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>

#include "driver/gpio.h"
#include "esp_attr.h"
#include "esp_err.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

enum {
    GPIO_PWM_IR = 10,
    GPIO_PWM_RED = 11,
    GPIO_PWM_GREEN = 12,
    GPIO_PWM_BLUE = 16,
    GPIO_ADC_CONVST = 15,
    GPIO_ADC_SCLK = 17,
    GPIO_ADC_CS = 18,
    GPIO_ADC_DOUTA = 21,
    GPIO_ADC_DOUTB = 38,
    GPIO_ADC_BUSY = 47,
    GPIO_ADC_RESET = 48,
    DIAGNOSTIC_CONVERSIONS = 8,
    CONTINUOUS_LOG_EVERY = 10,
};

typedef struct {
    int busy_before;
    int busy_immediate;
    int busy_after_1us;
    int busy_after_3us;
    uint32_t busy_edges;
    uint32_t douta;
    uint32_t doutb;
} conversion_observation_t;

static const char *TAG = "ad7606_diag";
static volatile uint32_t busy_edge_count;

static void IRAM_ATTR busy_edge_isr(void *argument)
{
    (void)argument;
    ++busy_edge_count;
}

static void force_lasers_off(void)
{
    gpio_set_level(GPIO_PWM_IR, 0);
    gpio_set_level(GPIO_PWM_RED, 0);
    gpio_set_level(GPIO_PWM_GREEN, 0);
    gpio_set_level(GPIO_PWM_BLUE, 0);
}

static esp_err_t configure_gpio(void)
{
    const gpio_config_t laser_outputs = {
        .pin_bit_mask = (1ULL << GPIO_PWM_IR) | (1ULL << GPIO_PWM_RED) |
                        (1ULL << GPIO_PWM_GREEN) | (1ULL << GPIO_PWM_BLUE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t error = gpio_config(&laser_outputs);
    if (error != ESP_OK) {
        return error;
    }
    force_lasers_off();

    const gpio_config_t adc_outputs = {
        .pin_bit_mask = (1ULL << GPIO_ADC_CONVST) | (1ULL << GPIO_ADC_SCLK) |
                        (1ULL << GPIO_ADC_CS) | (1ULL << GPIO_ADC_RESET),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    error = gpio_config(&adc_outputs);
    if (error != ESP_OK) {
        return error;
    }
    gpio_set_level(GPIO_ADC_CONVST, 0);
    gpio_set_level(GPIO_ADC_SCLK, 0);
    gpio_set_level(GPIO_ADC_CS, 1);
    gpio_set_level(GPIO_ADC_RESET, 0);

    const gpio_config_t adc_inputs = {
        .pin_bit_mask = (1ULL << GPIO_ADC_DOUTA) | (1ULL << GPIO_ADC_DOUTB) |
                        (1ULL << GPIO_ADC_BUSY),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    error = gpio_config(&adc_inputs);
    if (error != ESP_OK) {
        return error;
    }

    error = gpio_install_isr_service(ESP_INTR_FLAG_IRAM);
    if (error != ESP_OK && error != ESP_ERR_INVALID_STATE) {
        return error;
    }
    error = gpio_set_intr_type(GPIO_ADC_BUSY, GPIO_INTR_ANYEDGE);
    if (error != ESP_OK) {
        return error;
    }
    return gpio_isr_handler_add(GPIO_ADC_BUSY, busy_edge_isr, NULL);
}

static void reset_adc(uint32_t high_us)
{
    gpio_set_level(GPIO_ADC_RESET, 1);
    esp_rom_delay_us(high_us);
    gpio_set_level(GPIO_ADC_RESET, 0);
    esp_rom_delay_us(100);
}

static void read_serial_outputs(uint32_t *douta, uint32_t *doutb)
{
    uint32_t a = 0;
    uint32_t b = 0;

    gpio_set_level(GPIO_ADC_SCLK, 0);
    gpio_set_level(GPIO_ADC_CS, 0);
    esp_rom_delay_us(2);

    a = (uint32_t)gpio_get_level(GPIO_ADC_DOUTA);
    b = (uint32_t)gpio_get_level(GPIO_ADC_DOUTB);
    for (unsigned bit = 1; bit < 32; ++bit) {
        gpio_set_level(GPIO_ADC_SCLK, 1);
        esp_rom_delay_us(2);
        gpio_set_level(GPIO_ADC_SCLK, 0);
        esp_rom_delay_us(2);
        a = (a << 1U) | (uint32_t)gpio_get_level(GPIO_ADC_DOUTA);
        b = (b << 1U) | (uint32_t)gpio_get_level(GPIO_ADC_DOUTB);
    }
    gpio_set_level(GPIO_ADC_SCLK, 1);
    esp_rom_delay_us(2);
    gpio_set_level(GPIO_ADC_SCLK, 0);
    gpio_set_level(GPIO_ADC_CS, 1);

    *douta = a;
    *doutb = b;
}

static conversion_observation_t convert_and_read(void)
{
    conversion_observation_t observation = {0};
    observation.busy_before = gpio_get_level(GPIO_ADC_BUSY);

    gpio_set_level(GPIO_ADC_CONVST, 0);
    esp_rom_delay_us(10);
    const uint32_t edges_before = busy_edge_count;
    gpio_set_level(GPIO_ADC_CONVST, 1);
    observation.busy_immediate = gpio_get_level(GPIO_ADC_BUSY);
    esp_rom_delay_us(1);
    observation.busy_after_1us = gpio_get_level(GPIO_ADC_BUSY);
    esp_rom_delay_us(2);
    observation.busy_after_3us = gpio_get_level(GPIO_ADC_BUSY);
    esp_rom_delay_us(17);
    observation.busy_edges = busy_edge_count - edges_before;

    read_serial_outputs(&observation.douta, &observation.doutb);
    gpio_set_level(GPIO_ADC_CONVST, 1);
    return observation;
}

static const char *pull_name(gpio_pull_mode_t pull)
{
    switch (pull) {
    case GPIO_FLOATING:
        return "floating";
    case GPIO_PULLUP_ONLY:
        return "pullup";
    case GPIO_PULLDOWN_ONLY:
        return "pulldown";
    default:
        return "unexpected";
    }
}

static void run_pull_phase(gpio_pull_mode_t pull)
{
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_ADC_BUSY, pull));
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_ADC_DOUTA, pull));
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_ADC_DOUTB, pull));
    esp_rom_delay_us(1000);

    reset_adc(10);
    busy_edge_count = 0;
    const int busy_idle = gpio_get_level(GPIO_ADC_BUSY);
    const int douta_idle = gpio_get_level(GPIO_ADC_DOUTA);
    const int doutb_idle = gpio_get_level(GPIO_ADC_DOUTB);
    uint32_t total_edges = 0;
    unsigned busy_high_samples = 0;
    uint32_t douta_or = 0;
    uint32_t douta_and = UINT32_MAX;
    uint32_t doutb_or = 0;
    uint32_t doutb_and = UINT32_MAX;

    ESP_LOGI(
        TAG,
        "PHASE_BEGIN pull=%s idle_busy=%d idle_douta=%d idle_doutb=%d",
        pull_name(pull),
        busy_idle,
        douta_idle,
        doutb_idle
    );

    for (unsigned index = 0; index < DIAGNOSTIC_CONVERSIONS; ++index) {
        const conversion_observation_t observation = convert_and_read();
        total_edges += observation.busy_edges;
        busy_high_samples += (unsigned)observation.busy_before +
                             (unsigned)observation.busy_immediate +
                             (unsigned)observation.busy_after_1us +
                             (unsigned)observation.busy_after_3us;
        douta_or |= observation.douta;
        douta_and &= observation.douta;
        doutb_or |= observation.doutb;
        doutb_and &= observation.doutb;
        if (index < 2U) {
            ESP_LOGI(
                TAG,
                "OBS pull=%s n=%u busy=%d,%d,%d,%d edges=%" PRIu32
                " douta=%08" PRIx32 " doutb=%08" PRIx32,
                pull_name(pull),
                index,
                observation.busy_before,
                observation.busy_immediate,
                observation.busy_after_1us,
                observation.busy_after_3us,
                observation.busy_edges,
                observation.douta,
                observation.doutb
            );
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    ESP_LOGI(
        TAG,
        "PHASE_END pull=%s conversions=%u busy_edges=%" PRIu32
        " busy_high_samples=%u douta_or=%08" PRIx32
        " douta_and=%08" PRIx32 " doutb_or=%08" PRIx32
        " doutb_and=%08" PRIx32,
        pull_name(pull),
        DIAGNOSTIC_CONVERSIONS,
        total_edges,
        busy_high_samples,
        douta_or,
        douta_and,
        doutb_or,
        doutb_and
    );
}

void app_main(void)
{
    ESP_ERROR_CHECK(configure_gpio());
    force_lasers_off();
    ESP_LOGW(TAG, "DIAGNOSTIC_ONLY lasers_forced_off=1 no_arm_path=1");
    ESP_LOGI(
        TAG,
        "PINMAP convst=%d reset=%d busy=%d cs=%d sclk=%d douta=%d doutb=%d",
        GPIO_ADC_CONVST,
        GPIO_ADC_RESET,
        GPIO_ADC_BUSY,
        GPIO_ADC_CS,
        GPIO_ADC_SCLK,
        GPIO_ADC_DOUTA,
        GPIO_ADC_DOUTB
    );

    run_pull_phase(GPIO_FLOATING);
    run_pull_phase(GPIO_PULLUP_ONLY);
    run_pull_phase(GPIO_PULLDOWN_ONLY);

    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_ADC_BUSY, GPIO_FLOATING));
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_ADC_DOUTA, GPIO_FLOATING));
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_ADC_DOUTB, GPIO_FLOATING));
    reset_adc(10);
    busy_edge_count = 0;
    ESP_LOGI(TAG, "CONTINUOUS_BEGIN period_ms=100 scope_trigger=CONVST_rising");

    uint32_t conversion = 0;
    for (;;) {
        force_lasers_off();
        const conversion_observation_t observation = convert_and_read();
        ++conversion;
        if ((conversion % CONTINUOUS_LOG_EVERY) == 0U) {
            ESP_LOGI(
                TAG,
                "CONT n=%" PRIu32 " busy=%d,%d,%d,%d edges=%" PRIu32
                " total_edges=%" PRIu32 " douta=%08" PRIx32
                " doutb=%08" PRIx32,
                conversion,
                observation.busy_before,
                observation.busy_immediate,
                observation.busy_after_1us,
                observation.busy_after_3us,
                observation.busy_edges,
                busy_edge_count,
                observation.douta,
                observation.doutb
            );
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
