# AP2112 3V3 Regulator Category Review - 2026-07-05

Scope: severity-ranked category 3 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 3, high. A wrong +3V3 load assumption can overheat the AP2112 SOT25 LDO,
brown out the ESP32, or make first-article firmware/readout tests unreliable.

## Current Result

The current layout/package state is acceptable for controlled first-article
ordering and USB/UART bench firmware under the existing no-RF boundary:

- ESP32 Wi-Fi disabled.
- ESP32 BLE disabled.
- Continuous `+3V3` current no higher than 120 mA.
- No added external 3.3 V load on J7 without rerunning the AP2112 thermal
  budget.
- Measure AP2112 package temperature and `+3V3` rail current during first
  bring-up.

This category is not production-closed. Sustained Wi-Fi/BLE on the present
SOT25 AP2112 rail remains out of policy unless a buck regulator, larger
thermally proven regulator, lower-current duty-cycle proof, and measured board
temperature evidence are added.

## Evidence Reviewed

- `python3 circuits/check_power_thermal_budget.py --policy bench-uart-usb`
  passes the 120 mA, 85 degC, no-RF bench policy.
- `python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty`
  remains an expected fail for sustained ESP32-S3 Wi-Fi TX.
- `python3 circuits/check_power_thermal_budget.py --policy ble-tx-20dbm`
  remains an expected fail for sustained ESP32-S3 BLE TX.
- `python3 circuits/check_ap2112_first_article_signoff.py`
  passes the no-RF first-article operating signoff.
- `python3 circuits/check_layout_review_geometry.py circuits/laser_controller.kicad_pcb`
  passes the AP2112 local layout/proximity checks as part of the focused layout
  review.

## Closure State

Do not mark any `AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `no_rf_current_temp`: measured no-RF firmware state, `+3V3` rail current, and
  AP2112 package temperature during first-article operation.
- `regulator_decision`: documented decision to keep RF disabled, replace the
  rail with a buck or larger regulator, or accept a measured wireless duty
  cycle with thermal proof.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is intentional first-article/prototype
scope, not a cleared sustained-wireless or production regulator release.
