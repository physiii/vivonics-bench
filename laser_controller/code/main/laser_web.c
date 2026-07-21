#include "laser_web.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cJSON.h"
#include "esp_app_desc.h"
#include "esp_event.h"
#include "esp_heap_caps.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_ota_ops.h"
#include "esp_partition.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "nvs.h"
#include "nvs_flash.h"

enum {
    WEB_COMMAND_QUEUE_LENGTH = 8,
    WEB_LOG_CAPACITY = 32,
    WEB_LOG_MESSAGE_CAPACITY = 112,
    WEB_JSON_BODY_CAPACITY = 512,
    WEB_ASSET_CHUNK_BYTES = 4096,
    WEB_OTA_BUFFER_BYTES = 4096,
    WEB_OTA_REBOOT_DELAY_MS = 1500,
    WEB_OTA_VALIDATION_DELAY_MS = 10000,
};

typedef struct {
    uint32_t timestamp_ms;
    char message[WEB_LOG_MESSAGE_CAPACITY];
} laser_web_log_entry_t;

static const char *TAG = "laser_web";
static const char *const LASER_NAMES[LASER_TEST_CHANNEL_COUNT] = {
    "Infrared",
    "Red",
    "Green",
    "Blue",
};
static const unsigned LASER_WAVELENGTHS_NM[LASER_TEST_CHANNEL_COUNT] = {
    780,
    650,
    520,
    450,
};
static const unsigned LASER_PWM_GPIOS[LASER_TEST_CHANNEL_COUNT] = {
    10,
    11,
    12,
    16,
};

static QueueHandle_t s_command_queue;
static SemaphoreHandle_t s_snapshot_mutex;
static SemaphoreHandle_t s_log_mutex;
static SemaphoreHandle_t s_ota_mutex;
static laser_web_snapshot_t s_snapshot;
static bool s_snapshot_valid;
static laser_web_log_entry_t s_logs[WEB_LOG_CAPACITY];
static size_t s_log_head;
static size_t s_log_count;
static httpd_handle_t s_server;
static esp_netif_t *s_ap_netif;
static esp_netif_t *s_sta_netif;
static volatile bool s_sta_connected;
static volatile bool s_ota_in_progress;
static char s_device_id[24] = "laser-controller";
static char s_ap_ssid[33] = "VIVONICS-LASER";
static char s_saved_ssid[33];
static char s_saved_password[65];

static const char *safety_state_name(laser_state_t state)
{
    switch (state) {
        case LASER_STATE_BOOT_SAFE:
            return "boot-safe";
        case LASER_STATE_ADC_READY_LASERS_INHIBITED:
            return "ready-lasers-off";
        case LASER_STATE_ARMED:
            return "armed";
        case LASER_STATE_RUN:
            return "running";
        case LASER_STATE_FAULT_LATCHED:
            return "fault-latched";
        default:
            return "unknown";
    }
}

static const char *reset_reason_name(esp_reset_reason_t reason)
{
    switch (reason) {
        case ESP_RST_POWERON:
            return "Power-on";
        case ESP_RST_SW:
            return "Software reset";
        case ESP_RST_PANIC:
            return "Panic";
        case ESP_RST_INT_WDT:
            return "Interrupt watchdog";
        case ESP_RST_TASK_WDT:
            return "Task watchdog";
        case ESP_RST_WDT:
            return "Watchdog";
        case ESP_RST_DEEPSLEEP:
            return "Deep sleep";
        case ESP_RST_BROWNOUT:
            return "Brownout";
        default:
            return "Other";
    }
}

static const char *ota_state_name(esp_ota_img_states_t state)
{
    switch (state) {
        case ESP_OTA_IMG_NEW:
            return "new";
        case ESP_OTA_IMG_PENDING_VERIFY:
            return "pending-verify";
        case ESP_OTA_IMG_VALID:
            return "valid";
        case ESP_OTA_IMG_INVALID:
            return "invalid";
        case ESP_OTA_IMG_ABORTED:
            return "aborted";
        default:
            return "undefined";
    }
}

static const char *wifi_auth_name(wifi_auth_mode_t auth_mode)
{
    switch (auth_mode) {
        case WIFI_AUTH_OPEN:
            return "Open";
        case WIFI_AUTH_WEP:
            return "WEP";
        case WIFI_AUTH_WPA_PSK:
            return "WPA";
        case WIFI_AUTH_WPA2_PSK:
            return "WPA2";
        case WIFI_AUTH_WPA_WPA2_PSK:
            return "WPA/WPA2";
        case WIFI_AUTH_WPA3_PSK:
            return "WPA3";
        case WIFI_AUTH_WPA2_WPA3_PSK:
            return "WPA2/WPA3";
        default:
            return "Unknown";
    }
}

static unsigned wifi_quality_from_rssi(int rssi)
{
    if (rssi <= -100) {
        return 0;
    }
    if (rssi >= -50) {
        return 100;
    }
    return (unsigned)(2 * (rssi + 100));
}

void laser_web_record_event(const char *message)
{
    if (message == NULL || message[0] == '\0' || s_log_mutex == NULL) {
        return;
    }
    if (xSemaphoreTake(s_log_mutex, pdMS_TO_TICKS(50)) != pdTRUE) {
        return;
    }
    laser_web_log_entry_t *entry = &s_logs[s_log_head];
    entry->timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL);
    strlcpy(entry->message, message, sizeof(entry->message));
    s_log_head = (s_log_head + 1U) % WEB_LOG_CAPACITY;
    if (s_log_count < WEB_LOG_CAPACITY) {
        ++s_log_count;
    }
    xSemaphoreGive(s_log_mutex);
}

void laser_web_publish_snapshot(const laser_web_snapshot_t *snapshot)
{
    if (snapshot == NULL || s_snapshot_mutex == NULL) {
        return;
    }
    if (xSemaphoreTake(s_snapshot_mutex, pdMS_TO_TICKS(5)) == pdTRUE) {
        s_snapshot = *snapshot;
        s_snapshot_valid = true;
        xSemaphoreGive(s_snapshot_mutex);
    }
}

