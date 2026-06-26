# Laser Harness Pin-Code Compatibility

Sources:
- Current proof buy list:
  `../docs/program/PROOF_LASER_PARTS_2026-06-24.md`
- Thorlabs TO-can diode tables for `L785P090`, `L638P040`, `L520A1`,
  `L450G2`, and `L405P20`
- Thorlabs laser-diode mount documentation for A/B/C/G pin-code behavior
- ams OSRAM `PLT5 520B` datasheet

Current bench topology:
- The laser driver is a low-side current sink:
  `LASER_V+ -> laser diode -> LASER_Nx -> AO3400A -> 10 ohm sense -> GND`.
- The monitor path is a low-side passive burden:
  `MPD_RAWx -> 10k to GND || 100 nF to GND -> 1k -> ESP32 ADC1`.
- This monitor path expects the monitor photodiode cathode at the laser common
  high node and the monitor photodiode anode on `MPD_RAWx`.

Compatible direct harness class:
- `PLT5 520B` style: pin 1 `LD cathode` -> `LASER_Nx`; pin 2
  `LD anode + PD cathode + case` -> `LASER_V+`; pin 3 `PD anode` ->
  `MPD_RAWx`.
- Thorlabs A-code parts such as `L785P5`, `L638P040`, and `L520A1` are
  compatible with the same electrical assumption: isolated laser cathode,
  common case/anode side, and isolated monitor diode anode.

Not compatible with the current monitor front end:
- Thorlabs `L785P090` is a C-code diode. Its isolated laser pin is the laser
  anode, and its monitor diode cathode is the isolated monitor pin; the case
  common is on the laser cathode / monitor diode anode side. The low-side sink
  can only drive that laser with an adapter that maps the common pin to
  `LASER_Nx`, and the current low-side `MPD_RAWx` burden is the wrong polarity
  and common-mode for its monitor diode.
- Thorlabs `L450G2` is a G-code diode with no monitor photodiode, so `MPD_RAWx`
  cannot provide source feedback for that part.
- Thorlabs `L405P20` is a B-code spot-test candidate, not the production erase
  source. It is not part of the four-channel bench source harness unless its
  exact pin table and adapter are reviewed.

Required action before laser bring-up:
- For direct monitor feedback on this bench PCB, use only A-code or PLT-style
  common-anode / monitor-PD-cathode laser cans, or build a documented adapter
  that presents that topology to J4.
- For `L785P090` monitor feedback, add a C-code-compatible driver/monitor front
  end or use a dedicated APC driver matched to the diode polarity. Do not wire
  `L785P090` directly to J4 and expect the existing `MPD_RAWx` circuit to work.
- `L785P5` is an A-code low-power 785 nm bring-up part that fits the current
  monitor front end, but it is not a substitute for the `L785P090` 90 mW phase-
  read proof source.
- If `L450G2` is installed, treat the corresponding `MPD_RAWx` channel as absent
  telemetry and rely on current telemetry plus external optical calibration.
