# Release Category Matrix - 2026-07-05

Scope: current `circuits/laser_controller.kicad_pcb`, generated JLCPCB
prototype package, and the open release blockers reported by
`circuits/check_laser_controller_release_readiness.py`.

This matrix ranks the remaining failure categories by how much money, time,
hardware, or safety margin they can consume if missed. It is not a waiver and
does not replace the individual first-article signoff files.

## Current Order Stance

The repo has a generated Gerber/BOM/POS package and the available automated
layout/package gates pass. The current board should still be treated as a
controlled first-article prototype only, not a released production design.

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
- PD/ADC readings treated as uncalibrated until the first-article calibration
  templates are filled with measured data.

## Ranked Failure Categories

| Rank | Category | Release blocker(s) | Severity | What fails if missed | Current repo evidence | Still required |
|---:|---|---|---|---|---|---|
| 1 | Native CAD/fab/assembly signoff | `KICAD_ERC_DRC_ZONE_SIGNOFF` | Critical | Wrong nets, stale schematic/PCB sync, unbuildable clearances, or assembly surprises can turn the order into scrap. | Custom netlist/PCB/parity gates pass; headless Pcbnew reports 0 unconnected pads and 0 footprint errors; 4 courtyard-only warnings are explicitly waived; JLCPCB package gate passes. | GUI ERC, update PCB from schematic, refill zones, run native PCB DRC with schematic parity, inspect ignored tests/courtyard waivers in KiCad and the JLCPCB assembly viewer. |
| 2 | 24 V input protection and buck-rail bring-up | `VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT` | Critical | Reverse polarity, hot-plug, transients, overcurrent, buck instability, or rail overshoot can destroy the board or connected supplies. | J5/J6 to U15/U16 topology is checked; buck pinout/capacitor/current math passes for the selected first-article limits; external-current-limit signoff exists. | Select production fuse/current-limit, reverse, TVS/transient, and harness limits; measure AP632 startup, ripple, load-step behavior, switch-loop temperature, and board temperature. |
| 3 | Laser current, thermal, and optical safety | `PER_DIODE_LASER_THERMAL_BUDGET` | Critical | Diodes, MOSFETs, sense resistors, or operators can be harmed by wrong duty/current, wrong rail, poor thermal margin, or uncontrolled optical output. | Selected diode MPNs/footprints/pin nets are checked; per-channel analog limits pass on the 9.3 V-class rail; bring-up template and signoff require one-channel-at-a-time operation. | Measure current, driver/sense-resistor temperature, optical output, duty cycle, firmware clamps, and shutoff behavior with the actual received diodes and optics. |
| 4 | +3V3 regulator and ESP32 RF load | `AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE` | High | The AP2112 can overheat or brown out the controller if sustained wireless load is treated as released. | Bench no-RF policy passes with continuous +3V3 current limited to 120 mA; AP2112 first-article signoff exists. | Measure +3V3 current and AP2112 package temperature; keep RF disabled, or replace/prove the regulator before sustained Wi-Fi/BLE. |
| 5 | ADC firmware and system readback | `AD7606_SYSTEM_INTERFACE` | High | The board may assemble correctly but return wrong, swapped, stale, or incorrectly scaled measurement data. | AD7606 package/pinout and interface-budget checks pass; firmware/readback validation template and signoff exist. | Implement and scope RESET/CONVST/BUSY/CS/SCLK timing, verify both DOUT lanes, confirm channel order, scaling, and known-input counts. |
| 6 | Signal-PD TIA range and calibration | `TIA_READOUT_RANGE_CALIBRATION` | High | PD channels can saturate, bury signal in noise, or report meaningless optical values under the real fixture. | D1-D4 to OPA380 to VOUT1..4 topology is checked; the 2 MOhm high-sensitivity bench range is documented; calibration template exists. | Define actual Vivonics photocurrent range, RF/VBIAS settings, shielding, dark offsets, noise floor, response slope, saturation threshold, and AD7606 calibration. |
| 7 | Monitor-PD calibration and APC/safety behavior | `MONITOR_PD_FRONTEND_RANGE_CALIBRATION` | High | Laser monitor telemetry can be wrong, saturated, absent, or trusted for a blue source that has no monitor PD. | INA4180/LM4040 monitor topology is checked; LD1-LD3 monitor-capable sources fit the local ADC-headroom guard; LD4/MPD4 spare-open behavior is documented. | Calibrate LD1-LD3 against an external optical meter, record dark/off counts, slope, saturation, setpoint, optical power, and firmware fail-shutoff behavior; keep MPD4 out of blue APC logic. |
| 8 | Quote-time procurement, substitution, and derating | `PASSIVE_PRODUCTION_AVL_AND_DERATING` | Medium | JLCPCB substitutions, stock drift, lifecycle changes, surge/current pulses, or hotter board operation can invalidate the locked design assumptions. | Current passive MPN/LCSC set is locked against the netlist; steady-state voltage/power derating checks pass; procurement template exists. | At quote time, verify every C-code, reject or explicitly review substitutions, save order evidence, and capture pulse/surge/current derating plus board-temperature measurements. |

## Practical Meaning

The broad categories are now: CAD/fab correctness, input power, laser safety,
3.3 V power, ADC firmware/readback, signal-PD calibration, monitor-PD
calibration, and procurement/derating. The first three are the highest-severity
spend risks because they can directly scrap hardware or create unsafe bring-up
conditions. The measurement-chain and procurement categories can still waste the
order, but they are more likely to be discovered during controlled first-article
bring-up if the boundaries above are followed.