void laser_web_publish_fault(uint32_t fault_mask)
{
    if (s_snapshot_mutex == NULL) {
        return;
    }
    if (xSemaphoreTake(s_snapshot_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
        s_snapshot.sampled_at_us = esp_timer_get_time();
        s_snapshot.safety_state = LASER_STATE_FAULT_LATCHED;
        s_snapshot.fault_mask = fault_mask;
        s_snapshot.active_mask = 0U;
        s_snapshot.duty_permille = 0U;
        s_snapshot.output_active = false;
        s_snapshot.output_latched = false;
        s_snapshot_valid = true;
        xSemaphoreGive(s_snapshot_mutex);
    }
    char event[64];
    snprintf(event, sizeof(event), "Safety fault latched: 0x%08" PRIx32, fault_mask);
    laser_web_record_event(event);
}

static bool read_snapshot(laser_web_snapshot_t *snapshot)
{
    if (snapshot == NULL || s_snapshot_mutex == NULL) {
        return false;
    }
    bool valid = false;
    if (xSemaphoreTake(s_snapshot_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
        if (s_snapshot_valid) {
            *snapshot = s_snapshot;
            valid = true;
        }
        xSemaphoreGive(s_snapshot_mutex);
    }
    return valid;
}

bool laser_web_receive_command(laser_test_command_t *command)
{
    return command != NULL && s_command_queue != NULL &&
        xQueueReceive(s_command_queue, command, 0) == pdTRUE;
}

bool laser_web_ota_in_progress(void)
{
    return s_ota_in_progress;
}

static esp_err_t initialize_nvs(void)
{
    esp_err_t error = nvs_flash_init();
    if (error == ESP_ERR_NVS_NO_FREE_PAGES ||
        error == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        error = nvs_flash_erase();
        if (error == ESP_OK) {
            error = nvs_flash_init();
        }
    }
    return error;
}

static void load_wifi_credentials(void)
{
    s_saved_ssid[0] = '\0';
    s_saved_password[0] = '\0';
    nvs_handle_t handle;
    if (nvs_open("laser_network", NVS_READONLY, &handle) != ESP_OK) {
        return;
    }
    size_t ssid_size = sizeof(s_saved_ssid);
    size_t password_size = sizeof(s_saved_password);
    const esp_err_t ssid_error = nvs_get_str(
        handle,
        "ssid",
        s_saved_ssid,
        &ssid_size
    );
    const esp_err_t password_error = nvs_get_str(
        handle,
        "password",
        s_saved_password,
        &password_size
    );
    if (ssid_error != ESP_OK || password_error != ESP_OK) {
        s_saved_ssid[0] = '\0';
        s_saved_password[0] = '\0';
    }
    nvs_close(handle);
}

static esp_err_t store_wifi_credentials(const char *ssid, const char *password)
{
    nvs_handle_t handle;
    esp_err_t error = nvs_open("laser_network", NVS_READWRITE, &handle);
    if (error != ESP_OK) {
        return error;
    }
    error = nvs_set_str(handle, "ssid", ssid);
    if (error == ESP_OK) {
        error = nvs_set_str(handle, "password", password);
    }
    if (error == ESP_OK) {
        error = nvs_commit(handle);
    }
    nvs_close(handle);
    return error;
}

static esp_err_t apply_station_credentials(const char *ssid, const char *password)
{
    wifi_config_t config = {0};
    strlcpy((char *)config.sta.ssid, ssid, sizeof(config.sta.ssid));
    strlcpy((char *)config.sta.password, password, sizeof(config.sta.password));
    config.sta.threshold.authmode = WIFI_AUTH_OPEN;
    config.sta.pmf_cfg.capable = true;
    config.sta.pmf_cfg.required = false;

    esp_err_t error = esp_wifi_set_config(WIFI_IF_STA, &config);
    if (error != ESP_OK) {
        return error;
    }
    esp_wifi_disconnect();
    error = esp_wifi_connect();
    if (error == ESP_ERR_WIFI_CONN) {
        return ESP_OK;
    }
    return error;
}

esp_err_t laser_web_save_wifi_credentials(const char *ssid, const char *password)
{
    if (ssid == NULL || password == NULL || ssid[0] == '\0' ||
        strlen(ssid) > 32U || strlen(password) > 64U) {
        return ESP_ERR_INVALID_ARG;
    }
    esp_err_t error = store_wifi_credentials(ssid, password);
    if (error != ESP_OK) {
        return error;
    }
    strlcpy(s_saved_ssid, ssid, sizeof(s_saved_ssid));
    strlcpy(s_saved_password, password, sizeof(s_saved_password));
    error = apply_station_credentials(s_saved_ssid, s_saved_password);
    if (error == ESP_OK) {
        char event[80];
        snprintf(event, sizeof(event), "Wi-Fi credentials saved for %.32s", ssid);
        laser_web_record_event(event);
    }
    return error;
}

static void wifi_event_handler(
    void *argument,
    esp_event_base_t event_base,
    int32_t event_id,
    void *event_data
)
{
    (void)argument;
    if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        const ip_event_got_ip_t *event = event_data;
        s_sta_connected = true;
        char message[80];
        snprintf(
            message,
            sizeof(message),
            "Wi-Fi connected at " IPSTR,
            IP2STR(&event->ip_info.ip)
        );
        ESP_LOGI(TAG, "%s", message);
        laser_web_record_event(message);
        return;
    }
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        s_sta_connected = false;
        if (s_saved_ssid[0] != '\0') {
            esp_wifi_connect();
        }
    }
}

