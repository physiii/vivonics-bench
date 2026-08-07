# Laser-controller bring-up and green-channel hold

**Last updated:** 2026-07-30  
**Board:** assembled ESP32-S3 laser controller `ac:27:6e:ca:0c:e4`  
**Firmware:** `0.3.4-dashboard`, running from `ota_0`  
**Green disposition:** **HOLD — do not use for an experiment or safety claim**

This note is the bench-side electrical bring-up record. Optical geometry,
printed-mask tolerances, and diffraction metrics are owned by
`vivonics/docs/program/PROOF_BENCH_GRATING_RUNBOOK_2026-07-29.md`.

## Immediate safety state

The controller and dashboard finish every check with all commanded duties at
zero. That is not yet a validated physical green shutoff: a green spot remains
visible in the live camera when the green command, controller state, and all
reported duties are zero.

- Keep the beam enclosed and terminated.
- Do not use apparent brightness as a power measurement.
- Do not run Green at full command until the feedback divider, current loop,
  and optical off state pass the checks below.
- Perform unpowered continuity/resistance checks before powered node probing.
- Use wavelength-appropriate eyewear and the lowest useful command for powered
  checks.

## Green control chain

```text
ESP32 GPIO12, 10 kHz PWM
  -> R30 10 kOhm
  -> CMD_FILTER / U7 pin 3 (+)
       |-> R31 3 kOhm to GND
       `-> C24 1 uF to GND
  -> U7 TLV9001 pin 1
  -> R27 1 kOhm
  -> Q3 AO3400A gate
  -> Q3 source / FB / top of R28 10 Ohm
  -> U7 pin 4 (-)
  -> R29 1 kOhm
  -> ISENSE3 telemetry
