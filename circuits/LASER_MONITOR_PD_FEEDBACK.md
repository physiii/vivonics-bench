# Laser Monitor Photodiode Feedback

## Conclusion

Yes: the third pin on the relevant raw laser diodes is an internal monitor
photodiode connection. It is useful for optical source feedback and source
normalization. It does not replace the external/sample photodiode path, because
it monitors the laser back-facet or internal optical power before the beam,
sample, GLV, relay optics, and detector path.

Use it for:

- slow optical-power telemetry during every pulse/read;
- firmware source normalization, e.g. `detector_signal / laser_monitor`;
- a slow outer loop that trims laser current/PWM against a monitor setpoint;
- production APC, where the driver closes the loop directly around monitor
  photodiode current.

Do not use it as the film/readout detector.

## Current bench design

- `laser_ir/red/green/blue.kicad_sch` are current-regulated low-side sinks:
  `PWM_IN -> RC + 30k limiter -> TLV9001 -> AO3400A gate`, with `10 ohm`
  2512 2 W source-sense feedback.
- `power_io.kicad_sch` exposes each laser cathode and monitor photodiode node
  on J4, plus common `LASER_V+` and a shield/return `GND`.
- Each monitor input uses a passive front end: `MPD_RAWx -> 10k burden to GND`,
  `100nF` shunt filter to GND, then `1k` series isolation into `MPDx`.
- `mcu.kicad_sch` routes `MPD1..4` to ESP32-S3 ADC1 pins:
  GPIO2, GPIO1, GPIO8, and GPIO9.
- `tia_ir/red/green/blue.kicad_sch` use separate on-board SFH2201 photodiodes and OPA380
  TIAs for the optical readout path.

So the bench board measures all three quantities per source: laser electrical
current (`ISENSE`), internal source monitor (`MPD`), and external/sample optical
signal (`VOUT1..4`).

## Bench connector and front end

J4 is now a 1x10 laser/monitor header:

| Pin | Net |
|---:|---|
| 1 | `LASER_N1` |
| 2 | `MPD_RAW1` |
| 3 | `LASER_N2` |
| 4 | `MPD_RAW2` |
| 5 | `LASER_N3` |
| 6 | `MPD_RAW3` |
| 7 | `LASER_N4` |
| 8 | `MPD_RAW4` |
| 9 | `LASER_V+` |
| 10 | `GND` shield/return |

Do not assume all 3-pin cans share the same common terminal. For example,
`PLT5 520B` uses pin 2 as `LD anode + PD cathode + case` and pin 3 as `PD
anode`; Thorlabs `L785P090` is a C-pin-code diode and needs its exact C-code
mechanical pin map checked before footprint/connector assignment.

That is not just a paperwork issue. The current bench monitor front end is
compatible with PLT5-style and Thorlabs A-code common-anode / monitor-PD-cathode
diodes. `L785P090` is C-code: the laser cathode / monitor-PD anode side is the
case common, while the monitor-PD cathode is the isolated monitor pin. The
low-side current sink can only drive that laser through an adapter that maps the
common pin to `LASER_Nx`, and the existing `MPD_RAWx -> 10k to GND` burden is
the wrong polarity/common-mode for the C-code monitor diode. Do not wire
`L785P090` directly to J4 and expect monitor feedback from this circuit.

`L450G2` is G-code and has no monitor photodiode, so its corresponding `MPD_RAWx`
channel is absent telemetry unless a different source monitor is added.

The PLT5 520B datasheet gives a typical monitor current around `150 uA` at its
rated optical power, so the existing `10M` OPA380 TIA topology is the wrong
scale for monitor feedback. The bench path uses `10k`, giving about `1.5 V`
typical before calibration, with the existing firmware current clamp still
acting as the hard safety limit.

Recommended bench control architecture:

1. Keep the existing fast analog current loop and `ISENSE` safety telemetry.
2. Add `MPD1..4` ADC telemetry.
3. In firmware, enforce a hard current limit first.
4. Add a slow outer optical-power loop that adjusts each channel setpoint to
   hold calibrated `MPD` current.
5. Log both `ISENSE` and `MPD` with each optical sample, then normalize the
   external readout against `MPD` when analyzing drift.

Fail shutoff conditions should include monitor open/short, current rising
without monitor response, monitor saturation, and any setpoint that would
exceed the per-channel current clamp.

## Production design implication

The production source board should use the internal monitor PD as the APC
feedback element for the 785 nm read laser and 520 nm write laser. This matches
the production documents that already call for ADN2830/iC-Haus-class APC laser
drivers.

This APC decision is separate from the bench `LASER_V+` thermal decision. The
bench board uses one common laser rail and SOT-23 low-side linear sinks; that is
acceptable only after each diode's forward voltage, current setpoint, duty cycle,
and AO3400A dissipation are checked. Production should not copy the common high
rail as the source-driver architecture for mixed red/green/blue/IR diodes.

Driver polarity matters:

- ADI ADN2830 is an APC baseline and explicitly controls average optical power
  by holding monitor photodiode current.
- iC-Haus iC-WKN is optimized for N-type laser diodes.
- iC-Haus iC-WKP is optimized for P-type/case-grounded laser diodes.
- The selected driver must match each laser package common-node polarity.
  `PLT5 520B` has the case tied to `LD anode + PD cathode`, so it should not be
  blindly assigned to an N-type-only driver without a pinout/topology check.

Production still needs an external edge/reference detector or sensor-side
normalization. The internal monitor PD stabilizes source output; it does not
measure GLV efficiency, optics contamination, film transmission/phase response,
or detector gain drift.

## Bring-up checklist

- Confirm each laser MPN's exact pin table and can/common-node polarity.
- Reject direct `L785P090` monitor-PD use on this board until a C-code adapter or
  C-code-compatible driver/monitor front end is designed.
- Confirm whether the mechanical mount isolates the can or ties it to chassis.
- Pick driver topology per diode polarity, not per wavelength.
- Calibrate `laser current -> monitor current -> external power meter` for each
  source.
- Store per-source monitor setpoints and safe current clamps in firmware.
- Treat monitor current as relative/calibrated telemetry, not an absolute power
  measurement without external calibration.
