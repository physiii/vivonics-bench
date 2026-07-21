set(laser_controller_sources
    "ad7606_decode.c"
    "laser_safety.c"
    "laser_test_protocol.c"
    "main.c"
)

set(laser_controller_embedded_files "")
set(laser_controller_requires
    esp_app_format
    esp_common
    esp_driver_gpio
    esp_adc
    esp_driver_ledc
    esp_driver_spi
    esp_driver_uart
    esp_driver_usb_serial_jtag
    app_update
    esp_event
    esp_http_server
    esp_netif
    esp_partition
    esp_rom
    esp_system
    esp_timer
    esp_wifi
    freertos
    heap
    json
    log
    nvs_flash
)
if(CONFIG_LC_ENABLE_WEB_DASHBOARD)
    list(APPEND laser_controller_sources "laser_web.c")
    list(APPEND laser_controller_embedded_files
        "public/index.html"
        "public/script.js"
        "public/style.css"
        "public/favicon.svg"
    )
endif()

idf_component_register(
    SRCS ${laser_controller_sources}
    INCLUDE_DIRS "."
    EMBED_FILES ${laser_controller_embedded_files}
    REQUIRES ${laser_controller_requires}
)
