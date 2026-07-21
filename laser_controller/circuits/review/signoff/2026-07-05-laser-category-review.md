# Laser Current Thermal And Safety Category Review - 2026-07-05

Scope: severity-ranked category 2 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 2, critical. Wrong laser current, rail headroom, diode orientation, duty
cycle, or optical safety practice can damage LD1-LD4 or create unsafe emitted
optical power during first article.

## Current Result

The current layout/package state is acceptable for controlled first-article
ordering and one-channel-at-a-time laser bring-up under the existing bench
boundary:

- Verify `LASER_V+` as a 9.3 V-class rail before enabling any channel.
- Inspect each received laser can against the signed MPN/footprint pin table
  before soldering.
- Use wavelength-rated eyewear and an enclosed beam stop.
- Bring up exactly one channel at a time from minimum firmware duty and command.
- Keep firmware clamps at or below the per-channel analog command limits:
  IR 38.0 mA, red 23.0 mA, green 76.2 mA, and blue 105.5 mA.
- Measure current, optical output, driver/sense-resistor temperature, and
  shutoff behavior for every channel.

This category is not production-closed. The current repo proves the electrical
current-limit assumptions and footprint/pad-net mapping; it does not prove
received-can orientation, optical output, duty-cycle thermal behavior, loop
transients, firmware clamp behavior, or operator laser safety.

## Evidence Reviewed

- `python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-9v3`
  passes the selected LD1-LD4 typical-current 9.3 V rail case.
- `python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3`
  passes the selected LD1-LD4 datasheet max-current 9.3 V rail case.
- `python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3`
  passes the per-channel analog command-limit tolerance corner.
- `python3 circuits/check_laser_driver_control_loop.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy hardware-clamp-gate-margin`
  passes the TLV9001/AO3400A gate-drive margin check.
- `python3 circuits/check_laser_diode_footprints.py --netlist circuits/review/generated/laser_controller_kicad9.net --board circuits/laser_controller.kicad_pcb`
  passes the selected direct TO-can schematic-to-PCB pin mapping.
- `python3 circuits/check_laser_bringup_template.py`
  passes the LD1-LD4 measurement-template guard.
- `python3 circuits/check_laser_first_article_signoff.py`
  passes the one-channel-at-a-time bring-up signoff.

## Closure State

Do not mark any `PER_DIODE_LASER_THERMAL_BUDGET` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `laser_bringup`: measured LD1-LD4 current, external optical power,
  driver/sense-resistor temperature, duty cycle, and firmware shutoff behavior.
- `laser_safety_fixture`: wavelength-rated eyewear, enclosed beam stop,
  one-channel-at-a-time procedure, and received-can pinout/orientation
  inspection for the actual delivered diodes.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is intentional first-article/prototype
scope, not a cleared production laser release.