static esp_err_t start_wifi(void)
{
    esp_err_t error = esp_netif_init();
    if (error != ESP_OK && error != ESP_ERR_INVALID_STATE) {
        return error;
    }
    error = esp_event_loop_create_default();
    if (error != ESP_OK && error != ESP_ERR_INVALID_STATE) {
        return error;
    }

    s_ap_netif = esp_netif_create_default_wifi_ap();
    s_sta_netif = esp_netif_create_default_wifi_sta();
    if (s_ap_netif == NULL || s_sta_netif == NULL) {
        return ESP_ERR_NO_MEM;
    }

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    error = esp_wifi_init(&init_config);
    if (error != ESP_OK) {
        return error;
    }
    error = esp_wifi_set_storage(WIFI_STORAGE_RAM);
    if (error != ESP_OK) {
        return error;
    }
    error = esp_event_handler_register(
        WIFI_EVENT,
        ESP_EVENT_ANY_ID,
        wifi_event_handler,
        NULL
    );
    if (error != ESP_OK) {
        return error;
    }
    error = esp_event_handler_register(
        IP_EVENT,
        IP_EVENT_STA_GOT_IP,
        wifi_event_handler,
        NULL
    );
    if (error != ESP_OK) {
        return error;
    }

    uint8_t mac[6] = {0};
    error = esp_read_mac(mac, ESP_MAC_WIFI_STA);
    if (error != ESP_OK) {
        return error;
    }
    snprintf(
        s_device_id,
        sizeof(s_device_id),
        "laser-%02x%02x%02x%02x%02x%02x",
        mac[0],
        mac[1],
        mac[2],
        mac[3],
        mac[4],
        mac[5]
    );
    snprintf(
        s_ap_ssid,
        sizeof(s_ap_ssid),
        "VIVONICS-LASER-%02X%02X%02X",
        mac[3],
        mac[4],
        mac[5]
    );

    wifi_config_t ap_config = {
        .ap = {
            .channel = 6,
            .authmode = WIFI_AUTH_WPA2_PSK,
            .max_connection = 4,
            .pmf_cfg = {
                .required = false,
            },
        },
    };
    strlcpy((char *)ap_config.ap.ssid, s_ap_ssid, sizeof(ap_config.ap.ssid));
    ap_config.ap.ssid_len = strlen(s_ap_ssid);
    strlcpy((char *)ap_config.ap.password, "vivonics", sizeof(ap_config.ap.password));

    error = esp_wifi_set_mode(WIFI_MODE_APSTA);
    if (error == ESP_OK) {
        error = esp_wifi_set_config(WIFI_IF_AP, &ap_config);
    }
    if (error == ESP_OK) {
        error = esp_wifi_start();
    }
    if (error != ESP_OK) {
        return error;
    }
    esp_wifi_set_ps(WIFI_PS_NONE);

    load_wifi_credentials();
    if (s_saved_ssid[0] != '\0') {
        error = apply_station_credentials(s_saved_ssid, s_saved_password);
        if (error != ESP_OK) {
            ESP_LOGW(TAG, "Saved Wi-Fi connection start failed: %s", esp_err_to_name(error));
        }
    }

    char message[80];
    snprintf(message, sizeof(message), "Provisioning AP started: %s", s_ap_ssid);
    laser_web_record_event(message);
    ESP_LOGI(TAG, "%s at http://192.168.4.1/", message);
    return ESP_OK;
}

static void add_ip_string(cJSON *object, const char *key, esp_netif_t *netif)
{
    esp_netif_ip_info_t info = {0};
    if (netif != NULL && esp_netif_get_ip_info(netif, &info) == ESP_OK &&
        info.ip.addr != 0U) {
        char address[16];
        snprintf(address, sizeof(address), IPSTR, IP2STR(&info.ip));
        cJSON_AddStringToObject(object, key, address);
    } else {
        cJSON_AddNullToObject(object, key);
    }
}

static void add_mac_string(cJSON *object, const char *key, esp_mac_type_t type)
{
    uint8_t mac[6] = {0};
    if (esp_read_mac(mac, type) == ESP_OK) {
        char value[18];
        snprintf(value, sizeof(value), MACSTR, MAC2STR(mac));
        cJSON_AddStringToObject(object, key, value);
    } else {
        cJSON_AddNullToObject(object, key);
    }
}

static cJSON *build_network_object(void)
{
    cJSON *network = cJSON_CreateObject();
    if (network == NULL) {
        return NULL;
    }
    add_ip_string(network, "wifi_ap_ip", s_ap_netif);
    add_ip_string(network, "wifi_sta_ip", s_sta_netif);
    add_mac_string(network, "wifi_sta_mac", ESP_MAC_WIFI_STA);
    add_mac_string(network, "wifi_ap_mac", ESP_MAC_WIFI_SOFTAP);
    cJSON_AddStringToObject(network, "wifi_ap_ssid", s_ap_ssid);
    cJSON_AddBoolToObject(network, "wifi_sta_connected", s_sta_connected);
    cJSON_AddStringToObject(network, "active_ssid", s_saved_ssid);

    wifi_ap_record_t record = {0};
    if (s_sta_connected && esp_wifi_sta_get_ap_info(&record) == ESP_OK) {
        cJSON_AddNumberToObject(network, "wifi_sta_rssi", record.rssi);
        cJSON_AddNumberToObject(
            network,
            "wifi_sta_quality",
            wifi_quality_from_rssi(record.rssi)
        );
        cJSON_AddNumberToObject(network, "wifi_sta_channel", record.primary);
        cJSON_AddStringToObject(network, "wifi_sta_auth", wifi_auth_name(record.authmode));
        char bssid[18];
        snprintf(bssid, sizeof(bssid), MACSTR, MAC2STR(record.bssid));
        cJSON_AddStringToObject(network, "wifi_sta_bssid", bssid);
    }
    return network;
}

