# Signal-PD TIA Range And Calibration Category Review - 2026-07-05

Scope: severity-ranked category 5 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 5, high. A wrong TIA range, ambient-light assumption, RF/VBIAS setting, or
ADC scaling assumption can make the signal-PD channels saturate or report
meaningless optical values.

## Current Result

The current layout/package state is acceptable for controlled first-article
ordering and signal-PD calibration under the existing bench boundary:

- Treat the 2 Mohm feedback trim as a high-sensitivity, low-current bench
  range.
- Start with VBIAS target 1.5 V and record actual VBIAS per channel.
- Keep SFH2201 detectors covered or optically shielded during dark-offset
  capture.
- Calibrate `VOUT1..4` one channel at a time using known electrical current
  injection or a calibrated optical input.
- Record RF/trim state, VBIAS, dark counts, slope, noise floor, saturation
  threshold, ambient condition, known input level, and AD7606 scaling.
- Treat the SFH2201 1000 lx datasheet short-circuit-current example as an
  expected saturation case at 2 Mohm feedback.

This category is not production-closed. The repo proves topology, component
identity, VBIAS bound, OPA380 output headroom, AD7606 input connectivity, and
the bright-ambient expected-fail guard; it does not prove the real Vivonics
photocurrent range, ambient shielding, noise/stability, firmware saturation
handling, or calibrated optical measurements.

## Evidence Reviewed

- `python3 circuits/check_tia_readout_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net`
  passes the SFH2201/OPA380/VOUT1..4 topology and bench-range math.
- `python3 circuits/check_tia_readout_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy sfh2201-1000lx-example`
  remains an expected fail because the 1000 lx example would require about
  152 V of TIA swing at 2 Mohm feedback.
- `python3 circuits/check_tia_first_article_signoff.py`
  passes the first-article calibration signoff.
- `python3 circuits/check_optical_calibration_template.py`
  passes the D1-D4 signal-PD and U14 `adc_readback` calibration rows.
- `python3 circuits/check_ad7606_interface_budget.py circuits/review/generated/laser_controller_kicad9.net`
  passes the AD7606 +/-5 V scaling/timing contract used by the TIA signoff.

## Closure State

Do not mark any `TIA_READOUT_RANGE_CALIBRATION` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `signal_pd_calibration`: measured D1-D4 RF, VBIAS, dark counts, slope,
  saturation, and noise floor under known input.
- `ambient_saturation_policy`: measured ambient/shielding condition plus
  firmware saturation and out-of-range behavior.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is intentional first-article/calibration
scope, not a cleared production optical measurement release.
