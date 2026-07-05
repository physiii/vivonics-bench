# Monitor-PD APC And Calibration Category Review - 2026-07-05

Scope: severity-ranked category 6 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 6, high. A wrong monitor-PD pinout, ADC range, blue-channel assumption, or
APC firmware behavior can make source telemetry misleading or unsafe.

## Current Result

The current layout/package state is acceptable for controlled first-article
ordering and monitor-PD calibration under the existing bench boundary:

- `LD1` D7805I, `LD2` D6505I, and `LD3` PLT5 520EB_P are the only selected
  monitor-capable sources.
- `LD4` PLT5 450GB has no monitor photodiode, so `MPD_RAW4` / `MPD4` is
  spare/open and must not be used as blue-source optical telemetry.
- The 240R sense resistor and INA4180A1 gain-20 scale fit the selected
  monitor-current typical and high-end cases inside the local ADC-headroom
  guard.
- Calibrate one source at a time at minimum firmware duty cycle and minimum
  command before increasing setpoint.
- Keep the analog current loop and firmware current clamps as the hard safety
  limit; MPD telemetry must not raise current above the per-channel clamps.
- Record dark/off counts, response slope, saturation threshold, firmware
  setpoint, external optical-power reading, and fail-shutoff behavior for each
  monitor-capable source.

This category is not production-closed. The repo proves topology, component
identity, current PCB pad-net mapping, LD4 no-connect handling, and first-order
ADC headroom; it does not prove optical calibration, APC behavior, firmware
fail-shutoff behavior, physical diode orientation, ambient coupling, or source
substitution safety.

## Evidence Reviewed

- `python3 circuits/check_laser_monitor_pd_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy selected-monitor-typ-9v3`
  passes the selected-laser typical monitor-current case.
- `python3 circuits/check_laser_monitor_pd_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy selected-monitor-worst-9v3`
  passes the selected-laser high-end monitor-current case.
- `python3 circuits/check_monitor_pd_package_pcb.py --netlist circuits/review/generated/laser_controller_kicad9.net --board circuits/laser_controller.kicad_pcb`
  passes the INA4180/LM4040 package, schematic pinout, current PCB pad-net
  mapping, sense/filter parts, and LD4 case no-connect guard.
- `python3 circuits/check_monitor_pd_first_article_signoff.py`
  passes the first-article calibration and APC-safety signoff.
- `python3 circuits/check_optical_calibration_template.py`
  passes the LD1-LD4 monitor-PD calibration rows.

## Closure State

Do not mark any `MONITOR_PD_FRONTEND_RANGE_CALIBRATION` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `monitor_pd_calibration`: measured LD1-LD3 dark/off counts, response slope,
  saturation threshold, firmware setpoint, external optical-power reading, and
  fail-shutoff behavior.
- `mpd4_blue_spare_open`: measured or firmware-reviewed evidence that MPD4 is
  treated as spare/open and ignored for blue APC/normalization/safety decisions.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is intentional first-article/calibration
scope, not a cleared production APC or optical-safety release.
