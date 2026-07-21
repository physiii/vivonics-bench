# AP632 First-Article Buck Validation Signoff - 2026-07-05

## Scope

This signoff accepts the AP63205 `/POWER_IO/BUCK_5V` rail and AP63200
`LASER_V+` rail for controlled first-article bring-up only. It does not release
production 24 V input protection, RJ45 power injection, hot-plug operation, or
unmeasured buck ripple/transient/temperature behavior.

## Accepted First-Article Configuration

- Follow `2026-07-05-vin24-bench-input-signoff.md`: J5 barrel input only,
  24.0 V, external current limit no higher than 300 mA, RJ45 power disabled,
  verified center-positive polarity, and no hot-plug.
- Verify `/POWER_IO/BUCK_5V`, post-OR `+5V`, and `LASER_V+` before enabling
  firmware, lasers, or optical measurements.
- Treat `LASER_V+` as a 9.3 V-class rail and rerun the laser-current and buck
  budget checks before changing the AP63200 feedback network or laser load.
- Measure startup overshoot, steady ripple, and load-step transient on
  `/POWER_IO/BUCK_5V`, post-OR `+5V`, and `LASER_V+` with a short probe ground.
- Measure U15, U16, L1, L2, D6, C64-C65, and C67-C68 temperature during
  steady first-article load.
- Do not run all laser channels at maximum command until `LASER_V+` ripple,
  buck temperature, and laser driver temperature are measured together.
- Rerun `check_buck_input_power_budget.py` before changing the input voltage,
  rail loads, output capacitors, inductors, laser current limits, or `LASER_V+`
  setpoint.

## Remaining Risk

This signoff is enough to order and perform controlled first-article buck
bring-up with external current limiting. It does not close production input protection, adapter/RJ45 harness rating, reverse-polarity protection,
transient/TVS protection, hot-plug behavior, measured ripple/transient/stability
data, or measured temperature data.
