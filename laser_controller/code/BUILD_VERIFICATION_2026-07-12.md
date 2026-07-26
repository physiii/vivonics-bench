# Laser-Controller Firmware Build Verification

**Originally verified 2026-07-12; repeated for the original three profiles on
2026-07-20 and from the relocated bench package on 2026-07-21. The dashboard
profile was built and verified on the assembled board on 2026-07-21.**

## Outcome

- Host decoder/safety suite: **PASS** under `-Wall -Wextra -Werror -Wpedantic`
  plus AddressSanitizer and UndefinedBehaviorSanitizer.
- ESP32-S3 clean container builds: **PASS** twice consecutively for the normal,
  board-validation, and finite-pulse laser-test profiles.
- Post-dashboard regression builds: **PASS** for normal, board-validation,
  laser-test, and dashboard profiles using the same pinned container.
- Reproducibility: bootloader, partition table, application binary, and
  application ELF were byte-identical across the two clean builds.
- Current application sizes: normal `0x324f0`, validation `0x32590`, laser-test
  `0x41650`, and dashboard `0xe9a40` bytes. The dashboard image leaves 54% of
  each 2 MiB OTA slot free.
- Build-log scan: no compiler `warning:`, `error:`, or dubious-ownership message.
- The dashboard profile intentionally includes Wi-Fi, NVS, HTTP server, JSON,
  and application-update components. Bluetooth remains disabled.

## Pinned toolchain

- ESP-IDF: `v5.5.4`
- Official image OCI index:
  `docker.io/espressif/idf@sha256:b9f2d6ea1c19e0c9f7959bdb74a9e3c775642f9d0f3b841937c5fa3363db892b`
- Resolved amd64 manifest:
  `sha256:116f0526dfc87e764785370e59b88822e02cf4f9e1edd953cad5ed2d02672023`
- Target/compiler: `esp32s3`, Xtensa GCC `14.2.0_20260121`

## Locked generated configuration

```text
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE="16MB"
CONFIG_FREERTOS_HZ=1000
CONFIG_LC_AD7606_SCLK_HZ=10000000
CONFIG_LC_AD7606_SAMPLE_RATE_HZ=1000
CONFIG_LC_AD7606_BUSY_TIMEOUT_US=100
CONFIG_LC_AD7606_LOG_EVERY_N=0
CONFIG_APP_PROJECT_VER="0.1.0-bringup"
CONFIG_APP_COMPILE_TIME_DATE=n
CONFIG_BOOTLOADER_COMPILE_TIME_DATE=n
```

Flash mode is DIO at 80 MHz. Offsets are bootloader `0x0`, partition table
`0x8000`, and application `0x10000`.

## Repeated-build hashes

```text
dc2676e87a93b03d1c243e6477de0d3bbec30c135eb593b4a1062bae33f54404  bootloader/bootloader.bin
7f00b6c042a89b15b0cac534f82ed988caf29278ff5700b0c511eb1b5bb7c820  partition_table/partition-table.bin
81363ea8dae923ca31142f65ae2ed65d39d3560c586702d2191c0c0149c19b64  vivonics_laser_controller.bin
3d46ea6635d126f8a5c1dd6a3394a6a82f106fb1a76d0c9c43fcd330c725df5e  vivonics_laser_controller.elf
```

Reproduce with:

```bash
laser_controller/code/run-host-tests.sh
laser_controller/code/build-container.sh
```

## Board-validation logging profile

The injection fixture uses a separate artifact with `50 sample/s`, every-sample
UART logging, and version `0.1.0-board-validation`. It retains the same safety
logic and timing-overrun latch but is not interchangeable with the default 1 kSPS
artifact. Two clean validation-profile builds also matched byte-for-byte:

```text
dc2676e87a93b03d1c243e6477de0d3bbec30c135eb593b4a1062bae33f54404  bootloader/bootloader.bin
7f00b6c042a89b15b0cac534f82ed988caf29278ff5700b0c511eb1b5bb7c820  partition_table/partition-table.bin
ed7b8f00ee94b7e4317689ccbd80f5685979d5483638329bd92bdad4d0e0ee08  vivonics_laser_controller.bin
a502d9d521a991bd4976c77bcc73dbac9ec2021a4d93dfbc768480a076a106b5  vivonics_laser_controller.elf
```

Build it with:

```bash
laser_controller/code/build-validation-container.sh
```

Attach the flashed profile, application hash, device identity, and complete boot
metadata to every calibration capture.

## Local laser-test profile

The separately selected `0.1.0-laser-test` profile preserves the AD7606 fault
gate and adds local `STATUS`, `OFF`, `ON`, and bounded `PULSE` commands for
controlled first-article measurements. A valid local USB-serial command is the
test-profile arm request; the physical `FACT` input is not required. `PULSE` is
limited to `20..900 ms`; `ON` remains active until `OFF`, reset, an ADC/telemetry
fault, or overcurrent. Every canonical combination of IR, Red, Green, and Blue
is supported, with `ALL` as an alias for all four. Normal and board-validation
builds keep this option disabled. The current application size is `0x41230`
bytes (`266,800` bytes), leaving `75%` of the 1 MiB app partition free. The
current regression artifact is:

```text
1fbe26e0370b5414e4d6da0af676d9eb87782d7636b233a46087ebb5152e303d  vivonics_laser_controller.bin
```

The earlier two-build reproducibility evidence was:

