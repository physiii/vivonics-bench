# Vivonics Laser-Controller Bring-Up Firmware

ESP32-S3 firmware for the fabricated four-laser/four-TIA controller. The normal
and board-validation profiles are measurement-only and expose no laser command
surface. A separately built local laser-test profile supports deliberate
first-article output tests over USB serial. The dashboard profile adds the
access-controller web foundation, AP/STA Wi-Fi, real-time AD7606/current/monitor
telemetry, remote first-article controls, and rollback-protected OTA. At
application entry every profile
configures GPIO10/11/12/16 low before ADC initialization, reads all four
AD7606-4 channels through DOUTA, and latches BUSY/SPI/timing or telemetry
failures into a laser-off state. The dashboard profile reports scheduling
deadline overruns instead of latching them because Wi-Fi and HTTP execution is
nondeterministic; BUSY/SPI and telemetry-read failures still latch All-Off. The
PCB's analog command-limit pulldowns—not
application firmware—provide the safe command state while the ESP32-S3 is held
in reset or is still in ROM/bootloader execution.

## Evidence boundary

- Implemented: safe boot GPIO, AD7606 reset/conversion sequencing with a latched
  BUSY rising edge, bounded BUSY fall timeout, mode-1 one-lane SPI, 64-clock
  V1–V4 decode, signed scaling, metadata/counters, and latched safety state.
- Laser-test profile implemented: local `STATUS`, `OFF`, bounded `PULSE`, and
  latched `ON` commands; every validated combination of the four wavelengths;
  10 kHz PWM below full command and a probeable steady GPIO high at `1000`
  permille; current-sense and monitor-PD telemetry.
- Dashboard profile implemented: professional responsive UI, 50 Hz telemetry,
  discovery/health/log/network APIs, the same safety-gated output state machine,
  WPA2 provisioning AP, saved station credentials, dual 2 MiB OTA slots, output
  inhibit during OTA, and delayed image-valid marking for rollback.
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
- Dashboard/OTA observed on 2026-07-21: version `0.3.2-dashboard` running valid
  from `ota_1`, zero firmware faults, advancing 50 Hz AD7606 samples, responsive
  desktop/mobile layouts with no browser errors, simultaneous IR + Green
  control followed by verified All-Off, and unequal IR/Green duties of 70%/40%
  accepted and reported independently. IR current sense tracked the command at
  `365 mV`/approximately `36.5 mA` at 100% and `246 mV`/approximately `24.6 mA`
  at 70%. Green emitted under command but its current-sense and all equipped
  source-monitor ADC readings were `0`; those hardware sensing paths remain
  unresolved and are shown as degraded rather than hidden or simulated.
  The outputs-off `SENSETEST` subsequently produced a repeatable `45..50 mV`
  weak-pull response on all eight ESP32 sensing inputs across five runs. This
  proves the ADC inputs respond and rules out an obvious floating MCU-side path;
  the Green-current and common source-monitor faults are upstream analog issues.
- Dashboard safety follow-up observed on 2026-07-26: an acquisition/control-loop
  stall left the last active snapshot visible and prevented queued All-Off
  commands from being consumed. Version `0.3.3-dashboard` adds an independent,
  higher-priority output watchdog that reboots into safe-low GPIO state whenever
  an active snapshot is more than `500 ms` stale. The host boundary tests,
  pinned ESP-IDF build, rollback-protected OTA, advancing live samples, and
  outputs-off desktop/mobile smoke passed. The expired-watchdog reboot branch
  has not yet been deliberately fault-injected on the assembled board.
- Not yet verified: absolute ADC accuracy and channel order against known
  external inputs, calibrated optical power or source-monitor slope, board
  temperature at sustained duty, or fail-shutoff behavior under real
  reset/brownout/power faults.
- Not implemented: production laser authorization/control, dual-DOUT acquisition
  in the main sampler, authenticated LAN control, signed OTA images, or
  production security provisioning.

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

The artifacts are written under `build-laser-test/`. The profile accepts
`STATUS`, `OFF`, `SENSETEST`, `ON <target> <duty_permille>`, and
`PULSE <target> <duty_permille> <duration_ms>`. A target is any canonical
underscore-separated combination in IR, RED, GREEN, BLUE order, or `ALL`;
examples are `IR_GREEN`, `RED_BLUE`, and `IR_RED_GREEN_BLUE`. `ON` keeps the
selected channels active until `OFF`, reset, overcurrent, or an ADC/telemetry
fault. `PULSE` applies them for `20..900 ms`. Both accept `1..1000` permille
only when the AD7606 is ready and no fault is latched. A valid command received
on native USB-Serial/JTAG is the test-profile arm request; the `FACT` button is
not required. This profile is for controlled first-article work; it is not a
production authorization or control interface.
At `1000` permille the selected command pin is driven as a steady 3.3 V GPIO
level so it can be checked with a DC probe. Settings below `1000` use the
10 kHz LEDC PWM path and appear as a waveform at the corresponding duty cycle.
Each sample log includes calibrated `I`/`M` millivolts and the corresponding
uncalibrated `IRAW`/`MRAW` ADC counts so a zero-millivolt observation can be
distinguished from a disconnected input or a calibration-floor effect.

