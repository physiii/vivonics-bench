# Vivonics Laser Controller

This directory is the authoritative bench package for the fabricated ESP32-S3
laser-controller board. Firmware and circuit artifacts live together so a code
change, board assumption, and first-article measurement can be reviewed against
the same bench-repository commit.

## Package map

- [`code/`](code/README.md): ESP-IDF firmware, host tests, build profiles, and
  the isolated AD7606 diagnostic.
- [`circuits/`](circuits/README.md): KiCad source, fabrication artifacts,
  electrical review scripts, signoffs, and calibration templates.

The old parent-repository locations `firmware/laser_controller/` and
`bench/circuits/` are retired. Make laser-controller changes only under this
directory. In the main Vivonics checkout the full paths are
`bench/laser_controller/code/` and `bench/laser_controller/circuits/`.

## Verification from the bench repository root

```bash
laser_controller/code/run-host-tests.sh
laser_controller/code/build-container.sh
laser_controller/code/build-validation-container.sh
laser_controller/code/build-laser-test-container.sh
laser_controller/code/build-dashboard-container.sh
python3 laser_controller/circuits/run_laser_controller_review.py
```

The firmware wrappers work both in a standalone clone of `vivonics-bench` and
when this repository is checked out as the parent Vivonics repo's `bench/`
submodule. The circuit review regenerates its local audit report under
`circuits/review/generated/`.

## Evidence boundary

Code and CAD checks establish reproducible software and design-review evidence;
they do not replace current-limited board bring-up, oscilloscope captures,
optical-power calibration, temperature measurements, or fail-safe testing. The
parent Vivonics repository owns experimental records under `bench-output/` and
program-level interpretations under `docs/program/`.
