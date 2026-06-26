# ESP32-S3-WROOM-1-N16R8 Part Note

Sources:
- Espressif ESP32-S3-WROOM-1/WROOM-1U datasheet:
  `https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf`
- Espressif ESP32-S3 series datasheet:
  `https://documentation.espressif.com/esp32-s3_datasheet_en.pdf`
- Local source symbol:
  `~/projects/access-controller/circuits/controller/microcontroller.kicad_sch`

Current design:
- Real `Espressif:ESP32-S3-WROOM-1` symbol block is used in `mcu.kicad_sch`;
  `check_laser_controller_netlist.py` compares it against the access-controller
  source block with only the footprint-library substitution allowed.
- `+3V3` connects only module pin 2, AP2112 output, local/bulk decoupling, EN
  pull-up, and BOOT pull-up.
- Native USB: GPIO19/pin 13 = D-, GPIO20/pin 14 = D+.
- ADC telemetry is on ADC1-capable pins: `ISENSE1..4` on GPIO4/5/6/7 and
  `MPD1..4` on GPIO2/1/8/9.
- Laser PWM outputs use GPIO16/38/13/14. GPIO38 is used for `PWM2` to keep the
  red command route off the GND reference plane while avoiding strapping pins.
- GPIO0/BOOT has a pull-up and is exposed on J2; EN has a pull-up and 100 nF
  POR capacitor.
- Bench power policy assumes native USB/UART control with Wi-Fi/BLE disabled.
  Espressif RF peak-current modes exceed the AP2112 SOT25 thermal budget from
  a 5 V source.

Layout notes:
- Keep the module antenna keepout clear on all copper layers; the PCB checker
  counts antenna-keepout intrusions and verifies the generated keepout spans the
  declared four copper layers.
- Keep 3V3 decoupling local to the module and LDO output.

Open release risks:
- AP2112 is acceptable only under the documented bench/no-RF 120 mA continuous
  +3V3 policy unless measured rail current and regulator temperature prove more
  margin.
- GUI DRC and visual RF/return-path review still required.