`SENSETEST` is accepted only while every output is off and the controller is
fault-free. It sequentially samples ISENSE1–4 and MPD1–4 while each ESP32 input
is floating, weakly pulled up, and weakly pulled down, then restores the input
to floating. A floating board path follows both weak pulls; a connected,
low-impedance zero-volt source remains near zero. The command never enables a
laser and logs `SENSE_PIN` records over native USB-Serial/JTAG for first-article
fault isolation.

## Laser dashboard and OTA profile

Build the web-enabled first-article image with the pinned ESP-IDF container:

```bash
laser_controller/code/build-dashboard-container.sh
```

The profile is versioned independently and writes artifacts under
`build-dashboard/`. Its custom 16 MiB layout contains `ota_0` and `ota_1`, each
2 MiB, plus NVS, PHY, and OTA-selection data. A full initial flash needs the
bootloader at `0x0`, partition table at `0x8000`, initial OTA data at `0xe000`,
and application at `0x10000`. The fabricated board can be programmed without
holding `FACT`: use the CP2102N auto-reset USB connector when available, or the
ESP32-S3 built-in USB-JTAG interface. Subsequent releases upload only
`vivonics_laser_controller.bin` through the System tab or
`POST /api/ota/upload`.

On every boot the controller advertises `VIVONICS-LASER-<MAC>` with WPA2 key
`vivonics` at `http://192.168.4.1/`. Use the Network tab to save the bench Wi-Fi
credentials; the AP remains available while the station interface connects.
The assigned station address appears in the Network/System views and
`GET /api/state`. Credentials are stored in NVS and are not embedded in the
firmware image.

The main HTTP surface is:

- `GET /api/health`, `/api/state`, `/api/telemetry`, `/api/discovery`, and
  `/api/logs`
- `POST /api/lasers` and `/api/lasers/off`
- `POST /api/diagnostics/sensing-pins` while fault-free and All-Off; results
  appear as `SENSE_PIN` entries in `GET /api/logs`. The Dashboard's driver
  telemetry card runs this electrical-only test and renders all eight raw
  floating/pull-up/pull-down results without energizing a laser.
- `GET /api/wifi/list` and `/api/wifi/scan`; `POST /api/wifi`
- `POST /api/ota/upload` with a raw ESP-IDF application binary

Run the deterministic local UI test with `tests/dashboard-ui-smoke.js`. Run the
live-device test with `tests/dashboard-live-smoke.js <base-url>`; add
`--exercise-multi` only at a controlled optical bench. The multi-output test
uses the UI to add IR and Green concurrently, removes IR without disturbing
Green, and then forces All-Off. Every live test checks desktop/mobile rendering
and fails on browser console errors, missing telemetry, faults, or viewport
overflow.

`POST /api/lasers` remains compatible with a shared-duty command such as
`{"target":"IR_GREEN","dutyPermille":1000}`. Independent per-source duty uses
`{"channels":[{"target":"IR","dutyPermille":700},{"target":"GREEN","dutyPermille":400}]}`.
The state and telemetry responses return the active channel mask and the duty
assigned to each channel.

## Safety behavior and sensing limits

Firmware-enforced output inhibition includes safe-low boot GPIOs, a valid ADC
startup sample, fault-free arm/run transitions, input validation, PWM register
or GPIO-pad readback, AD7606 BUSY/SPI checks, telemetry-ADC read checks, and
per-channel hard current ceilings. The dashboard profile also runs an
independent output watchdog: while any channel is active, a control snapshot
older than `500 ms` forces a software reboot so boot-safe GPIO initialization
removes the output even if the acquisition task can no longer consume its
command queue. The current-sense ceilings are IR `450 mV`
(approximately `45 mA`), Red `300 mV` (`30 mA`), Green `850 mV` (`85 mA`), and
Blue `1150 mV` (`115 mA`). Exceeding one forces all channels off and latches a
reset-required fault. OTA start also commands All-Off.

An active channel with zero current-sense or equipped source-monitor response
sets `sensingDegraded`, makes `/api/health` unhealthy, and produces an explicit
dashboard warning. It does **not** currently latch a shutdown fault. Therefore
the Green overcurrent gate cannot be credited while its current-sense path is
reading zero, and the source monitors cannot be credited while their paths are
reading zero. There is no physical door/key/E-stop interlock and no network
command-heartbeat timeout in this bench profile.

This is a first-article operator surface, not a production safety controller.
LAN requests are currently unauthenticated, OTA images are not signed, and the
documented AP2112 no-RF thermal acceptance does not cover sustained Wi-Fi.
Measure +3V3 current and U11 temperature under the dashboard workload or change
the regulator before treating continuous wireless operation as released.
