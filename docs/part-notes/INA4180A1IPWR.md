# INA4180A1IPWR Part Note

Sources:
- Texas Instruments INA180/INA181/INA2180/INA2181/INA4180/INA4181 datasheet:
  `https://www.ti.com/lit/ds/symlink/ina180.pdf`
- LCSC `C2057528` order source for `INA4180A1IPWR`

Package / pinout captured:
- `INA4180A1IPWR` is the PW TSSOP-14 quad current-sense amplifier.
- Pin 1 = `OUT1`, pin 2 = `IN-1`, pin 3 = `IN+1`, pin 4 = `VS`.
- Pin 5 = `IN+2`, pin 6 = `IN-2`, pin 7 = `OUT2`.
- Pin 8 = `OUT3`, pin 9 = `IN-3`, pin 10 = `IN+3`, pin 11 = `GND`.
- Pin 12 = `IN+4`, pin 13 = `IN-4`, pin 14 = `OUT4`.

Bench design decision:
- U12 implements the internal laser monitor-PD current readout.
- Each channel is `MPD_RAWx -> 750R MPD sense -> MPD_BIAS`.
- INA4180 `IN+x` connects to `MPD_RAWx`; INA4180 `IN-x` connects to `MPD_BIAS`.
- The A1 gain option is `20 V/V`, so PLT5-style `150 uA` monitor current through
  `750R` gives `112.5 mV` sense drop and about `2.25 V` at the ESP32 ADC path.
- `OUT1..4` drive `MPD_AMP1..4`, then `1k/100nF` ADC-side filters into `MPD1..4`.
- U12 is powered from `+3V3` with local `100nF` decoupling at C35.

Release / layout implication:
- Use Kelvin-style routing from each 750R sense resistor to the matching INA4180
  input pair. Do not route laser cathode current through the sense input stubs.
- The INA common-mode range covers the bench `MPD_RAWx` / `MPD_BIAS` nodes when
  `LASER_V+` is 10.5 V, while the output remains ESP32-scale.
- This is source telemetry, not a calibrated optical-power guarantee or a
  production APC waiver. Actual laser MPN pinout, monitor-PD reverse-bias limit,
  optical calibration, and shutoff behavior still need release review.
