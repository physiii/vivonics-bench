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
- Each laser sheet includes a non-SMT direct TO-can footprint:
  `LD_K -> LASER_N`, common `LD_A/PD_K/case -> LASER_V+`, and `PD_A ->
  MPD_RAW` for monitor-capable cans.
- Each monitor input uses a high-side current-sense front end:
  `MPD_RAWx -> 240R sense -> MPD_BIAS`; INA4180A1 gain 20 drives
  `MPD_AMPx -> 1k -> MPDx`, with `100nF` ADC-side filtering.
- LM4040C50 holds `LASER_V+ - MPD_BIAS` near 5 V through a 2.49 k sink, so
  PLT5-style monitor diodes see about the datasheet monitor-current bias.
- `mcu.kicad_sch` routes `MPD1..4` to ESP32-S3 ADC pins:
  GPIO2, GPIO3, GPIO8, and GPIO9. GPIO1 is the copied factory-button net.
- `tia_ir/red/green/blue.kicad_sch` use separate on-board SFH2201 photodiodes and OPA380
  TIAs for the optical readout path.

So the bench board measures all three quantities per source: laser electrical
current (`ISENSE`), internal source monitor (`MPD`), and external/sample optical
signal (`VOUT1..4`).

## Direct Laser Footprints

The old laser/monitor header has been removed. Laser sources are mounted in
the direct `LD1..LD4` through-hole footprints.

Do not assume all 3-pin cans share the same common terminal. The selected
Digikey-cart sources are mapped as:

| Channel | MPN | Diode pin mapping |
|---|---|---|
| IR | D7805I | `LD1` TO18 footprint: pin 1 laser cathode to `LASER_N1`; pin 2 common case to `LASER_V+`; pin 3 monitor anode to `MPD_RAW1` |
| Red | D6505I | `LD2` TO18 footprint: pin 1 laser cathode to `LASER_N2`; pin 2 common case to `LASER_V+`; pin 3 monitor anode to `MPD_RAW2` |
| Green | PLT5 520EB_P | `LD3` TO56 footprint: pin 1 laser cathode to `LASER_N3`; pin 2 LD anode / PD cathode / case to `LASER_V+`; pin 3 monitor anode to `MPD_RAW3` |
| Blue | PLT5 450GB | `LD4` TO56 footprint: pin 1 laser anode to `LASER_V+`; pin 3 laser cathode to `LASER_N4`; pin 2 case no-connect |

`MPD_RAW4` stays available at the INA4180 monitor front end, but it is
spare/open for PLT5 450GB because that diode has no monitor photodiode. Do not
wire the PLT5 450GB case to `MPD_RAW4`.

The PLT5 520EB_P datasheet gives a typical monitor current around `150 uA` at
its rated optical power, and monitor current refers to `VRPD = 5 V` as a
short-time power reference, not guaranteed absolute accuracy. The bench path is
scaled for that condition: at the current green policy of `LASER_V+ = 10.5 V`,
LM4040C50 sets `MPD_BIAS` near `5.5 V`, the `240R` sense resistor drops about
`36 mV` at `150 uA`, and INA4180A1 gain 20 drives about `0.72 V` into the
ESP32 ADC path. The monitor photodiode reverse bias is about `4.89 V` at
typical monitor current and about `5.00 V` in the dark/off case while
`LASER_V+` is present. The ADC path remains linear to about `218 uA` of monitor
current with the current 3.3 V headroom guard.

This fixes the PLT5-style 10.5 V bench-bias defect, but it is still source
telemetry rather than a release-approved production APC loop. Firmware must keep
the current loop as the hard safety limit, and every actual laser MPN still
needs a pin table, can/common polarity, monitor-PD reverse-bias limit, and
optical calibration check before relying on MPD feedback.

The selected LD1-LD3 pin topology is compatible with the high-side
INA4180/LM4040 front end. The present `240R` / INA4180A1 gain-20 scaling fits
the selected monitor-current spread inside the local ADC-headroom guard:
`D7805I` typical monitor current (`200 uA`) maps to about `0.96 V`, its
`600 uA` high-end value maps to about `2.88 V`, and `D6505I` high-end monitor
current (`0.3 mA`) maps to about `1.44 V`. This fixes ADC headroom only; MPD
still requires optical calibration before production APC or safety feedback.

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
  `PLT5 520EB_P` has the case tied to `LD anode + PD cathode`; `PLT5 450GB`
  exposes a case pin but no monitor photodiode. Neither should be blindly
  assigned to a driver without a pinout/topology check.

Production still needs an external edge/reference detector or sensor-side
normalization. The internal monitor PD stabilizes source output; it does not
measure GLV efficiency, optics contamination, film transmission/phase response,
or detector gain drift.

## Bring-up checklist

- Confirm each laser MPN's exact pin table and can/common-node polarity.
- Verify the high-side INA4180/LM4040 monitor front end against D6505I, D7805I,
  and PLT5 520EB_P monitor-PD reverse-bias limits before bring-up.
- Keep PLT5 450GB case isolated/no-connect unless the mechanical design
  intentionally bonds the can elsewhere.
- Confirm whether the mechanical mount isolates the can or ties it to chassis.
- Pick driver topology per diode polarity, not per wavelength.
- Calibrate `laser current -> monitor current -> external power meter` for each
  source.
- Store per-source monitor setpoints and safe current clamps in firmware.
- Treat monitor current as relative/calibrated telemetry, not an absolute power
  measurement without external calibration.
