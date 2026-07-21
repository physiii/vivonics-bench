# 2026-07-05 Laser First-Article Bring-Up Signoff

Scope: LD1-LD4 first-article laser bring-up on the current JLCPCB bench board.

This signoff accepts the electrical current-limit design for controlled
first-article bring-up only. It does not close optical safety, driver/sense
temperature measurement, optical output calibration, firmware clamp validation,
loop transient behavior, or production laser release.

## Accepted Bring-Up Configuration

- Use appropriate wavelength-rated laser safety eyewear and an enclosed beam stop before any LD1-LD4 channel is energized.
- Inspect each received laser can against the 2026-07-04 MPN/footprint pin table
  before soldering.
- Bring up one laser channel at a time.
- Start each channel at minimum firmware duty cycle and minimum command.
- Keep firmware current and duty-cycle clamps at or below the per-channel analog
  command limits: IR 38.0 mA, red 23.0 mA, green 76.2 mA, blue 105.5 mA.
- Verify the shared `LASER_V+` rail before enabling any channel; the current
  checked reference is the 9.3 V-class rail.
- Measure driver/sense-resistor temperature during bring-up for every channel.
- Measure optical output with an external optical power meter for every channel.
- Do not run all four colors continuously at maximum command without thermal
  measurement.

## Current Evidence

- `check_laser_current_budget.py --policy selected-diodes-typ-9v3` passes.
- `check_laser_current_budget.py --policy selected-diodes-max-9v3` passes.
- `check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3`
  passes for the per-channel analog command limiter high-current corner.
- `check_laser_driver_control_loop.py --policy hardware-clamp-gate-margin`
  passes for the per-channel analog command limits.
- `check_buck_input_power_budget.py --policy hardware-clamp-9v3` passes for the
  all-channel per-channel analog-limit input-current case.

## Remaining Release Risk

This signoff is enough to order and perform controlled first-article laser
bring-up. It does not close optical safety, measured optical output, measured
driver/sense-resistor temperature, firmware clamp behavior, duty-cycle limits,
loop transient behavior, or future laser/rail/current substitutions.