static void add_firmware_object(cJSON *parent)
{
    const esp_app_desc_t *app = esp_app_get_description();
    const esp_partition_t *running = esp_ota_get_running_partition();
    const esp_partition_t *boot = esp_ota_get_boot_partition();
    const esp_partition_t *next = esp_ota_get_next_update_partition(NULL);
    cJSON *firmware = cJSON_CreateObject();
    if (firmware == NULL) {
        return;
    }

    cJSON_AddStringToObject(firmware, "projectName", app->project_name);
    cJSON_AddStringToObject(firmware, "projectVersion", app->version);
    cJSON_AddStringToObject(firmware, "idfVersion", app->idf_ver);
    cJSON_AddStringToObject(firmware, "buildDate", app->date);
    cJSON_AddStringToObject(firmware, "buildTime", app->time);

    char sha[17];
    for (size_t index = 0; index < 8U; ++index) {
        snprintf(&sha[index * 2U], 3U, "%02x", app->app_elf_sha256[index]);
    }
    sha[16] = '\0';
    cJSON_AddStringToObject(firmware, "elfSha256", sha);
    cJSON_AddStringToObject(firmware, "runningPartition", running ? running->label : "unknown");
    cJSON_AddStringToObject(firmware, "bootPartition", boot ? boot->label : "unknown");
    cJSON_AddStringToObject(firmware, "nextUpdatePartition", next ? next->label : "none");
    cJSON_AddNumberToObject(firmware, "otaPartitionCount", esp_ota_get_app_partition_count());
    cJSON_AddBoolToObject(firmware, "rollbackEnabled", true);
    cJSON_AddNumberToObject(firmware, "maxUploadBytes", next ? next->size : 0U);

    esp_ota_img_states_t state = ESP_OTA_IMG_UNDEFINED;
    if (running != NULL && esp_ota_get_state_partition(running, &state) == ESP_OK) {
        cJSON_AddStringToObject(firmware, "otaState", ota_state_name(state));
    } else {
        cJSON_AddStringToObject(firmware, "otaState", "undefined");
    }
    cJSON_AddItemToObject(parent, "firmware", firmware);
}

static cJSON *build_telemetry_object(void)
{
    laser_web_snapshot_t snapshot = {0};
    const bool valid = read_snapshot(&snapshot);
    cJSON *root = cJSON_CreateObject();
    if (root == NULL) {
        return NULL;
    }
    cJSON_AddBoolToObject(root, "ok", valid);
    if (!valid) {
        return root;
    }

    cJSON_AddNumberToObject(root, "sampleIndex", (double)snapshot.sample_index);
    cJSON_AddNumberToObject(root, "sampledAtUs", (double)snapshot.sampled_at_us);
    cJSON_AddNumberToObject(root, "sampleRateHz", CONFIG_LC_AD7606_SAMPLE_RATE_HZ);
    cJSON_AddNumberToObject(root, "timingOverruns", (double)snapshot.timing_overruns);
    cJSON_AddStringToObject(root, "safetyState", safety_state_name(snapshot.safety_state));
    cJSON_AddNumberToObject(root, "faultMask", snapshot.fault_mask);

    cJSON *output = cJSON_CreateObject();
    cJSON_AddBoolToObject(output, "active", snapshot.output_active);
    cJSON_AddBoolToObject(output, "latched", snapshot.output_latched);
    cJSON_AddNumberToObject(output, "channelMask", snapshot.active_mask);
    cJSON_AddStringToObject(
        output,
        "target",
        snapshot.output_active ? laser_test_target_name(snapshot.active_mask) : "OFF"
    );
    cJSON_AddNumberToObject(output, "dutyPermille", snapshot.duty_permille);
    cJSON_AddItemToObject(root, "output", output);

    cJSON *photodiodes = cJSON_CreateArray();
    for (size_t channel = 0; channel < LASER_WEB_PHOTODIODE_COUNT; ++channel) {
        cJSON *item = cJSON_CreateObject();
        cJSON_AddNumberToObject(item, "channel", channel + 1U);
        cJSON_AddStringToObject(item, "name", "Signal photodiode");
        cJSON_AddNumberToObject(item, "counts", snapshot.photodiode_counts[channel]);
        cJSON_AddNumberToObject(
            item,
            "volts",
            (double)snapshot.photodiode_counts[channel] * 5.0 / 32768.0
        );
        cJSON_AddItemToArray(photodiodes, item);
    }
    cJSON_AddItemToObject(root, "photodiodes", photodiodes);

    cJSON *lasers = cJSON_CreateArray();
    for (size_t channel = 0; channel < LASER_TEST_CHANNEL_COUNT; ++channel) {
        cJSON *item = cJSON_CreateObject();
        cJSON_AddNumberToObject(item, "channel", channel + 1U);
        cJSON_AddStringToObject(item, "target", laser_test_channel_name(channel));
        cJSON_AddStringToObject(item, "name", LASER_NAMES[channel]);
        cJSON_AddNumberToObject(item, "wavelengthNm", LASER_WAVELENGTHS_NM[channel]);
        cJSON_AddNumberToObject(item, "pwmGpio", LASER_PWM_GPIOS[channel]);
        cJSON_AddBoolToObject(
            item,
            "active",
            snapshot.output_active && (snapshot.active_mask & (1U << channel)) != 0U
        );

        cJSON *current = cJSON_CreateObject();
        cJSON_AddNumberToObject(current, "raw", snapshot.telemetry_raw[channel]);
        cJSON_AddNumberToObject(current, "millivolts", snapshot.telemetry_mv[channel]);
        cJSON_AddNumberToObject(
            current,
            "milliampsApprox",
            (double)snapshot.telemetry_mv[channel] / 10.0
        );
        cJSON_AddItemToObject(item, "currentSense", current);

        cJSON *monitor = cJSON_CreateObject();
        cJSON_AddNumberToObject(monitor, "raw", snapshot.telemetry_raw[channel + 4U]);
        cJSON_AddNumberToObject(monitor, "millivolts", snapshot.telemetry_mv[channel + 4U]);
        cJSON_AddItemToObject(item, "sourceMonitor", monitor);
        cJSON_AddItemToArray(lasers, item);
    }
    cJSON_AddItemToObject(root, "lasers", lasers);
    return root;
}

