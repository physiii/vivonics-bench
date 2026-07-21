# Monitor-PD First-Article Calibration Signoff - 2026-07-05

## Scope

This signoff accepts the current INA4180/LM4040 monitor-PD front end for
controlled first-article bring-up. It does not release production APC,
normalization, or optical-safety behavior until calibration data exists for the
received laser cans and bench optics.

## Accepted First-Article Configuration

- `LD1` D7805I, `LD2` D6505I, and `LD3` PLT5 520EB_P are the only selected
  monitor-capable sources.
- `LD4` PLT5 450GB has no monitor photodiode; treat `MPD_RAW4` / `MPD4` as spare/open, not blue-source telemetry.
- Use MPD telemetry only after calibrating laser current -> MPD ADC counts ->
  external optical power meter for each monitor-capable source.
- Keep the analog current loop and firmware current clamps as the hard safety
  limit. Monitor-PD telemetry must not raise current above the per-channel
  clamps.
- Calibrate one source at a time at minimum firmware duty cycle and minimum
  command before increasing setpoint.
- Record dark/off ADC counts, response slope, saturation threshold, firmware
  setpoint, and external optical-power reading for each monitor-capable source.
- Firmware must fail shutoff or inhibit the source if the monitor path is open,
  shorted, saturated, current rises without monitor response, or the requested
  optical setpoint would exceed the current clamp.

## Remaining Risk

This signoff is enough to order and perform controlled first-article monitor-PD
bring-up with an external optical meter. It does not close production APC,
normalization, or optical-safety release. It also does not close physical
orientation inspection, diode substitution review, firmware implementation,
ambient-light coupling, or measured calibration data.
