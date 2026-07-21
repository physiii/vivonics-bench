# Vivonics Laser-Controller Bring-Up Firmware

ESP32-S3 firmware for the fabricated four-laser/four-TIA controller. The normal
and board-validation profiles are measurement-only and expose no laser command
surface. A separately built local laser-test profile supports deliberate
first-article output tests over USB serial. At application entry every profile
configures GPIO10/11/12/16 low before ADC initialization, reads all four
AD7606-4 channels through DOUTA, and latches BUSY/SPI/timing or telemetry
failures into a laser-off state. The PCB's analog command-limit pulldowns—not
application firmware—provide the safe command state while the ESP32-S3 is held
in reset or is still in ROM/bootloader execution.

## Evidence boundary

- Implemented: safe boot GPIO, AD7606 reset/conversion sequencing with a latched
  BUSY rising edge, bounded BUSY fall timeout, mode-1 one-lane SPI, 64-clock
  V1–V4 decode, signed scaling, metadata/counters, and latched safety state.
- Laser-test profile implemented: local `STATUS`, `OFF`, bounded `PULSE`, and
  latched `ON` commands; individual wavelengths or the explicit `IR_GREEN`
  target; 10 kHz PWM below full command and a probeable steady GPIO high at
  `1000` permille; current-sense and monitor-PD telemetry.
- Host verified: decoder boundary vectors, 100,000 deterministic round trips,
  safety transitions, and every defined fault latch.
- Target-build verified: the complete ESP32-S3 flash set was built twice from
  clean state and matched byte-for-byte. See
  [`BUILD_VERIFICATION_2026-07-12.md`](BUILD_VERIFICATION_2026-07-12.md).
- First-article observed: 5.2 V/3.3 V power and AD7606 reference rails, repeatable
  CONVST/BUSY activity, active DOUTA/DOUTB in the isolated diagnostic, 239
  consecutive four-channel board-validation samples without a firmware fault,
  and initial IR/green emission/current telemetry under the laser-test profile.
  See the parent repo's
  [first-article record](https://github.com/physiii/vivonics/blob/main/bench-output/laser-controller-first-article-2026-07-20.json).
- Not yet verified: absolute ADC accuracy and channel order against known
  external inputs, calibrated optical power or source-monitor slope, board
  temperature at sustained duty, or fail-shutoff behavior under real
  reset/brownout/power faults.
- Not implemented: production laser authorization/control, dual-DOUT acquisition
  in the main sampler, networking, OTA, or production security provisioning.

The board-level acceptance procedure remains in the parent repo's
[`ESP32_AD7606_FIRMWARE_BRINGUP_2026-07-12.md`](https://github.com/physiii/vivonics/blob/main/docs/program/ESP32_AD7606_FIRMWARE_BRINGUP_2026-07-12.md).

## Host tests

```bash
laser_controller/code/run-host-tests.sh
```

## Reproducible ESP-IDF build

The build uses Espressif's official ESP-IDF `v5.5.4` multi-architecture image,
pinned by OCI index digest. Both application and bootloader compile dates are
disabled so clean builds are byte-reproducible.

```bash
laser_controller/code/build-container.sh
```

Expected flash artifacts are written under `laser_controller/code/build/`.
Do not flash or connect lasers until the incoming-inspection and current-limited
power-up procedure in the master report is complete.

## Board-validation logging profile

The default build disables sample logging so synchronous UART output cannot hide
a missed 1 ms deadline. The injection fixture instead uses a separate 50 sample/s
profile that logs every sample and retains the same timing-fault latch:

```bash
laser_controller/code/build-validation-container.sh
```

Its artifacts and independent `sdkconfig.validation` are written under
`build-validation/`. Record that binary's hash with every calibration log; do
not substitute it for the byte-reproducible default artifact documented above.

## Local laser-output test profile

The normal and board-validation profiles keep all laser outputs inhibited. A
separate first-article profile adds a local UART test surface for staged optical
bring-up:

```bash
laser_controller/code/build-laser-test-container.sh
```

The artifacts are written under `build-laser-test/`. The profile accepts `STATUS`, `OFF`,
`ON <IR|RED|GREEN|BLUE|IR_GREEN> <duty_permille>`, and
`PULSE <IR|RED|GREEN|BLUE|IR_GREEN> <duty_permille> <duration_ms>`. `ON` keeps
the selected target active until `OFF`, reset, overcurrent, or an ADC/telemetry
fault; `IR_GREEN` explicitly enables those two channels together. `PULSE`
applies the selected target for `20..900 ms`. Both accept `1..1000` permille
only when the AD7606 is ready and no fault is latched. A valid command received
on native USB-Serial/JTAG is the test-profile arm request; the `FACT` button is
not required. Except for the explicit IR-plus-green bring-up target, this
profile is for controlled first-article work; it is not a production
authorization or control interface.
At `1000` permille the selected command pin is driven as a steady 3.3 V GPIO
level so it can be checked with a DC probe. Settings below `1000` use the
10 kHz LEDC PWM path and appear as a waveform at the corresponding duty cycle.
Each sample log includes calibrated `I`/`M` millivolts and the corresponding
uncalibrated `IRAW`/`MRAW` ADC counts so a zero-millivolt observation can be
distinguished from a disconnected input or a calibration-floor effect.