static cJSON *build_state_object(void)
{
    cJSON *root = cJSON_CreateObject();
    if (root == NULL) {
        return NULL;
    }
    cJSON_AddBoolToObject(root, "ok", true);
    cJSON *device = cJSON_CreateObject();
    cJSON_AddStringToObject(device, "uuid", s_device_id);
    cJSON_AddStringToObject(device, "name", "Vivonics Laser Controller");
    cJSON *network = build_network_object();
    if (network != NULL) {
        cJSON_AddItemToObject(device, "network", network);
    }
    cJSON_AddItemToObject(root, "device", device);

    cJSON *system = cJSON_CreateObject();
    cJSON_AddNumberToObject(system, "uptimeSeconds", esp_timer_get_time() / 1000000ULL);
    cJSON_AddNumberToObject(system, "freeHeap", esp_get_free_heap_size());
    cJSON_AddNumberToObject(system, "minFreeHeap", esp_get_minimum_free_heap_size());
    cJSON_AddNumberToObject(
        system,
        "largestFreeBlock",
        heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)
    );
    cJSON_AddStringToObject(system, "resetReason", reset_reason_name(esp_reset_reason()));
    add_firmware_object(system);
    cJSON_AddItemToObject(root, "system", system);

    cJSON *telemetry = build_telemetry_object();
    if (telemetry != NULL) {
        cJSON_AddItemToObject(root, "telemetry", telemetry);
    }
    return root;
}

static esp_err_t send_json(httpd_req_t *request, cJSON *root)
{
    if (root == NULL) {
        return httpd_resp_send_err(
            request,
            HTTPD_500_INTERNAL_SERVER_ERROR,
            "Unable to allocate response"
        );
    }
    char *serialized = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    if (serialized == NULL) {
        return httpd_resp_send_err(
            request,
            HTTPD_500_INTERNAL_SERVER_ERROR,
            "Unable to encode response"
        );
    }
    httpd_resp_set_type(request, "application/json");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store, no-cache, must-revalidate");
    httpd_resp_set_hdr(request, "Pragma", "no-cache");
    const esp_err_t error = httpd_resp_sendstr(request, serialized);
    free(serialized);
    return error;
}

static esp_err_t send_status_text(
    httpd_req_t *request,
    const char *status,
    const char *message
)
{
    httpd_resp_set_status(request, status);
    httpd_resp_set_type(request, "text/plain");
    return httpd_resp_sendstr(request, message);
}

static esp_err_t read_json_body(httpd_req_t *request, cJSON **payload)
{
    if (request == NULL || payload == NULL || request->content_len <= 0 ||
        request->content_len >= WEB_JSON_BODY_CAPACITY) {
        return ESP_ERR_INVALID_ARG;
    }
    char body[WEB_JSON_BODY_CAPACITY];
    size_t received_total = 0;
    while (received_total < (size_t)request->content_len) {
        const int received = httpd_req_recv(
            request,
            body + received_total,
            request->content_len - received_total
        );
        if (received == HTTPD_SOCK_ERR_TIMEOUT) {
            continue;
        }
        if (received <= 0) {
            return ESP_FAIL;
        }
        received_total += (size_t)received;
    }
    body[received_total] = '\0';
    *payload = cJSON_Parse(body);
    return *payload == NULL ? ESP_ERR_INVALID_ARG : ESP_OK;
}

static esp_err_t send_asset(
    httpd_req_t *request,
    const unsigned char *start,
    const unsigned char *end,
    const char *content_type
)
{
    httpd_resp_set_type(request, content_type);
    httpd_resp_set_hdr(request, "Cache-Control", "no-store, no-cache, must-revalidate");
    httpd_resp_set_hdr(request, "Pragma", "no-cache");
    const size_t size = (size_t)(end - start);
    if (size <= 32768U) {
        return httpd_resp_send(request, (const char *)start, size);
    }
    size_t offset = 0;
    while (offset < size) {
        const size_t remaining = size - offset;
        const size_t chunk = remaining > WEB_ASSET_CHUNK_BYTES ?
            WEB_ASSET_CHUNK_BYTES : remaining;
        const esp_err_t error = httpd_resp_send_chunk(
            request,
            (const char *)(start + offset),
            chunk
        );
        if (error != ESP_OK) {
            return error;
        }
        offset += chunk;
        vTaskDelay(1);
    }
    return httpd_resp_send_chunk(request, NULL, 0);
}

static esp_err_t index_handler(httpd_req_t *request)
{
    extern const unsigned char index_start[] asm("_binary_index_html_start");
    extern const unsigned char index_end[] asm("_binary_index_html_end");
    return send_asset(request, index_start, index_end, "text/html");
}

static esp_err_t script_handler(httpd_req_t *request)
{
    extern const unsigned char script_start[] asm("_binary_script_js_start");
    extern const unsigned char script_end[] asm("_binary_script_js_end");
    return send_asset(request, script_start, script_end, "application/javascript");
}

static esp_err_t style_handler(httpd_req_t *request)
{
    extern const unsigned char style_start[] asm("_binary_style_css_start");
    extern const unsigned char style_end[] asm("_binary_style_css_end");
    return send_asset(request, style_start, style_end, "text/css");
}

static esp_err_t favicon_handler(httpd_req_t *request)
{
    extern const unsigned char favicon_start[] asm("_binary_favicon_svg_start");
    extern const unsigned char favicon_end[] asm("_binary_favicon_svg_end");
    return send_asset(request, favicon_start, favicon_end, "image/svg+xml");
}

static esp_err_t state_handler(httpd_req_t *request)
{
    return send_json(request, build_state_object());
}

static esp_err_t telemetry_handler(httpd_req_t *request)
{
    return send_json(request, build_telemetry_object());
}

static esp_err_t health_handler(httpd_req_t *request)
{
    laser_web_snapshot_t snapshot = {0};
    cJSON *root = cJSON_CreateObject();
    const bool valid = read_snapshot(&snapshot);
    cJSON_AddBoolToObject(root, "ok", valid && snapshot.fault_mask == 0U);
    cJSON_AddBoolToObject(root, "adcReady", valid);
    cJSON_AddNumberToObject(root, "faultMask", valid ? snapshot.fault_mask : -1);
    cJSON_AddBoolToObject(root, "otaInProgress", s_ota_in_progress);
    return send_json(request, root);
}

