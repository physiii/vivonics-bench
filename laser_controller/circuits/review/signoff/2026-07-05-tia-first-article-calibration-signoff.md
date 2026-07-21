# TIA Readout First-Article Calibration Signoff - 2026-07-05

## Scope

This signoff accepts the current SFH2201/OPA380/AD7606 signal-photodiode path
for controlled first-article calibration. It does not release production
measurement use until the real Vivonics optical photocurrent range, ambient
shielding, trim state, and ADC scaling are measured.

## Accepted First-Article Configuration

- Treat the current 2 Mohm feedback trim as a high-sensitivity, low-current
  bench range.
- Start with VBIAS target 1.5 V and record the actual VBIAS for each channel.
- Keep the SFH2201 detectors covered or optically shielded during dark-offset
  capture.
- Limit ambient light before enabling lasers; the SFH2201 1000 lx example is an
  expected saturation case at 2 Mohm feedback.
- Calibrate `VOUT1..4` one channel at a time with a known electrical current injection or a calibrated optical input at the SFH2201.
- Record RF/trim state, VBIAS, dark ADC counts, response slope, noise floor,
  saturation threshold, ambient condition, and known input level for each
  channel.
- Confirm AD7606 +/-5 V scaling for `VOUT1..4` before trusting counts as
  calibrated voltage.
- Firmware must flag saturation, out-of-range counts, dark-offset drift, and
  any trim/calibration mismatch before reporting production measurements.

## Remaining Risk

This signoff is enough to order and perform controlled first-article TIA
readout calibration. It does not close production measurement release, ambient
shielding, optical-path calibration, noise/stability proof, firmware
implementation, or the final RF/VBIAS setting for field use.