```

The command divider predicts `0.7615 V` at full PWM and approximately
`76.2 mA` through the `10 Ohm` sense resistor. Its small-signal time constant is
`(R30 || R31) * C24 = 2.31 ms`, or about `69 Hz`. The 10 kHz PWM is therefore
filtered, but this is an electrical current loop, not an optical automatic
power-control loop. The source monitor is telemetry only in the present
firmware.

## Confirmed errors, likely risks, and open assumptions

### Confirmed errors

1. The previous firmware forced all outputs off and re-armed on every nonzero
   slider update. That discharged the command filter and caused visible update
   flicker. Firmware `0.3.4-dashboard` updates an already-latched output in
   place.
2. The previous `/bench` slider effect could omit an all-off request when the
   last armed channel reached zero, or lose the last update while a prior
   request was loading. The live dashboard now serializes and coalesces
   commands; a positive slider value auto-arms that channel and zero disarms it
   and sends the zero setpoint.
3. The assembled Green channel emits visible light at commanded off.
4. Green current-sense and equipped source-monitor telemetry remain exactly
   `0 mV` during visible Green emission. The existing build record also reports
   U7 pin 3 at `1.2 V`, U7 pin 4 at `0 V`, and U12 monitor outputs at `0 V`
   during a full-command IR+Green probe. Green overcurrent protection and
   optical monitoring therefore cannot be credited.

### Likely risks

- An open or misassembled feedback path between Q3 source/R28 and U7 pin 4 can
  leave U7 operating open-loop. Input offset can then drive or chatter Q3 even
  when the nominal command is zero.
- If U7 and FB are low at off but Green still emits, Q3 may be shorted/leaking
  or the laser cathode may have an unintended return path.
- The previously measured `1.2 V` at U7 pin 3 is above the `0.7615 V` predicted
  by the captured `R30=10 kOhm`, `R31=3 kOhm` divider. Installed values, node
  identity, and meter reference must be checked before any high command.
- The board has no independent digital hard-disable element in series with the
  laser supply or gate path. Software-low alone cannot guarantee physical off
  if the analog loop fails.

### Open assumptions

- The visible spot in the declared off screenshot is direct Green LD emission,
  not fluorescence or a second green source. Confirm by disconnecting Green LD
  power with all commands off.
- R28 is installed as `10 Ohm`, R30 as `10 kOhm`, and R31 as `3 kOhm`.
- The camera exposure/white-balance path was stable enough for relative
  frame-to-frame comparisons. It is not calibrated optical-power evidence.

## 2026-07-30 live evidence

| Check | Result | Disposition |
| --- | --- | --- |
| Firmware host suite | sanitizer-enabled suite passed | Pass |
| ESP-IDF target build | pinned ESP-IDF `v5.5.4`; 957,264-byte image | Pass |
| OTA identity | `0.3.4-dashboard`, SHA-256 `0a16303696063fccba7ebe3f36d10b4ded08fd04415cfe8b4d19aeabab6f1f7a` | Pass |
| Boot safe state | `faultMask=0`, ready-lasers-off, duties `[0,0,0,0]` | Logical pass only |
| Slider semantics | Green `0 -> 1` auto-armed; `1 -> 0` disarmed and sent all-off | Pass |
| UI-to-controller confirmation | low-on about `452 ms`; off about `295 ms` | Pass against provisional `500 ms` gate |
| Live update continuity | 56 active telemetry samples across 16 increasing commands; 0 inactive samples inside the active interval | Pass |
| Fine-control range exercised | UI `1..16` mapped monotonically to `4..63 permille` | Pass for command path |
| Settled camera stability | prior 40-frame blocks at direct duties `1,2,4,8,16 permille` had green-mean CV `0.25–0.58%` | Relative pass only |
| Controller faults during sweep | fault mask remained `0` | Pass |
| Green current sense while active | `0 mV` for every active sample | **Fail** |
| Green source monitor while active | `0 mV` for every active sample | **Fail** |
| Physical off | visible green spot remains after confirmed all-off | **Fail** |

The UI remains an 8-bit `0..255` experiment interface. Its smallest nonzero
step maps to about `4 permille` (`0.4%`) at the controller. The controller
protocol itself supports integer `1..1000 permille` (`0.1%`) commands. Do not
interpret either resolution as achieved optical-power resolution until the
analog loop and monitor path are repaired.

## Green probe sequence

Record the meter model, range, ground point, board supply, command, and every
measured value. Do not increase the command if any preceding condition fails.

| Step | State | Probe | Expected result | Interpretation if it fails |
| --- | --- | --- | --- | --- |
| 1 | Power removed | R28 end-to-end | `10 Ohm` within component tolerance | Wrong/open sense resistor |
| 2 | Power removed | Q3 source/R28 top to U7 pin 4 | continuity, near `0 Ohm` trace resistance | Open FB interconnect or solder joint |
| 3 | Power removed | R30 and R31 | `10 kOhm` and `3 kOhm` within tolerance | Wrong population explains command scaling |
| 4 | Commanded off | GPIO12 to GND | logic low, target `<0.2 V` | MCU/output mux is not actually low |
| 5 | Commanded off | U7 pin 3 / CMD_FILTER | target `<5 mV` after settling | Divider/filter leakage or wrong PWM polarity |
| 6 | Commanded off | U7 pin 4 / FB and R28 top | target `<5 mV` | Unintended current or broken reference |
| 7 | Commanded off | U7 pin 1, then Q3 gate | low enough to cut Q3 off; record actual value | U7 rails high/open-loop if FB is open |
| 8 | UI Green level `4` only | U7 pin 3 | about `12.2 mV` (`16 permille`) | Command divider or installed values differ |
| 9 | Same low command | U7 pin 4 / R28 top | tracks pin 3; about `12.2 mV` | Current loop is not closed |
| 10 | Same low command | inferred R28 current | about `1.22 mA` from `V/R` | Do not trust telemetry until it agrees |

Decision tree:

- U7 pin 3 low at off, U7 pin 4 low, but U7 output/gate high: repair or replace
  U7 and verify FB continuity.
- Gate low at off but Green remains visible: isolate Q3 and the LD return path;
  check Q3 for drain-source leakage/short.
- The spot disappears when Green LD supply is physically disconnected:
  confirms direct Green emission and rejects camera-only explanations.
- Do not proceed to optical stability testing until current sense is nonzero
  and proportional at a bounded low command, source monitor responds, and off
  is below the measurement floor.

## Acceptance metrics after repair

These are initial engineering gates, not production specifications.

| Metric | Initial acceptance |
| --- | --- |
| Physical off leakage | below calibrated power-meter detection and below camera dark background plus `5 sigma` |
| Command continuity | no zero/off telemetry sample between adjacent nonzero updates |
| UI command confirmation | `<=500 ms` from slider input to confirmed telemetry |
| Minimum command | controller `1 permille` produces a repeatable response or is explicitly declared below the usable floor |
| Low-level monotonicity | each declared level exceeds the prior level by `>=3 sigma` over repeated captures |
| Short-term source-normalized power | CV `<=1%` in each settled 10 s block |
| Ten-minute drift | `<=1%` after declared warm-up |
| Frame-scale flicker | source-normalized frame CV `<=1%`, peak-to-peak `<=3%`, no unexplained spectral line |
| Current-loop agreement | R28 meter current and calibrated ISENSE3 agree within `+/-5%` initially |
| Source-monitor repeatability | CV `<=1%` at a fixed command; nonzero response above `5 sigma` noise |
| Power-versus-command fit | monotonic usable region with residuals `<=2%` of full scale after calibration |

A calibrated optical power meter and a working source-monitor path are required
to call optical power “rock solid.” The current camera result only shows that
settled image intensity was stable over short blocks.

## Required board revision for fail-safe off

After repairing the first article, add an independent hardware enable in a
future revision: a load switch, laser-rail switch, or gate clamp controlled by
a separate fail-safe signal and default-off pulldown. The safety path must be
able to force zero optical output even if U7 rails or the current-feedback trace
opens. Verify it with a deliberately opened feedback loop and with MCU reset.