static esp_err_t discovery_handler(httpd_req_t *request)
{
    cJSON *root = cJSON_CreateObject();
    cJSON_AddBoolToObject(root, "ok", true);
    cJSON_AddStringToObject(root, "service", "vivonics-laser-controller");
    cJSON_AddStringToObject(root, "deviceKind", "laser_controller");
    cJSON_AddStringToObject(root, "name", "Vivonics Laser Controller");

    cJSON *device = cJSON_CreateObject();
    cJSON_AddStringToObject(device, "uuid", s_device_id);
    cJSON *network = build_network_object();
    if (network != NULL) {
        cJSON_AddItemToObject(device, "network", network);
    }
    cJSON_AddItemToObject(root, "device", device);

    cJSON *capabilities = cJSON_CreateArray();
    const char *const items[] = {
        "laser-control",
        "ad7606",
        "photodiode-telemetry",
        "current-sense",
        "source-monitor",
        "ota-upload",
        "rollback",
        "wifi-config",
        "web-ui",
    };
    for (size_t index = 0; index < sizeof(items) / sizeof(items[0]); ++index) {
        cJSON_AddItemToArray(capabilities, cJSON_CreateString(items[index]));
    }
    cJSON_AddItemToObject(root, "capabilities", capabilities);

    cJSON *api = cJSON_CreateObject();
    cJSON_AddStringToObject(api, "state", "/api/state");
    cJSON_AddStringToObject(api, "health", "/api/health");
    cJSON_AddStringToObject(api, "telemetry", "/api/telemetry");
    cJSON_AddStringToObject(api, "laserControl", "/api/lasers");
    cJSON_AddStringToObject(api, "allOff", "/api/lasers/off");
    cJSON_AddStringToObject(api, "otaUpload", "/api/ota/upload");
    cJSON_AddStringToObject(api, "logs", "/api/logs");
    cJSON_AddStringToObject(api, "wifi", "/api/wifi");
    cJSON_AddStringToObject(api, "wifiScan", "/api/wifi/scan");
    cJSON_AddStringToObject(api, "wifiList", "/api/wifi/list");
    cJSON_AddItemToObject(root, "api", api);

    cJSON *system = cJSON_CreateObject();
    cJSON_AddNumberToObject(system, "uptimeSeconds", esp_timer_get_time() / 1000000ULL);
    add_firmware_object(system);
    cJSON_AddItemToObject(root, "system", system);
    return send_json(request, root);
}