```text
dc2676e87a93b03d1c243e6477de0d3bbec30c135eb593b4a1062bae33f54404  bootloader/bootloader.bin
7f00b6c042a89b15b0cac534f82ed988caf29278ff5700b0c511eb1b5bb7c820  partition_table/partition-table.bin
6683c6cfe96b20aa03f9b381577acddb9109236f79cd71a88e9cc8875be1daa7  vivonics_laser_controller.bin
26837c0b46176d37c761d8b1bf26d496b28419fe60ee68bc9f06e12f4c5ec3d8  vivonics_laser_controller.elf
```

Build it with:

```bash
laser_controller/code/build-laser-test-container.sh
```

## Dashboard, live-device, and OTA verification

The `0.3.2-dashboard` profile is selected by
`sdkconfig.dashboard.defaults` and built with:

```bash
laser_controller/code/build-dashboard-container.sh
```

The verified application artifact deployed on 2026-07-21 is:

```text
0e0edd67d4961220d849c8dee8125f5994994548b7d4fa74d63004ccc15c7979  vivonics_laser_controller.bin
```

Assembled-board verification on ESP32-S3 `ac:27:6e:ca:0c:e4`:

- full initial flash over built-in USB-JTAG with no `FACT` hold;
- boot from `ota_0`, ADC ready, fault mask zero, outputs OFF;
- WPA2 provisioning AP `VIVONICS-LASER-CA0CE4` and station join to the bench
  LAN;
- live `50 Hz` AD7606 telemetry and responsive desktop/mobile UI with no
  browser console or layout failures;
- simultaneous IR + Green `1000` permille UI control, removal of IR while Green
  remained active, and final verified All-Off;
- independent API duties of IR `700` permille and Green `400` permille, reported
  with channel mask `5` and `sharedDuty: false`;
- IR current telemetry of `365 mV`/approximately `36.5 mA` at full command and
  `246 mV`/approximately `24.6 mA` at 70% command;
- live four-channel AD7606 readings near `0.96`, `1.10`, `1.13`, and `1.12 V`;
- raw HTTP OTA upload of the hash above to `ota_1`, reboot into
  `0.3.2-dashboard`, and final OTA state `valid` after the rollback gate;
- five outputs-off sensing-pin self-tests through
  `POST /api/diagnostics/sensing-pins`; every ISENSE1–4 and MPD1–4 ADC input
  moved repeatably from raw zero to raw `51..55` (`45..50 mV`) under its weak
  internal pull-up and returned to zero under pull-down, with fault mask zero
  and all outputs remaining off.
- live desktop/mobile browser smoke on `0.3.2-dashboard`, including the new
  Dashboard sensing-test control, eight rendered input rows, no browser errors
  or viewport overflow, final All-Off, and fault mask zero.

The live smoke exposed and then verified the fix for a request-lifetime defect
that corrupted the logged target name after a laser command. The reusable
checks are `tests/dashboard-ui-smoke.js` and
`tests/dashboard-live-smoke.js`.

Green current sense and all equipped source-monitor readings remained raw zero
during the live output samples. The API and UI now label those active paths
`no-response`, set `sensingDegraded: true`, make `/api/health` unhealthy, and
state that the values are not hidden or simulated. This is recorded as an
unresolved physical sensing-path issue rather than treated as successful
current/monitor validation. The warning is diagnostic only; it is not a
fail-shutoff latch. Consequently Green overcurrent protection cannot be
credited until the current-sense path is repaired.

### 2026-07-26 active-output watchdog follow-up

During a simultaneous IR + Green physical probe, the last sample snapshot
stopped advancing while the HTTP task remained responsive. Repeated
`POST /api/lasers/off` requests were acknowledged and queued but could not be
consumed by the stalled acquisition/control task. The board was recovered by a
same-image OTA reboot, which restored the safe-low boot state.

`0.3.3-dashboard` adds a separate priority-8 output watchdog. It reads the
published snapshot every `50 ms` and calls `esp_restart()` if any output is
active and the control sample age exceeds `500 ms`. The timeout predicate is a
host-tested pure function, including inactive, exact-boundary, expired,
backwards-clock, and invalid-threshold cases.

The verified application artifact is:

```text
bff1fcaccee2aa41d4a81704914ab84b48448b4959f6b8b487c28dbfc0eaad07  vivonics_laser_controller.bin
```

Verification passed:

- sanitizer-enabled host tests;
- pinned ESP-IDF `v5.5.4` target build, `957,440` application bytes;
- HTTP OTA to `ota_1`, rollback state `valid`, version
  `0.3.3-dashboard`, and fault mask zero;
- live sample index `2039` to `2100` in one second with outputs OFF;
- desktop/mobile live dashboard smoke, no output exercise, final sample index
  `5711`, fault mask zero, and all outputs OFF.

The assembled-board expired-watchdog branch has not been deliberately
fault-injected. The Green-driver and source-monitor analog faults remain open:
with IR and Green commanded at full duty, U7 pin 3 measured `1.2 V`, U7 pin 4
measured `0 V`, and U12 outputs on pins 1 and 8 both measured `0 V`. U13 held
the intended `5.0 V` bias difference (`9.8 V` on pin 1 and `4.8 V` on pins 2
and 3), so the shared source-monitor bias generator is operating.

## Claim boundary

These results prove source compilation, host decoder/safety behavior, pinned
configuration, artifact generation, initial USB-JTAG deployment, live web/ADC
operation, a brief IR/Green control path, and one complete OTA slot transition.
They do **not** prove absolute ADC accuracy or channel order, calibrated optical
power, Green current/monitor sensing, sustained wireless/regulator thermal
behavior, brownout behavior, or physical laser fail-shutoff. Those remain
first-article evidence gates.
