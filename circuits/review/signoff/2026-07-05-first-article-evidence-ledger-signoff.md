# First-Article Evidence Ledger Signoff

Date: 2026-07-05

Scope: Machine-checkable closure criteria for the remaining first-article and
production-release blockers.

## Result

Added `circuits/review/calibration/first_article_release_evidence.csv` and
`circuits/check_first_article_release_evidence.py`.

The ledger currently has 16 evidence rows across the seven deferred blocker
categories:

- `VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT`
- `PER_DIODE_LASER_THERMAL_BUDGET`
- `AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE`
- `AD7606_SYSTEM_INTERFACE`
- `TIA_READOUT_RANGE_CALIBRATION`
- `MONITOR_PD_FRONTEND_RANGE_CALIBRATION`
- `PASSIVE_PRODUCTION_AVL_AND_DERATING`

Every row is intentionally `OPEN`. A row may only be changed to `CLOSED` after
an evidence file exists and contains the row's required tokens. This prevents
clearing the blocker registry with prose-only signoff or incomplete bring-up
notes.

## Verification

- `python3 circuits/check_first_article_release_evidence.py`
  - returns `2`
  - reports 16 open evidence rows
- `python3 circuits/run_laser_controller_review.py`
  - reports `DEFERRED: First-article release evidence ledger`
  - keeps `JLCPCB order package status: READY`
  - keeps `First-article/production release status: BLOCKED`
