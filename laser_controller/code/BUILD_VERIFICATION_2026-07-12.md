# Laser-Controller Firmware Build Verification

**Originally verified 2026-07-12; repeated for all three profiles on
2026-07-20 and twice from the relocated bench package on 2026-07-21. This is
software/build evidence, not assembled-board evidence.**

## Outcome

- Host decoder/safety suite: **PASS** under `-Wall -Wextra -Werror -Wpedantic`
  plus AddressSanitizer and UndefinedBehaviorSanitizer.
- ESP32-S3 clean container builds: **PASS** twice consecutively for the normal,
  board-validation, and finite-pulse laser-test profiles.
- Reproducibility: bootloader, partition table, application binary, and
  application ELF were byte-identical across the two clean builds.
- Normal-profile application size: `0x2ce90` bytes (`183,952` bytes); `82%` of
  the 1 MiB app partition remains free.
- Build-log scan: no compiler `warning:`, `error:`, or dubious-ownership message.
- Component closure excludes Wi-Fi, Bluetooth, networking, OTA, and web-server
  components.

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
fault, or overcurrent. Individual wavelengths and the explicit `IR_GREEN`
target are supported. Normal and board-validation builds keep this option
disabled. The application size is `0x3c050` bytes (`245,840` bytes), leaving
`77%` of the 1 MiB app partition free. Two consecutive clean builds matched:

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

## Claim boundary

These results prove source compilation, host decoder/safety behavior, pinned
configuration, artifact generation, and byte reproducibility. They do **not**
prove GPIO electrical state, reset-window behavior, SPI phase/byte order, BUSY
timing, ADC accuracy, sustained acquisition, brownout behavior, or laser
fail-shutoff on the fabricated board. Those remain return-board evidence gates.