static esp_err_t logs_handler(httpd_req_t *request)
{
    cJSON *root = cJSON_CreateArray();
    if (root == NULL) {
        return send_json(request, NULL);
    }
    if (s_log_mutex != NULL &&
        xSemaphoreTake(s_log_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        for (size_t offset = 0; offset < s_log_count; ++offset) {
            const size_t index =
                (s_log_head + WEB_LOG_CAPACITY - 1U - offset) % WEB_LOG_CAPACITY;
            cJSON *item = cJSON_CreateObject();
            cJSON_AddNumberToObject(item, "timestamp", s_logs[index].timestamp_ms);
            cJSON_AddStringToObject(item, "message", s_logs[index].message);
            cJSON_AddItemToArray(root, item);
        }
        xSemaphoreGive(s_log_mutex);
    }
    return send_json(request, root);
}

static esp_err_t enqueue_command(const laser_test_command_t *command)
{
    if (s_command_queue == NULL || command == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    return xQueueSend(s_command_queue, command, pdMS_TO_TICKS(50)) == pdTRUE ?
        ESP_OK : ESP_ERR_TIMEOUT;
}

static esp_err_t laser_control_handler(httpd_req_t *request)
{
    if (s_ota_in_progress) {
        return send_status_text(request, "409 Conflict", "OTA update in progress");
    }
    cJSON *payload = NULL;
    if (read_json_body(request, &payload) != ESP_OK) {
        return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Invalid JSON payload");
    }
    const cJSON *target_item = cJSON_GetObjectItemCaseSensitive(payload, "target");
    const cJSON *duty_item = cJSON_GetObjectItemCaseSensitive(payload, "dutyPermille");
    const char *target = cJSON_IsString(target_item) ? target_item->valuestring : NULL;
    const int duty = cJSON_IsNumber(duty_item) ? duty_item->valueint : 0;

    char line[64];
    snprintf(line, sizeof(line), "ON %s %d", target ? target : "", duty);
    laser_test_command_t command = {0};
    const bool valid = laser_test_parse_command(line, &command);
    char target_copy[16] = {0};
    if (valid) {
        strlcpy(target_copy, target, sizeof(target_copy));
    }
    cJSON_Delete(payload);
    if (!valid) {
        return httpd_resp_send_err(
            request,
            HTTPD_400_BAD_REQUEST,
            "Target must be IR, RED, GREEN, BLUE, or IR_GREEN; duty must be 1..1000"
        );
    }
    if (enqueue_command(&command) != ESP_OK) {
        return send_status_text(request, "503 Service Unavailable", "Control queue is busy");
    }

    char event[96];
    snprintf(event, sizeof(event), "Laser command queued: %s at %.1f%%", target_copy, duty / 10.0);
    laser_web_record_event(event);
    cJSON *response = cJSON_CreateObject();
    cJSON_AddBoolToObject(response, "ok", true);
    cJSON_AddBoolToObject(response, "queued", true);
    cJSON_AddStringToObject(response, "target", target_copy);
    cJSON_AddNumberToObject(response, "dutyPermille", duty);
    return send_json(request, response);
}

static esp_err_t all_off_handler(httpd_req_t *request)
{
    laser_test_command_t command = {
        .type = LASER_TEST_COMMAND_OFF,
    };
    if (s_command_queue != NULL) {
        xQueueReset(s_command_queue);
    }
    if (enqueue_command(&command) != ESP_OK) {
        return send_status_text(request, "503 Service Unavailable", "Control queue is busy");
    }
    laser_web_record_event("All laser outputs switched off");
    cJSON *response = cJSON_CreateObject();
    cJSON_AddBoolToObject(response, "ok", true);
    cJSON_AddBoolToObject(response, "queued", true);
    return send_json(request, response);
}

static esp_err_t wifi_list_handler(httpd_req_t *request)
{
    cJSON *root = cJSON_CreateArray();
    if (s_saved_ssid[0] != '\0') {
        cJSON *item = cJSON_CreateObject();
        cJSON_AddStringToObject(item, "ssid", s_saved_ssid);
        cJSON_AddBoolToObject(item, "active", s_sta_connected);
        cJSON_AddItemToArray(root, item);
    }
    return send_json(request, root);
}

static esp_err_t wifi_scan_handler(httpd_req_t *request)
{
    wifi_scan_config_t scan_config = {0};
    esp_err_t error = esp_wifi_scan_start(&scan_config, true);
    if (error != ESP_OK) {
        return send_status_text(request, "503 Service Unavailable", "Wi-Fi scan failed");
    }
    uint16_t count = 0;
    esp_wifi_scan_get_ap_num(&count);
    if (count > 20U) {
        count = 20U;
    }
    wifi_ap_record_t *records = calloc(count == 0U ? 1U : count, sizeof(*records));
    if (records == NULL) {
        return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "No memory for scan results");
    }
    error = esp_wifi_scan_get_ap_records(&count, records);
    if (error != ESP_OK) {
        free(records);
        return send_status_text(request, "503 Service Unavailable", "Wi-Fi scan result failed");
    }
    cJSON *root = cJSON_CreateArray();
    for (uint16_t index = 0; index < count; ++index) {
        cJSON *item = cJSON_CreateObject();
        cJSON_AddStringToObject(item, "ssid", (const char *)records[index].ssid);
        cJSON_AddNumberToObject(item, "rssi", records[index].rssi);
        cJSON_AddNumberToObject(item, "channel", records[index].primary);
        cJSON_AddStringToObject(item, "auth", wifi_auth_name(records[index].authmode));
        cJSON_AddBoolToObject(item, "secure", records[index].authmode != WIFI_AUTH_OPEN);
        cJSON_AddItemToArray(root, item);
    }
    free(records);
    return send_json(request, root);
}

static esp_err_t wifi_config_handler(httpd_req_t *request)
{
    cJSON *payload = NULL;
    if (read_json_body(request, &payload) != ESP_OK) {
        return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Invalid JSON payload");
    }
    const cJSON *ssid_item = cJSON_GetObjectItemCaseSensitive(payload, "ssid");
    const cJSON *password_item = cJSON_GetObjectItemCaseSensitive(payload, "password");
    const char *ssid = cJSON_IsString(ssid_item) ? ssid_item->valuestring : NULL;
    const char *password = cJSON_IsString(password_item) ? password_item->valuestring : NULL;
    const esp_err_t error = laser_web_save_wifi_credentials(ssid, password);
    cJSON_Delete(payload);
    if (error != ESP_OK) {
        return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Unable to save Wi-Fi credentials");
    }
    cJSON *response = cJSON_CreateObject();
    cJSON_AddBoolToObject(response, "ok", true);
    cJSON_AddStringToObject(response, "ssid", s_saved_ssid);
    cJSON_AddBoolToObject(response, "connecting", true);
    return send_json(request, response);
}

static void ota_reboot_task(void *argument)
{
    (void)argument;
    vTaskDelay(pdMS_TO_TICKS(WEB_OTA_REBOOT_DELAY_MS));
    esp_restart();
}

static esp_err_t ota_upload_handler(httpd_req_t *request)
{
    if (request->content_len <= 0) {
        return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Firmware binary is required");
    }
    const esp_partition_t *partition = esp_ota_get_next_update_partition(NULL);
    if (partition == NULL) {
        return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "No OTA partition available");
    }
    if ((size_t)request->content_len > partition->size) {
        httpd_resp_set_status(request, "413 Payload Too Large");
        return httpd_resp_sendstr(request, "Firmware exceeds OTA partition size");
    }
    if (s_ota_mutex == NULL || xSemaphoreTake(s_ota_mutex, 0) != pdTRUE) {
        return send_status_text(request, "409 Conflict", "OTA update already in progress");
    }

    s_ota_in_progress = true;
    if (s_command_queue != NULL) {
        xQueueReset(s_command_queue);
        const laser_test_command_t off = {.type = LASER_TEST_COMMAND_OFF};
        xQueueSend(s_command_queue, &off, 0);
    }
    laser_web_record_event("OTA upload started; laser outputs inhibited");

    uint8_t *buffer = malloc(WEB_OTA_BUFFER_BYTES);
    if (buffer == NULL) {
        s_ota_in_progress = false;
        xSemaphoreGive(s_ota_mutex);
        return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "Unable to allocate OTA buffer");
    }
    esp_ota_handle_t handle = 0;
    esp_err_t error = esp_ota_begin(partition, request->content_len, &handle);
    if (error != ESP_OK) {
        free(buffer);
        s_ota_in_progress = false;
        xSemaphoreGive(s_ota_mutex);
        return send_status_text(request, "409 Conflict", "Unable to start OTA update");
    }

    int remaining = request->content_len;
    size_t written = 0;
    while (remaining > 0) {
        const int requested = remaining > WEB_OTA_BUFFER_BYTES ?
            WEB_OTA_BUFFER_BYTES : remaining;
        const int received = httpd_req_recv(request, (char *)buffer, requested);
        if (received == HTTPD_SOCK_ERR_TIMEOUT) {
            continue;
        }
        if (received <= 0) {
            esp_ota_abort(handle);
            free(buffer);
            s_ota_in_progress = false;
            xSemaphoreGive(s_ota_mutex);
            return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "Firmware receive failed");
        }
        error = esp_ota_write(handle, buffer, received);
        if (error != ESP_OK) {
            esp_ota_abort(handle);
            free(buffer);
            s_ota_in_progress = false;
            xSemaphoreGive(s_ota_mutex);
            return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Invalid ESP32 firmware image");
        }
        written += (size_t)received;
        remaining -= received;
    }
    free(buffer);

    error = esp_ota_end(handle);
    if (error == ESP_OK) {
        error = esp_ota_set_boot_partition(partition);
    }
    if (error != ESP_OK) {
        s_ota_in_progress = false;
        xSemaphoreGive(s_ota_mutex);
        return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Firmware validation failed");
    }

    esp_app_desc_t description = {0};
    const esp_err_t description_error = esp_ota_get_partition_description(
        partition,
        &description
    );
    laser_web_record_event("OTA firmware installed; reboot scheduled");

    cJSON *response = cJSON_CreateObject();
    cJSON_AddBoolToObject(response, "ok", true);
    cJSON_AddBoolToObject(response, "reboot", true);
    cJSON_AddNumberToObject(response, "bytes", written);
    cJSON_AddNumberToObject(response, "rebootDelayMs", WEB_OTA_REBOOT_DELAY_MS);
    cJSON_AddStringToObject(response, "partition", partition->label);
    if (description_error == ESP_OK) {
        cJSON_AddStringToObject(response, "projectName", description.project_name);
        cJSON_AddStringToObject(response, "projectVersion", description.version);
    }
    if (xTaskCreate(ota_reboot_task, "ota_reboot", 2048, NULL, 5, NULL) != pdPASS) {
        s_ota_in_progress = false;
        xSemaphoreGive(s_ota_mutex);
        cJSON_Delete(response);
        return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "Reboot task failed");
    }
    xSemaphoreGive(s_ota_mutex);
    return send_json(request, response);
}

