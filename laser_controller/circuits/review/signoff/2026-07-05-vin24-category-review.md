# VIN24 Input And Buck Category Review - 2026-07-05

Scope: severity-ranked category 1 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 1, critical. A wrong VIN24 assumption can damage the first article before
firmware or optical calibration can be evaluated.

## Current Result

The current layout/package state is acceptable for controlled first-article
ordering and first power under the existing bench boundary:

- J5 barrel input only.
- 24.0 V regulated supply.
- External current limit no higher than 300 mA.
- Center-positive polarity verified before every power application.
- RJ45 power injection disabled.
- No hot-plug and no reverse-polarity test.
- ESP32 RF disabled until the +3V3 rail is separately measured.

This category is not production-closed. The present schematic still routes J5
and J6 directly to `VIN_24V` and U15/U16 input pins without an onboard
fuse/PTC/eFuse, reverse-polarity element, TVS/transient suppressor, or hot-swap
stage.

## Evidence Reviewed

- `python3 circuits/check_vin24_input_protection.py --netlist circuits/review/generated/laser_controller_kicad9.net`
  passes the current J5/J6/U15/U16 bench topology.
- `python3 circuits/check_vin24_input_protection.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy bench-external-protection`
  passes the bench-only external-current-limit signoff.
- `python3 circuits/check_vin24_input_protection.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy production-protection`
  remains an expected fail because production input protection is not designed
  into this PCB.
- `python3 circuits/check_buck_input_power_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy bench-selected-max-9v3`
  passes the selected-laser max-current first-article input-current case.
- `python3 circuits/check_buck_input_power_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy hardware-clamp-9v3`
  passes the all-channel per-channel analog-limit input-current case.
- `python3 circuits/check_buck_input_power_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy datasheet-recommended-components`
  passes the local AP632 input/output capacitor guard.

## Closure State

Do not mark any `VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `first_power_limits`: measured first-power record with 24.0 V, 300 mA limit,
  polarity, RJ45 disabled, and no-hot-plug boundary.
- `buck_rail_measurement`: measured U15/U16 startup overshoot, ripple,
  load-step behavior, and hot component temperatures.
- `production_protection`: selected fuse/current-limit, reverse-polarity,
  TVS/transient, hot-plug, adapter, and RJ45 harness strategy.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is intentional first-article/prototype
scope, not a cleared production release.
