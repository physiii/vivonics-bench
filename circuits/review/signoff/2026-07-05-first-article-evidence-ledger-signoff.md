# First-Article Evidence Ledger Signoff

Date: 2026-07-05; updated 2026-07-06 after JLCPCB first-article order placement

Scope: Machine-checkable closure criteria for the remaining first-article and
production-release blockers.

## Result

Added `circuits/review/calibration/first_article_release_evidence.csv` and
`circuits/check_first_article_release_evidence.py`. Updated
`circuits/check_laser_controller_release_readiness.py` so the open blocker list
is derived from this ledger, while the static blocker prose is kept as the
per-category explanation and required-action registry.

The ledger currently has 16 evidence rows across the seven deferred blocker
categories:

- `VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT`
- `PER_DIODE_LASER_THERMAL_BUDGET`
- `AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE`
- `AD7606_SYSTEM_INTERFACE`
- `TIA_READOUT_RANGE_CALIBRATION`
- `MONITOR_PD_FRONTEND_RANGE_CALIBRATION`
- `PASSIVE_PRODUCTION_AVL_AND_DERATING`

All rows were initially `OPEN`. A row may only be changed to `CLOSED` after an
evidence file exists and contains the row's required tokens. This prevents
clearing the blocker registry with prose-only signoff or incomplete bring-up
notes.

The `PASSIVE_PRODUCTION_AVL_AND_DERATING/quote_acceptance` row was closed on
2026-07-06 after order placement, with evidence in
`circuits/review/journal/2026-07-06-jlcpcb-laser-controller-order.md`. This
only closes quote/order acceptance evidence; it does not close passive
derating, board-temperature, calibration, firmware, laser-safety, or bring-up
evidence.

The release-readiness checker now verifies that the seven blocker IDs in its
registry match the blocker IDs required by the ledger. If a ledger row is
closed with valid evidence, that specific evidence item stops contributing to
the open blocker count; if all rows for a blocker are closed, the category is
removed from the reported production-release blockers.

## Verification

- `python3 circuits/check_first_article_release_evidence.py`
  - returns `2`
  - reports 15 open evidence rows after quote-acceptance closure
- `python3 circuits/run_laser_controller_review.py`
  - reports `DEFERRED: First-article release evidence ledger`
  - keeps `JLCPCB order package status: READY`
  - keeps `First-article/production release status: BLOCKED`
- `python3 circuits/check_laser_controller_release_readiness.py`
  - returns `2`
  - reports 7 open blocker categories across 16 open evidence rows
