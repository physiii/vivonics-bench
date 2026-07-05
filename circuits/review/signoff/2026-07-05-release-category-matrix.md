# Release Category Matrix - 2026-07-05

Scope: current `circuits/laser_controller.kicad_pcb`, generated JLCPCB
prototype package, and the open release blockers reported by
`circuits/check_laser_controller_release_readiness.py`.

This matrix ranks the remaining first-article and production-release failure
categories by how much money, time, hardware, or safety margin they can consume
if missed. It is not a waiver and does not replace the individual first-article
signoff files.

## Current Order Stance

The repo has a generated Gerber/BOM/POS package and the available automated
layout/package gates pass. `circuits/run_laser_controller_review.py` now reports
`JLCPCB order package status: READY` and `First-article/production release
status: BLOCKED`. The current board should still be treated as a controlled
first-article prototype only, not a released production design.

Minimum first-article boundaries:

- JLCPCB top-side SMT assembly only.
- J5 barrel input only for first power, 24.0 V, center-positive.
- External current limit no higher than 300 mA.
- RJ45 power injection disabled.
- No hot-plug or reverse-polarity testing.
- ESP32 Wi-Fi/BLE disabled until the +3V3 rail is measured or changed.
- Lasers enabled one channel at a time with wavelength-rated safety controls,
  minimum firmware command, external optical-power measurement, and temperature
  measurement.
- PD/ADC readings treated as uncalibrated until measured data is recorded in
  first-article evidence files.

## Closed Order Gate

Native CAD/fab/assembly package evidence is no longer a remaining release
blocker in `check_laser_controller_release_readiness.py`.

- JLCPCB package gate: PASS.
- Schematic/PCB parity: PASS.
- KiCad 9 ERC: PASS.
- KiCad 9 physical DRC report: PASS.
- KiCad 9 DRC with schematic parity: PASS.
- Headless Pcbnew DRC report: 0 unconnected pads and 0 footprint errors.
- Four native courtyard warnings remain, all courtyard-only and explicitly
  waived by `circuits/review/assembly_clearance_waivers.json`.

## Ranked Failure Categories

| Rank | Category | Release blocker(s) | Severity | What fails if missed | Current repo evidence | Still required |
|---:|---|---|---|---|---|---|
| 1 | 24 V input protection and buck-rail bring-up | `VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT` | Critical | Reverse polarity, hot-plug, transients, overcurrent, buck instability, or rail overshoot can destroy the board or connected supplies. | J5/J6 to U15/U16 topology is checked; buck pinout/capacitor/current math passes for the selected first-article limits; external-current-limit signoff exists. | Select production fuse/current-limit, reverse, TVS/transient, and harness limits; measure AP632 startup, ripple, load-step behavior, switch-loop temperature, and board temperature. |
| 2 | Laser current, thermal, and optical safety | `PER_DIODE_LASER_THERMAL_BUDGET` | Critical | Diodes, MOSFETs, sense resistors, or operators can be harmed by wrong duty/current, wrong rail, poor thermal margin, or uncontrolled optical output. | Selected diode MPNs/footprints/pin nets are checked; per-channel analog limits pass on the 9.3 V-class rail; bring-up template and signoff require one-channel-at-a-time operation. | Measure current, driver/sense-resistor temperature, optical output, duty cycle, firmware clamps, and shutoff behavior with the actual received diodes and optics. |
| 3 | +3V3 regulator and ESP32 RF load | `AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE` | High | The AP2112 can overheat or brown out the controller if sustained wireless load is treated as released. | Bench no-RF policy passes with continuous +3V3 current limited to 120 mA; AP2112 first-article signoff exists. | Measure +3V3 current and AP2112 package temperature; keep RF disabled, or replace/prove the regulator before sustained Wi-Fi/BLE. |
| 4 | ADC firmware and system readback | `AD7606_SYSTEM_INTERFACE` | High | The board may assemble correctly but return wrong, swapped, stale, or incorrectly scaled measurement data. | AD7606 package/pinout and interface-budget checks pass; firmware/readback validation template and signoff exist. | Implement and scope RESET/CONVST/BUSY/CS/SCLK timing, verify both DOUT lanes, confirm channel order, scaling, and known-input counts. |
| 5 | Signal-PD TIA range and calibration | `TIA_READOUT_RANGE_CALIBRATION` | High | PD channels can saturate, bury signal in noise, or report meaningless optical values under the real fixture. | D1-D4 to OPA380 to VOUT1..4 topology is checked; the 2 MOhm high-sensitivity bench range is documented; calibration template exists. | Define actual Vivonics photocurrent range, RF/VBIAS settings, shielding, dark offsets, noise floor, response slope, saturation threshold, and AD7606 calibration. |
| 6 | Monitor-PD calibration and APC/safety behavior | `MONITOR_PD_FRONTEND_RANGE_CALIBRATION` | High | Laser monitor telemetry can be wrong, saturated, absent, or trusted for a blue source that has no monitor PD. | INA4180/LM4040 monitor topology is checked; LD1-LD3 monitor-capable sources fit the local ADC-headroom guard; LD4/MPD4 spare-open behavior is documented. | Calibrate LD1-LD3 against an external optical meter, record dark/off counts, slope, saturation, setpoint, optical power, and firmware fail-shutoff behavior; keep MPD4 out of blue APC logic. |
| 7 | Quote-time procurement, substitution, and derating | `PASSIVE_PRODUCTION_AVL_AND_DERATING` | Medium | JLCPCB substitutions, stock drift, lifecycle changes, surge/current pulses, or hotter board operation can invalidate the locked design assumptions. | Current passive MPN/LCSC set is locked against the netlist; steady-state voltage/power derating checks pass; procurement template exists. | At quote time, verify every C-code, reject or explicitly review substitutions, save order evidence, and capture pulse/surge/current derating plus board-temperature measurements. |