static bool running_image_pending_verify(void)
{
#ifdef CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE
    const esp_partition_t *running = esp_ota_get_running_partition();
    esp_ota_img_states_t state = ESP_OTA_IMG_UNDEFINED;
    return running != NULL && esp_ota_get_state_partition(running, &state) == ESP_OK &&
        state == ESP_OTA_IMG_PENDING_VERIFY;
#else
    return false;
#endif
}

static void validate_running_image_task(void *argument)
{
    (void)argument;
    vTaskDelay(pdMS_TO_TICKS(WEB_OTA_VALIDATION_DELAY_MS));
#ifdef CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE
    if (running_image_pending_verify()) {
        const esp_err_t error = esp_ota_mark_app_valid_cancel_rollback();
        if (error == ESP_OK) {
            laser_web_record_event("OTA image marked valid after ADC and dashboard startup");
            ESP_LOGI(TAG, "OTA image marked valid");
        } else {
            ESP_LOGE(TAG, "Unable to mark OTA image valid: %s", esp_err_to_name(error));
        }
    }
#endif
    vTaskDelete(NULL);
}

bool laser_web_rollback_if_pending(const char *reason)
{
#ifdef CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE
    if (running_image_pending_verify()) {
        ESP_LOGE(TAG, "OTA startup validation failed: %s", reason ? reason : "unknown");
        esp_ota_mark_app_invalid_rollback_and_reboot();
        return true;
    }
#else
    (void)reason;
#endif
    return false;
}

static esp_err_t register_handler(
    const char *uri,
    httpd_method_t method,
    esp_err_t (*handler)(httpd_req_t *)
)
{
    const httpd_uri_t route = {
        .uri = uri,
        .method = method,
        .handler = handler,
    };
    return httpd_register_uri_handler(s_server, &route);
}

static esp_err_t start_http_server(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_uri_handlers = 20;
    config.stack_size = 12288;
    config.lru_purge_enable = true;
    config.recv_wait_timeout = 20;
    config.send_wait_timeout = 20;
    esp_err_t error = httpd_start(&s_server, &config);
    if (error != ESP_OK) {
        return error;
    }

    const struct {
        const char *uri;
        httpd_method_t method;
        esp_err_t (*handler)(httpd_req_t *);
    } routes[] = {
        {"/", HTTP_GET, index_handler},
        {"/index.html", HTTP_GET, index_handler},
        {"/script.js", HTTP_GET, script_handler},
        {"/style.css", HTTP_GET, style_handler},
        {"/favicon.svg", HTTP_GET, favicon_handler},
        {"/api/state", HTTP_GET, state_handler},
        {"/api/health", HTTP_GET, health_handler},
        {"/api/telemetry", HTTP_GET, telemetry_handler},
        {"/api/discovery", HTTP_GET, discovery_handler},
        {"/.well-known/laser-controller.json", HTTP_GET, discovery_handler},
        {"/api/logs", HTTP_GET, logs_handler},
        {"/api/lasers", HTTP_POST, laser_control_handler},
        {"/api/lasers/off", HTTP_POST, all_off_handler},
        {"/api/wifi", HTTP_POST, wifi_config_handler},
        {"/api/wifi/list", HTTP_GET, wifi_list_handler},
        {"/api/wifi/scan", HTTP_GET, wifi_scan_handler},
        {"/api/ota/upload", HTTP_POST, ota_upload_handler},
    };
    for (size_t index = 0; index < sizeof(routes) / sizeof(routes[0]); ++index) {
        error = register_handler(routes[index].uri, routes[index].method, routes[index].handler);
        if (error != ESP_OK) {
            httpd_stop(s_server);
            s_server = NULL;
            return error;
        }
    }
    laser_web_record_event("Embedded laser dashboard started");
    ESP_LOGI(TAG, "Dashboard ready on AP and STA interfaces");
    return ESP_OK;
}

esp_err_t laser_web_start(void)
{
    s_command_queue = xQueueCreate(WEB_COMMAND_QUEUE_LENGTH, sizeof(laser_test_command_t));
    s_snapshot_mutex = xSemaphoreCreateMutex();
    s_log_mutex = xSemaphoreCreateMutex();
    s_ota_mutex = xSemaphoreCreateMutex();
    if (s_command_queue == NULL || s_snapshot_mutex == NULL ||
        s_log_mutex == NULL || s_ota_mutex == NULL) {
        return ESP_ERR_NO_MEM;
    }

    esp_err_t error = initialize_nvs();
    if (error != ESP_OK) {
        return error;
    }
    laser_web_record_event("Boot complete; laser outputs default off");
    error = start_wifi();
    if (error != ESP_OK) {
        return error;
    }
    error = start_http_server();
    if (error != ESP_OK) {
        return error;
    }
    if (xTaskCreate(
            validate_running_image_task,
            "ota_valid",
            3072,
            NULL,
            5,
            NULL
        ) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}