## Closure Sequence

| Step | Close | Evidence file or action |
|---:|---|---|
| 1 | Quote-time procurement rows before spending order money. | Fill the JLCPCB quote, placement, passive AVL, substitution review, and order archive rows in `circuits/review/calibration/quote_time_procurement_release_template.csv`; save order number, quote timestamp, accepted substitutions, and commit hash. |
| 2 | Controlled first power without lasers. | Fill J5/VIN24, U15, D5/D6, U16, and U11 rows in `circuits/review/calibration/first_article_power_bringup_template.csv`; keep external current limit active and RF disabled. |
| 3 | AD7606 digital interface before trusting ADC values. | Fill `circuits/review/calibration/first_article_firmware_validation_template.csv`; record scope captures or firmware logs for timing, both DOUT lanes, range/scaling metadata, channel order, and known-input counts. |
| 4 | Signal-PD/TIA calibration. | Fill D1-D4 `signal_pd` rows and U14 V1-V4 `adc_readback` rows in `circuits/review/calibration/first_article_optical_calibration_template.csv`; record RF, VBIAS, dark counts, known input, noise, slope, and saturation. |
| 5 | One laser channel at a time. | Fill LD1-LD4 rows in `circuits/review/calibration/first_article_laser_bringup_template.csv`; record received-can pinout, command, measured current, optical power, driver/sense temperature, and shutoff behavior. |
| 6 | Monitor-PD calibration and safety behavior. | Fill LD1-LD4 `monitor_pd` rows in `circuits/review/calibration/first_article_optical_calibration_template.csv`; LD4 must remain spare/open with no blue APC telemetry. |
| 7 | Production release decision. | Add measured board-temperature, pulse/surge/current derating, production VIN24 protection, and any approved substitutions; then update `check_laser_controller_release_readiness.py` only for blockers that have actual evidence. |

## Practical Meaning

The broad remaining categories are now: input power, laser safety, 3.3 V power,
ADC firmware/readback, signal-PD calibration, monitor-PD calibration, and
procurement/derating. The first two are the highest-severity spend risks because
they can directly scrap hardware or create unsafe bring-up conditions. The
measurement-chain and procurement categories can still waste the order, but they
are more likely to be discovered during controlled first-article bring-up if the
boundaries above are followed.
